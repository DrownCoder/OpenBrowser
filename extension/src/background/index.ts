/**
 * Background Script - Main entry point for Chrome extension (Strict Mode)
 * 
 * All commands require conversation_id to be provided by server.
 * No default fallback behavior.
 */

import { wsClient } from '../websocket/client';
import { captureScreenshot } from '../commands/screenshot';
import { tabs } from '../commands/tabs';
import { tabManager } from '../commands/tab-manager';
import { javascript } from '../commands/javascript';
import type { Command, CommandResponse } from '../types';

console.log('🚀 OpenBrowser extension starting (Strict Mode)...');

// ============================================================================
// Command Queue Management System
// ============================================================================

/**
 * Command queue item interface
 */
interface QueuedCommand {
  data: any;
  resolve: (value: any) => void;
  reject: (error: Error) => void;
  addedAt: number;
}

/**
 * Command Queue Manager
 * Prevents command stacking and ensures proper flow control
 */
class CommandQueueManager {
  private queue: QueuedCommand[] = [];
  private isProcessing = false;
  private commandCooldown = 1000; // 1 second cooldown between commands
  private lastCommandEndTime = 0;
  private performanceHistory: Array<{type: string; duration: number; timestamp: number}> = [];
  private readonly maxHistory = 20;

  /**
   * Add command to queue
   */
  async enqueue(data: any): Promise<any> {
    return new Promise((resolve, reject) => {
      this.queue.push({
        data,
        resolve,
        reject,
        addedAt: Date.now(),
      });
      
      // Start processing if not already processing
      if (!this.isProcessing) {
        this.processQueue();
      }
      
      // Log queue status
      if (this.queue.length > 3) {
        console.warn(`⚠️ Command queue growing: ${this.queue.length} commands pending`);
      }
    });
  }

  /**
   * Process the command queue
   */
  private async processQueue(): Promise<void> {
    if (this.isProcessing || this.queue.length === 0) {
      return;
    }

    this.isProcessing = true;

    while (this.queue.length > 0) {
      const queuedCommand = this.queue.shift()!;
      const waitTime = Date.now() - queuedCommand.addedAt;
      
      // Warn about long wait times
      if (waitTime > 5000) {
        console.warn(`⌛ Command waited ${waitTime}ms in queue before processing`);
      }

      try {
        // Apply cooldown between commands if needed
        const timeSinceLastCommand = Date.now() - this.lastCommandEndTime;
        if (timeSinceLastCommand < this.commandCooldown) {
          const cooldownDelay = this.commandCooldown - timeSinceLastCommand;
          console.log(`⏸️ Command cooldown: waiting ${cooldownDelay}ms`);
          await new Promise(resolve => setTimeout(resolve, cooldownDelay));
        }

        // Process the command
        const result = await this.processCommand(queuedCommand.data);
        queuedCommand.resolve(result);
        
        // Update last command end time
        this.lastCommandEndTime = Date.now();
        
      } catch (error) {
        queuedCommand.reject(error as Error);
        this.lastCommandEndTime = Date.now();
      }
    }

    this.isProcessing = false;
  }

  /**
   * Process individual command (original command handling logic)
   * Public method so watchdog can wrap it
   */
  public async processCommand(data: any): Promise<any> {
    // This is the original command handling logic from wsClient.onMessage
    const commandId = data.command_id || `unknown_${Date.now()}`;
    const commandType = data.type || 'unknown';
    const commandStartTime = Date.now();

    // Track command execution
    wsClient.trackCommandStart(commandId, commandType, {
      conversation_id: data.conversation_id,
      action: data.action,
      tab_id: data.tab_id,
      url: data.url
    });

    try {
      const response = await handleCommand(data as Command);
      const commandDuration = Date.now() - commandStartTime;

      // Record performance
      this.recordPerformance(commandType, commandDuration);

      // Warn about long-running commands
      if (commandDuration > 10000) {
        console.warn(`⚠️ Long command execution: ${commandType} took ${commandDuration}ms`);
      }

      // Send response back to server
      if (wsClient.isConnected()) {
        const responseWithId = {
          ...response,
          command_id: data.command_id,
          timestamp: Date.now(),
        };

        wsClient.sendCommand(responseWithId as any).catch((error) => {
          console.error('Failed to send response:', error);
        });
      }

      return response;
    } catch (error) {
      console.error('Error handling command:', error);
      const commandDuration = Date.now() - commandStartTime;

      // Send error response
      const errorResponse: CommandResponse = {
        success: false,
        command_id: data.command_id,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: Date.now(),
      };

      if (wsClient.isConnected()) {
        wsClient.sendCommand(errorResponse as any).catch(console.error);
      }

      if (commandDuration > 10000) {
        console.warn(`⚠️ Long failed command: ${commandType} failed after ${commandDuration}ms`);
      }

      throw error;
    } finally {
      // End command tracking
      wsClient.trackCommandEnd(commandId);
    }
  }

  /**
   * Record command performance for monitoring
   */
  private recordPerformance(type: string, duration: number): void {
    this.performanceHistory.push({
      type,
      duration,
      timestamp: Date.now(),
    });

    if (this.performanceHistory.length > this.maxHistory) {
      this.performanceHistory.shift();
    }

    // Detect performance degradation
    if (this.performanceHistory.length >= 5) {
      const recent = this.performanceHistory.slice(-5);
      const avgDuration = recent.reduce((sum, cmd) => sum + cmd.duration, 0) / recent.length;
      
      if (avgDuration > 5000) {
        console.warn(`📉 Performance degradation detected: avg command time ${avgDuration.toFixed(0)}ms`);
        
        // Adaptive cooldown adjustment
        if (avgDuration > 10000) {
          this.commandCooldown = 2000; // Increase to 2 seconds
          console.log(`⚙️ Increased command cooldown to ${this.commandCooldown}ms`);
        }
      } else if (avgDuration < 1000 && this.commandCooldown > 1000) {
        // Reset cooldown if performance improves
        this.commandCooldown = 1000;
        console.log(`⚙️ Reset command cooldown to ${this.commandCooldown}ms`);
      }
    }
  }

  /**
   * Get queue status
   */
  getStatus() {
    return {
      queueLength: this.queue.length,
      isProcessing: this.isProcessing,
      lastCommandEndTime: this.lastCommandEndTime,
      performanceHistory: [...this.performanceHistory],
    };
  }

  /**
   * Clear queue (emergency cleanup)
   */
  clearQueue(): void {
    console.warn(`🧹 Clearing command queue with ${this.queue.length} pending commands`);
    
    for (const queuedCommand of this.queue) {
      queuedCommand.reject(new Error('Command queue cleared'));
    }
    
    this.queue = [];
    this.isProcessing = false;
  }
}

// Initialize command queue manager
const commandQueue = new CommandQueueManager();

// ============================================================================
// Watchdog Timer for Main Thread Freeze Detection
// ============================================================================

/**
 * Watchdog timer detects when main thread is frozen
 */
class WatchdogTimer {
  private lastCheckTime = Date.now();
  private watchdogInterval: number | null = null;
  private readonly CHECK_INTERVAL = 3000; // Check every 3 seconds
  private readonly FREEZE_THRESHOLD = 5000; // 5 seconds without check = frozen

  start(): void {
    console.log('🔍 Watchdog timer started');
    
    if (this.watchdogInterval) {
      clearInterval(this.watchdogInterval);
    }
    
    this.lastCheckTime = Date.now();
    
    this.watchdogInterval = setInterval(() => {
      const now = Date.now();
      const timeSinceLastCheck = now - this.lastCheckTime;
      
      if (timeSinceLastCheck > this.FREEZE_THRESHOLD) {
        console.error(`🚨 WATCHDOG: Main thread may be frozen! No check for ${timeSinceLastCheck}ms`);
        
        // Emergency cleanup if main thread appears frozen
        this.emergencyCleanup();
      }
      
      this.lastCheckTime = now;
    }, this.CHECK_INTERVAL) as unknown as number;
  }

  stop(): void {
    if (this.watchdogInterval) {
      clearInterval(this.watchdogInterval);
      this.watchdogInterval = null;
      console.log('🔍 Watchdog timer stopped');
    }
  }

  tick(): void {
    this.lastCheckTime = Date.now();
  }

  private emergencyCleanup(): void {
    console.warn('🆘 Watchdog emergency cleanup initiated');
    
    // Clear command queue to free up resources
    commandQueue.clearQueue();
    
    // Try to send heartbeat if WebSocket is still connected
    if (wsClient.isConnected()) {
      try {
        // Try to send immediate ping
        wsClient.sendCommand({ type: 'ping' } as any).catch(() => {
          // Ignore errors during emergency
        });
      } catch (error) {
        // Ignore errors during emergency cleanup
      }
    }
  }

  getStatus() {
    return {
      lastCheckTime: this.lastCheckTime,
      timeSinceLastCheck: Date.now() - this.lastCheckTime,
      isRunning: this.watchdogInterval !== null,
    };
  }
}

// Initialize watchdog timer
const watchdog = new WatchdogTimer();
watchdog.start();

// Update watchdog on each command processing - wrap the processCommand method
const originalProcessCommand = commandQueue.processCommand.bind(commandQueue);
commandQueue.processCommand = async function(data: any) {
  watchdog.tick();
  return originalProcessCommand(data);
};

// ============================================================================

// Initialize tab manager
tabManager.initialize().then(() => {
  console.log('✅ Tab manager initialized');
}).catch((error) => {
  console.error('❌ Failed to initialize tab manager:', error);
});

// Initialize WebSocket connection
wsClient.connect().then(() => {
  tabManager.updateStatus('idle');
  console.log('🌐 WebSocket connected, tab manager status updated');
}).catch((error) => {
  console.error('Failed to connect to WebSocket server:', error);
  tabManager.updateStatus('disconnected');
});

// Listen for WebSocket disconnection
wsClient.onDisconnect(() => {
  console.log('🌐 WebSocket disconnected, updating tab manager status');
  tabManager.updateStatus('disconnected');
});

// Listen for commands from WebSocket server
wsClient.onMessage(async (data) => {
  // Only handle command messages (not responses or server messages)
  if (data.type && !data.success && !data.error) {
    // Skip server messages that are not commands
    if (data.type === 'connected' || data.type === 'ping' || data.type === 'pong') {
      console.log(`📨 Received server message: ${data.type}`, data.message || '');
      return;
    }
    
    // Log command receipt
    const commandType = data.type || 'unknown';
    const commandId = data.command_id || `unknown_${Date.now()}`;
    console.log(`📨 Received command: ${commandType} (ID: ${commandId})`);
    
    // Add command to queue for processing
    try {
      await commandQueue.enqueue(data);
      console.log(`✅ Command ${commandType} (ID: ${commandId}) processed successfully`);
    } catch (error) {
      console.error(`❌ Command ${commandType} (ID: ${commandId}) failed:`, error);
      
      // Send error response if still connected
      if (wsClient.isConnected()) {
        const errorResponse: CommandResponse = {
          success: false,
          command_id: data.command_id,
          error: error instanceof Error ? error.message : 'Unknown error',
          timestamp: Date.now(),
        };
        wsClient.sendCommand(errorResponse as any).catch(console.error);
      }
    }
  }
});

/**
 * Handle incoming commands (Strict Mode)
 * All commands require conversation_id to be provided by server.
 */
async function handleCommand(command: Command): Promise<CommandResponse> {
  console.log(`📨 Handling command: ${command.type}`, command);

  try {
    switch (command.type) {
      case 'screenshot': {
        // ✅ STRICT MODE: conversation_id is REQUIRED
        if (!command.conversation_id) {
          throw new Error('conversation_id is required for screenshot command (strict mode)');
        }
        
        const conversationId = command.conversation_id;
        
        // Always use current active tab for the conversation (ignore tab_id if provided)
        const activeTabId = tabManager.getCurrentActiveTabId(conversationId);
        if (!activeTabId) {
          throw new Error(`No active tab found for conversation ${conversationId}. Use tab init or specify tab_id.`);
        }
        
        console.log(`📸 [Screenshot] Using active tab ${activeTabId} for conversation ${conversationId} (ignoring provided tab_id: ${command.tab_id || 'none'})`);
        
        console.log(`📸 [Screenshot] Starting for tab ${activeTabId}, conversation: ${conversationId}`);
        
        // Ensure tab is managed by tab manager for this conversation
        await tabManager.ensureTabManaged(activeTabId, conversationId);
        tabManager.updateTabActivity(activeTabId, conversationId);
        
        // Take screenshot in background (no tab activation)
        const screenshotResult = await captureScreenshot(
          activeTabId,
          command.include_cursor !== false,
          command.quality || 90,
          false, // resizeToPreset: false for WYSIWYG mode
          0    // waitForRender
        );
        
        console.log(`✅ [Screenshot] Completed for tab ${activeTabId}`);
        
        return {
          success: true,
          message: 'Screenshot captured',
          data: screenshotResult,
          timestamp: Date.now(),
        };
      }

      case 'tab': {
        // ✅ STRICT MODE: conversation_id is REQUIRED
        if (!command.conversation_id) {
          throw new Error('conversation_id is required for tab command (strict mode)');
        }
        const conversationId = command.conversation_id;
        console.log(`🔍 [Tab Command] conversation_id: "${conversationId}"`);

        switch (command.action) {
          case 'init':
            if (!command.url) {
              throw new Error('URL is required for init action');
            }
            const initResult = await tabManager.initializeSession(command.url, conversationId);
            
            console.log(`🚀 [Tab Init] Session ${conversationId} initialized with tab ${initResult.tabId}`);
            
            // Set the newly created tab as active
            tabManager.setCurrentActiveTabId(conversationId, initResult.tabId);
            
            return {
              success: true,
              message: `Session ${conversationId} initialized with ${command.url}`,
              data: {
                tabId: initResult.tabId,
                groupId: initResult.groupId,
                url: initResult.url,
                conversationId: conversationId,
                isManaged: true,
              },
              timestamp: Date.now(),
            };

          case 'open':
            if (!command.url) {
              throw new Error('URL is required for open action');
            }
            const openResult = await tabs.openTab(command.url, conversationId);
            
            // Set the newly opened tab as active if it has a tabId
            if (openResult.tabId) {
              tabManager.setCurrentActiveTabId(conversationId, openResult.tabId);
            }
            
            return {
              success: true,
              message: openResult.message,
              data: {
                ...openResult,
                conversationId: conversationId
              },
              timestamp: Date.now(),
            };

          case 'close':
            if (!command.tab_id) {
              throw new Error('tab_id is required for close action');
            }
            const closeResult = await tabs.closeTab(command.tab_id);
            return {
              success: true,
              message: closeResult.message,
              data: {
                ...closeResult,
                conversationId: conversationId
              },
              timestamp: Date.now(),
            };

          case 'switch':
            if (!command.tab_id) {
              throw new Error('tab_id is required for switch action');
            }
            const switchResult = await tabs.switchToTab(command.tab_id);
            await tabManager.ensureTabManaged(command.tab_id, conversationId);
            tabManager.updateTabActivity(command.tab_id, conversationId);
            
            // Set the switched-to tab as active
            tabManager.setCurrentActiveTabId(conversationId, command.tab_id);
            
            return {
              success: true,
              message: switchResult.message,
              data: {
                ...switchResult,
                conversationId: conversationId
              },
              timestamp: Date.now(),
            };

          case 'list':
            // ✅ STRICT MODE: conversation_id already checked above
            const listResult = await tabs.getAllTabs(true, conversationId);
            const conversationTabs = tabManager.getManagedTabs(conversationId);
            return {
              success: true,
              message: `Found ${listResult.count} tabs (${conversationTabs.length} in conversation ${conversationId})`,
              data: {
                ...listResult,
                conversationId: conversationId,
                conversationTabs: conversationTabs
              },
              timestamp: Date.now(),
            };

          case 'refresh':
            if (!command.tab_id) {
              throw new Error('tab_id is required for refresh action');
            }
            await tabManager.ensureTabManaged(command.tab_id, conversationId);
            tabManager.updateTabActivity(command.tab_id, conversationId);
            const refreshResult = await tabs.refreshTab(command.tab_id);
            return {
              success: true,
              message: refreshResult.message,
              data: {
                ...refreshResult,
                conversationId: conversationId
              },
              timestamp: Date.now(),
            };

          default:
            throw new Error(`Unknown tab action: ${command.action}`);
        }
      }

      case 'cleanup_session': {
        // ✅ STRICT MODE: conversation_id is REQUIRED
        if (!command.conversation_id) {
          throw new Error('conversation_id is required for cleanup_session (strict mode)');
        }
        const cleanupConversationId = command.conversation_id;
        console.log(`🧹 [Cleanup Session] Cleaning up session ${cleanupConversationId}`);
        
        await tabManager.cleanupSession(cleanupConversationId);
        
        return {
          success: true,
          message: `Session ${cleanupConversationId} cleaned up successfully`,
          data: {
            conversationId: cleanupConversationId
          },
          timestamp: Date.now(),
        };
      }

      case 'get_tabs': {
        // ✅ STRICT MODE: conversation_id is REQUIRED for managed_only=true
        const getTabsManagedOnly = command.managed_only !== false;
        
        if (getTabsManagedOnly) {
          if (!command.conversation_id) {
            throw new Error('conversation_id is required for get_tabs with managed_only=true (strict mode)');
          }
          const conversationTabs = tabManager.getManagedTabs(command.conversation_id);
          
          // ✅ FIX: Query Chrome API to get active status for each tab
          const tabsWithActive = await Promise.all(
            conversationTabs.map(async (managedTab) => {
              try {
                const chromeTab = await chrome.tabs.get(managedTab.tabId);
                return {
                  ...managedTab,
                  active: chromeTab.active,  // Add active status from Chrome API
                  index: chromeTab.index,    // Also add index for consistency
                };
              } catch (error) {
                // Tab might have been closed, return with active=false
                console.warn(`Tab ${managedTab.tabId} not found, marking as inactive`);
                return {
                  ...managedTab,
                  active: false,
                  index: -1,
                };
              }
            })
          );
          
          return {
            success: true,
            message: `Found ${tabsWithActive.length} managed tabs in conversation ${command.conversation_id}`,
            data: {
              tabs: tabsWithActive,
              count: tabsWithActive.length,
              conversationId: command.conversation_id,
              managed_only: true,
            },
            timestamp: Date.now(),
          };
        } else {
          // Get all tabs (no conversation filter)
          const allTabsResult = await tabs.getAllTabs(false, command.conversation_id);
          return {
            success: true,
            message: `Found ${allTabsResult.count} tabs total`,
            data: {
              ...allTabsResult,
              managed_only: false,
            },
            timestamp: Date.now(),
          };
        }
      }

      case 'javascript_execute': {
        // ✅ STRICT MODE: conversation_id is REQUIRED
        if (!command.conversation_id) {
          throw new Error('conversation_id is required for javascript_execute command (strict mode)');
        }
        
        const conversationId = command.conversation_id;
        
        // Determine which tab to execute JavaScript in
        // Always use current active tab for the conversation (ignore tab_id if provided)
        const activeTabId = tabManager.getCurrentActiveTabId(conversationId);
        if (!activeTabId) {
          throw new Error(`No active tab found for conversation ${conversationId}. Use tab init or specify tab_id.`);
        }
        
        console.log(`📜 [JavaScript] Executing in active tab ${activeTabId}, conversation: ${conversationId} (ignoring provided tab_id: ${command.tab_id || 'none'})`);
        
        // Ensure tab is managed by tab manager for this conversation
        await tabManager.ensureTabManaged(activeTabId, conversationId);
        tabManager.updateTabActivity(activeTabId, conversationId);
        
        const jsStartTime = Date.now();
        
        const jsResult = await javascript.executeJavaScript(
          activeTabId,
          command.script,
          command.return_by_value !== false,
          command.await_promise === true,
          command.timeout || 30000
        );
        
        const jsDuration = Date.now() - jsStartTime;
        console.log(`✅ [JavaScript] Execution completed in ${jsDuration}ms`);
        
        return {
          success: true,
          message: 'JavaScript executed successfully',
          data: jsResult,
          timestamp: Date.now(),
          duration: jsDuration,
        };
      }

      default:
        throw new Error(`Unknown command type: ${(command as any).type}`);
    }
  } catch (error) {
    console.error(`Command ${(command as any).type} failed:`, error);
    return {
      success: false,
      command_id: command.command_id,
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: Date.now(),
    };
  }
}

/**
 * Send tab switched event to server
 */
async function sendTabSwitchedEvent(conversationId: string, tabId: number): Promise<void> {
  try {
    if (!wsClient.isConnected()) {
      console.warn(`⚠️ Cannot send tab_switched event: WebSocket not connected`);
      return;
    }
    
    const event = {
      type: 'event',
      event_type: 'tab_switched',
      conversation_id: conversationId,
      tab_id: tabId,
      timestamp: Date.now(),
    };
    
    console.log(`🔄 [TabEvent] Sending tab_switched event: ${conversationId} -> ${tabId}`);
    await wsClient.sendCommand(event as any);
    console.log(`✅ [TabEvent] Tab switched event sent successfully`);
  } catch (error) {
    console.error('❌ [TabEvent] Failed to send tab switched event:', error);
  }
}

// Register tab switched listener with tab manager
tabManager.addTabSwitchedListener((conversationId: string, tabId: number) => {
  console.log(`🔄 [Background] Tab switched listener called: ${conversationId} -> ${tabId}`);
  // Send event to server asynchronously (don't await)
  sendTabSwitchedEvent(conversationId, tabId).catch(console.error);
});

console.log('✅ OpenBrowser extension loaded (Strict Mode)');
