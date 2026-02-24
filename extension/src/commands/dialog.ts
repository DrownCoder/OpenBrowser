/**
 * Dialog Handling - JavaScript Dialog Manager
 * 
 * Handles browser native dialogs (alert, confirm, prompt, beforeunload)
 * using Chrome DevTools Protocol (CDP).
 * 
 * Flow:
 * 1. Page executes confirm/alert/prompt
 * 2. CDP triggers Page.javascriptDialogOpening event
 * 3. DialogManager notifies server via WebSocket
 * 4. AI assistant decides how to respond
 * 5. Server sends handle_dialog command
 * 6. DialogManager executes Page.handleJavaScriptDialog
 */

import { CdpCommander } from './cdp-commander';
import { debuggerManager } from './debugger-manager';
import { wsClient } from '../websocket/client';
import type { DialogOpenedEvent, DialogType, DialogAction } from '../types';

/**
 * Dialog information stored when a dialog opens
 */
interface DialogResult {
  tabId: number;
  dialogType: DialogType;
  message: string;
  url: string;
  timestamp: number;
  hasBrowserHandler: boolean;
}

/**
 * DialogManager - Manages JavaScript dialog handling
 */
export class DialogManager {
  private dialogListener: ((source: chrome.debugger.Debuggee, method: string, params?: object) => void) | null = null;
  private activeDialogs = new Map<number, DialogResult>();  // tabId -> dialog info
  private enabledTabs = new Set<number>();  // Tabs with dialog handling enabled

  /**
   * Enable dialog handling for a tab
   * This attaches debugger and sets up event listener
   */
  async enableDialogHandling(tabId: number): Promise<void> {
    console.log(`💬 [Dialog] Enabling dialog handling for tab ${tabId}`);

    // Skip if already enabled
    if (this.enabledTabs.has(tabId)) {
      console.log(`💬 [Dialog] Dialog handling already enabled for tab ${tabId}`);
      return;
    }

    // Attach debugger
    const attached = await debuggerManager.safeAttachDebugger(tabId);
    if (!attached) {
      throw new Error(`Failed to attach debugger for dialog handling on tab ${tabId}`);
    }

    const cdpCommander = new CdpCommander(tabId);

    // Enable Page domain
    try {
      await cdpCommander.sendCommand('Page.enable', {}, 5000);
      console.log(`✅ [Dialog] Page domain enabled for tab ${tabId}`);
    } catch (error) {
      console.warn(`⚠️ [Dialog] Page.enable failed (may already be enabled):`, error);
    }

    // Register dialog event listener if not already registered
    if (!this.dialogListener) {
      this.dialogListener = (source: chrome.debugger.Debuggee, method: string, params?: object) => {
        if (method === 'Page.javascriptDialogOpening' && source.tabId !== undefined) {
          this.handleDialogOpening(source.tabId, params);
        }
      };

      chrome.debugger.onEvent.addListener(this.dialogListener);
      console.log('✅ [Dialog] Global dialog event listener registered');
    }

    // Mark this tab as enabled
    this.enabledTabs.add(tabId);
    console.log(`✅ [Dialog] Dialog handling enabled for tab ${tabId}`);
  }

  /**
   * Disable dialog handling for a tab
   */
  async disableDialogHandling(tabId: number): Promise<void> {
    console.log(`💬 [Dialog] Disabling dialog handling for tab ${tabId}`);

    this.enabledTabs.delete(tabId);
    this.activeDialogs.delete(tabId);

    // Note: We don't remove the global listener as other tabs may still need it
    // The listener will check if the tab is in enabledTabs
    console.log(`✅ [Dialog] Dialog handling disabled for tab ${tabId}`);
  }

  /**
   * Handle Page.javascriptDialogOpening event
   * This is called when a dialog opens
   */
  private async handleDialogOpening(tabId: number, params: any): Promise<void> {
    console.log(`💬 [Dialog] Dialog opening on tab ${tabId}:`, params);

    // Only process if dialog handling is enabled for this tab
    if (!this.enabledTabs.has(tabId)) {
      console.log(`💬 [Dialog] Dialog handling not enabled for tab ${tabId}, ignoring`);
      return;
    }

    const dialogInfo: DialogResult = {
      tabId: tabId,
      dialogType: params.type as DialogType,
      message: params.message || '',
      url: params.url || '',
      timestamp: Date.now(),
      hasBrowserHandler: params.hasBrowserHandler || false,
    };

    // Store dialog info
    this.activeDialogs.set(tabId, dialogInfo);

    // Notify server via WebSocket
    const event: DialogOpenedEvent = {
      type: 'dialog_opened',
      tab_id: tabId,
      conversation_id: undefined,  // Will be set by background script
      dialog_type: dialogInfo.dialogType,
      message: dialogInfo.message,
      url: dialogInfo.url,
      timestamp: dialogInfo.timestamp,
    };

    console.log(`💬 [Dialog] Sending dialog_opened event to server:`, event);

    if (wsClient.isConnected()) {
      try {
        wsClient.sendCommand(event as any);
        console.log(`✅ [Dialog] Dialog event sent to server`);
      } catch (error) {
        console.error(`❌ [Dialog] Failed to send dialog event:`, error);
      }
    } else {
      console.warn(`⚠️ [Dialog] WebSocket not connected, cannot send dialog event`);
    }
  }

  /**
   * Handle a dialog (accept or dismiss)
   * This is called when AI decides how to respond
   */
  async handleDialog(tabId: number, action: DialogAction, promptText?: string): Promise<void> {
    console.log(`💬 [Dialog] Handling dialog on tab ${tabId}: action=${action}, promptText=${promptText}`);

    // Check if there's an active dialog for this tab
    const dialogInfo = this.activeDialogs.get(tabId);
    if (!dialogInfo) {
      throw new Error(`No active dialog found for tab ${tabId}`);
    }

    const cdpCommander = new CdpCommander(tabId);

    try {
      // Execute Page.handleJavaScriptDialog
      await cdpCommander.sendCommand('Page.handleJavaScriptDialog', {
        accept: action === 'accept',
        promptText: promptText || '',
      }, 5000);

      console.log(`✅ [Dialog] Dialog handled: ${action}${promptText ? `, text="${promptText}"` : ''}`);

      // Remove active dialog
      this.activeDialogs.delete(tabId);
    } catch (error) {
      console.error(`❌ [Dialog] Failed to handle dialog:`, error);
      throw new Error(`Failed to handle dialog: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Get active dialog info for a tab
   */
  getActiveDialog(tabId: number): DialogResult | undefined {
    return this.activeDialogs.get(tabId);
  }

  /**
   * Check if there's an active dialog for a tab
   */
  hasActiveDialog(tabId: number): boolean {
    return this.activeDialogs.has(tabId);
  }

  /**
   * Clean up all dialog handling (for extension shutdown)
   */
  cleanup(): void {
    if (this.dialogListener) {
      chrome.debugger.onEvent.removeListener(this.dialogListener);
      this.dialogListener = null;
    }

    this.enabledTabs.clear();
    this.activeDialogs.clear();
    console.log('✅ [Dialog] Dialog manager cleaned up');
  }
}

// Singleton instance
export const dialogManager = new DialogManager();
