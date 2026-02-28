/**
 * Element Actions - Element-based interaction commands
 *
 * Provides element-based click and interaction commands that use cached
 * element selectors instead of pixel coordinates.
 *
 * DESIGN:
 * - Looks up elements from cache by element_id
 * - Executes JavaScript with full event sequence for React/Vue compatibility
 * - Handles dialog events using the same pattern as javascript.ts
 */

import type { ElementActionResult } from '../types';
import { elementCache } from './element-cache';
import { executeJavaScript, type JavaScriptResult } from './javascript';
import { captureScreenshot } from './screenshot';

/**
 * Result type for element click operation
 */
export interface ClickResult extends ElementActionResult {
  clicked: boolean;
  staleElement?: boolean;
}

/**
 * Perform a click on an element identified by its cached element_id
 *
 * Flow:
 * 1. Look up element from cache
 * 2. Build JavaScript to click with full event sequence
 * 3. Execute with dialog detection
 * 4. Capture screenshot for verification
 * 5. Return result with dialog info if applicable
 *
 * @param conversationId Session ID for element cache lookup
 * @param elementId Cached element ID (e.g., "click-1", "scroll-1")
 * @param tabId Target tab ID
 * @param timeout Maximum execution time in milliseconds (default: 30000)
 * @returns Click result with success status, screenshot, and dialog info
 */
export async function performElementClick(
  conversationId: string,
  elementId: string,
  tabId: number,
  timeout: number = 30000
): Promise<ClickResult> {
  console.log(
    `👆 [ElementClick] Clicking element ${elementId} in conversation ${conversationId} on tab ${tabId}`
  );

  // ============================================================
  // STEP 1: Look up element from cache
  // ============================================================
  const element = elementCache.getElementById(conversationId, elementId);
  if (!element) {
    console.log(`❌ [ElementClick] Element ${elementId} not found in cache`);
    return {
      success: false,
      elementId,
      clicked: false,
      staleElement: false,
    };
  }

  console.log(`✅ [ElementClick] Found element: selector="${element.selector}"`);

  // ============================================================
  // STEP 2: Build JavaScript to click with full event sequence
  // ============================================================
  // Escape quotes in selector for safe injection
  const escapedSelector = element.selector.replace(/"/g, '\\"');

  const script = `
    (function() {
      const selector = "${escapedSelector}";
      const el = document.querySelector(selector);

      if (!el) {
        return { clicked: false, error: "Element not found in DOM", stale: true };
      }

      // Check if element is still visible
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);

      if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
        return { clicked: false, error: "Element is not visible", stale: false };
      }

      // Scroll element into view if needed
      if (rect.top < 0 || rect.bottom > window.innerHeight ||
          rect.left < 0 || rect.right > window.innerWidth) {
        el.scrollIntoView({ behavior: 'instant', block: 'center', inline: 'center' });
      }

      // Full event sequence for React/Vue compatibility
      // Using PointerEvent for modern browsers, falls back to MouseEvent
      const eventOptions = {
        bubbles: true,
        cancelable: true,
        view: window,
        button: 0,
        buttons: 1,
      };

      try {
        // Pointer events sequence
        const pointerEvents = ['pointerdown', 'pointerup'];
        for (const eventType of pointerEvents) {
          const event = new PointerEvent(eventType, {
            ...eventOptions,
            pointerType: 'mouse',
            isPrimary: true,
          });
          el.dispatchEvent(event);
        }

        // Mouse events sequence
        const mouseEvents = ['mousedown', 'mouseup', 'click'];
        for (const eventType of mouseEvents) {
          const event = new MouseEvent(eventType, eventOptions);
          el.dispatchEvent(event);
        }

        // Focus the element if it's focusable
        if (typeof el.focus === 'function') {
          el.focus();
        }

        return { clicked: true };
      } catch (e) {
        return { clicked: false, error: e.message || String(e) };
      }
    })();
  `;

  // ============================================================
  // STEP 3: Execute JavaScript with dialog detection
  // ============================================================
  let jsResult: JavaScriptResult;

  try {
    jsResult = await executeJavaScript(tabId, conversationId, script, true, false, timeout);
  } catch (error) {
    console.error(`❌ [ElementClick] JavaScript execution error:`, error);
    return {
      success: false,
      elementId,
      clicked: false,
      staleElement: false,
    };
  }

  // ============================================================
  // STEP 4: Process result and handle dialog
  // ============================================================

  // If dialog opened during click
  if (jsResult.dialog_opened && jsResult.dialog) {
    console.log(`💬 [ElementClick] Dialog opened during click: type=${jsResult.dialog.type}`);

    // Try to capture screenshot even with dialog (may fail)
    let screenshotDataUrl: string | undefined;
    try {
      const screenshotResult = await captureScreenshot(tabId, conversationId, false, 80);
      screenshotDataUrl = screenshotResult?.dataUrl;
    } catch {
      // Screenshot may fail with dialog open, that's okay
    }

    return {
      success: true,
      elementId,
      clicked: true,
      dialogOpened: true,
      dialog: {
        type: jsResult.dialog.type,
        message: jsResult.dialog.message,
      },
      screenshotDataUrl,
    };
  }

  // Check for execution errors
  if (!jsResult.success) {
    console.log(`❌ [ElementClick] Click execution failed: ${jsResult.error}`);
    return {
      success: false,
      elementId,
      clicked: false,
      staleElement: false,
    };
  }

  // Check the result from the script
  const clickResult = jsResult.result as { clicked: boolean; error?: string; stale?: boolean } | undefined;

  if (!clickResult?.clicked) {
    const isStale = clickResult?.stale === true;
    console.log(
      `❌ [ElementClick] Click failed: ${clickResult?.error || 'Unknown error'}, stale=${isStale}`
    );

    return {
      success: false,
      elementId,
      clicked: false,
      staleElement: isStale,
    };
  }

  // ============================================================
  // STEP 5: Capture screenshot for verification
  // ============================================================
  console.log(`✅ [ElementClick] Click executed successfully`);

  let screenshotDataUrl: string | undefined;
  try {
    const screenshotResult = await captureScreenshot(tabId, conversationId, false, 80);
    screenshotDataUrl = screenshotResult?.dataUrl;
  } catch (screenshotError) {
    console.warn(`⚠️ [ElementClick] Failed to capture screenshot:`, screenshotError);
    // Continue without screenshot
  }

  return {
    success: true,
    elementId,
    clicked: true,
    screenshotDataUrl,
  };
}

/**
 * Export element actions module
 */
export const elementActions = {
  performElementClick,
};
