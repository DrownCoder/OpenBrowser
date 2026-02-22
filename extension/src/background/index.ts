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
    
    try {
      const response = await handleCommand(data as Command);
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
    } catch (error) {
      console.error('Error handling command:', error);
      
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
      case 'screenshot':
        // ✅ STRICT MODE: conversation_id and tab_id are REQUIRED
        if (!command.conversation_id) {
          throw new Error('conversation_id is required for screenshot command (strict mode)');
        }
        if (!command.tab_id) {
          throw new Error('tab_id is required for screenshot command (strict mode)');
        }
        const tabIdForScreenshot = command.tab_id;
        
        console.log(`📸 [Screenshot] Starting for tab ${tabIdForScreenshot}, conversation: ${command.conversation_id}`);
        
        // Ensure tab is managed by tab manager for this conversation
        await tabManager.ensureTabManaged(tabIdForScreenshot, command.conversation_id);
        tabManager.updateTabActivity(tabIdForScreenshot, command.conversation_id);
        
        // Take screenshot in background (no tab activation)
        const screenshotResult = await captureScreenshot(
          tabIdForScreenshot,
          command.include_cursor !== false,
          command.quality || 90,
          true, // resizeToPreset
          0    // waitForRender
        );
        
        console.log(`✅ [Screenshot] Completed for tab ${tabIdForScreenshot}`);
        
        return {
          success: true,
          message: 'Screenshot captured',
          data: screenshotResult,
          timestamp: Date.now(),
        };

      case 'tab':
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
            const openResult = await tabs.openTab(command.url);
            if (openResult.tabId) {
              await tabManager.addTabToManagement(openResult.tabId, conversationId);
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
            const listResult = await tabs.getAllTabs();
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

      case 'cleanup_session':
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

      case 'get_tabs':
        // ✅ STRICT MODE: conversation_id is REQUIRED for managed_only=true
        const getTabsManagedOnly = command.managed_only !== false;
        
        if (getTabsManagedOnly) {
          if (!command.conversation_id) {
            throw new Error('conversation_id is required for get_tabs with managed_only=true (strict mode)');
          }
          const conversationTabs = tabManager.getManagedTabs(command.conversation_id);
          return {
            success: true,
            message: `Found ${conversationTabs.length} managed tabs in conversation ${command.conversation_id}`,
            data: {
              tabs: conversationTabs,
              count: conversationTabs.length,
              conversationId: command.conversation_id,
              managed_only: true,
            },
            timestamp: Date.now(),
          };
        } else {
          // Get all tabs (no conversation filter)
          const allTabsResult = await tabs.getAllTabs();
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

      case 'javascript_execute':
        // ✅ STRICT MODE: conversation_id and tab_id are REQUIRED
        if (!command.conversation_id) {
          throw new Error('conversation_id is required for javascript_execute command (strict mode)');
        }
        if (!command.tab_id) {
          throw new Error('tab_id is required for javascript_execute command (strict mode)');
        }
        const tabIdForJS = command.tab_id;
        
        console.log(`📜 [JavaScript] Executing in tab ${tabIdForJS}, conversation: ${command.conversation_id}`);
        
        // Ensure tab is managed by tab manager for this conversation
        await tabManager.ensureTabManaged(tabIdForJS, command.conversation_id);
        tabManager.updateTabActivity(tabIdForJS, command.conversation_id);
        
        const jsStartTime = Date.now();
        
        const jsResult = await javascript.executeJavaScript(
          tabIdForJS,
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

console.log('✅ OpenBrowser extension loaded (Strict Mode)');
