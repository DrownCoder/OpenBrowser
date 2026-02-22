/**
 * JavaScript Execution Tool Implementation
 * Enables execution of JavaScript code in browser tabs via Chrome DevTools Protocol
 */

import { CdpCommander } from './cdp-commander';
import { debuggerManager } from './debugger-manager';

/**
 * CDP Runtime.evaluate response type
 */
interface RuntimeEvaluateResult {
  result?: {
    type: string;
    subtype?: string;
    value?: any;
    description?: string;
    objectId?: string;
    className?: string;
  };
  exceptionDetails?: {
    exception?: {
      type?: string;
      subtype?: string;
      value?: any;
      description?: string;
    };
    text?: string;
    lineNumber?: number;
    columnNumber?: number;
    stackTrace?: any;
  };
}

/**
 * Console output entry type
 */
interface ConsoleOutputEntry {
  type: 'log' | 'warn' | 'error' | 'info' | 'debug' | 'table' | 'trace' | 'dir' | string;
  args: any[];  // Serialized console arguments
  timestamp: number;
  url?: string;
  line?: number;
  column?: number;
}

/**
 * Execute JavaScript code in a tab using CDP Runtime.evaluate
 * @param tabId Target tab ID
 * @param script JavaScript code to execute
 * @param returnByValue If true, returns result as serializable JSON value (default: true)
 * @param awaitPromise If true, waits for Promise resolution (default: false)
 * @param timeout Maximum execution time in milliseconds (default: 30000)
 * @returns Execution result with success status, data, and console output
 */
export async function executeJavaScript(
  tabId: number,
  script: string,
  returnByValue: boolean = true,
  awaitPromise: boolean = false,
  timeout: number = 30000,
): Promise<any> {
  console.log(`📜 [JavaScript] Executing JavaScript in tab ${tabId}:`, script.substring(0, 100) + (script.length > 100 ? '...' : ''));

  // Attach debugger to tab (required for CDP commands)
  const attached = await debuggerManager.safeAttachDebugger(tabId);
  if (!attached) {
    throw new Error('Failed to attach debugger to tab');
  }

  const cdpCommander = new CdpCommander(tabId);
  
  // Collect console output during script execution
  const consoleOutput: ConsoleOutputEntry[] = [];
  let consoleListener: ((source: chrome.debugger.Debuggee, method: string, params?: object) => void) | null = null;

  try {
    // Enable Runtime domain if not already enabled
    try {
      await cdpCommander.sendCommand('Runtime.enable', {}, 5000);
      console.log('✅ [JavaScript] Runtime domain enabled');
    } catch (enableError) {
      console.warn('⚠️ [JavaScript] Runtime.enable failed, but continuing:', enableError);
      // Continue anyway - Runtime might already be enabled
    }

    // Set up console listener to capture console API calls
    consoleListener = (source: chrome.debugger.Debuggee, method: string, params?: object) => {
      if (source.tabId === tabId && method === 'Runtime.consoleAPICalled') {
        const consoleParams = params as any;
        
        // Serialize console arguments for transmission
        const serializedArgs = (consoleParams.args || []).map((arg: any) => {
          // Handle RemoteObject from CDP
          if (arg.type === 'string') {
            return arg.value || arg.description || '';
          } else if (arg.type === 'number') {
            return arg.value || 0;
          } else if (arg.type === 'boolean') {
            return arg.value || false;
          } else if (arg.type === 'undefined') {
            return undefined;
          } else if (arg.type === 'object' || arg.type === 'function') {
            // For objects and functions, try to get a readable representation
            return arg.description || arg.preview?.description || JSON.stringify(arg.value || {});
          } else {
            return arg.description || arg.value || String(arg);
          }
        });

        consoleOutput.push({
          type: consoleParams.type || 'log',
          args: serializedArgs,
          timestamp: consoleParams.timestamp || Date.now(),
          url: consoleParams.stackTrace?.callFrames?.[0]?.url,
          line: consoleParams.stackTrace?.callFrames?.[0]?.lineNumber,
          column: consoleParams.stackTrace?.callFrames?.[0]?.columnNumber,
        });
        
        console.log(`🖥️ [Console] Captured ${consoleParams.type}:`, ...serializedArgs);
      }
    };

    // Register console listener
    chrome.debugger.onEvent.addListener(consoleListener);
    console.log('🎯 [JavaScript] Console listener registered');

    // Execute JavaScript using Runtime.evaluate
    console.log(`📜 [JavaScript] Sending Runtime.evaluate command`);
    
    const result = await cdpCommander.sendCommand<RuntimeEvaluateResult>('Runtime.evaluate', {
      expression: script,
      returnByValue,
      awaitPromise,
      timeout: timeout, // CDP timeout parameter (milliseconds)
    }, timeout + 5000); // Add buffer for command round-trip

    console.log(`✅ [JavaScript] JavaScript execution successful`);

    // Process result
    const response: any = {
      success: true,
      message: 'JavaScript executed successfully',
      consoleOutput: consoleOutput.length > 0 ? consoleOutput : undefined,  // ✅ Add console output
    };

    if (result.exceptionDetails) {
      // Execution threw an exception
      const exception = result.exceptionDetails.exception;
      response.success = false;
      response.error = `JavaScript execution threw exception: ${exception?.description || exception?.value || 'Unknown error'}`;
      response.exceptionDetails = result.exceptionDetails;
      console.error(`❌ [JavaScript] JavaScript execution threw exception:`, result.exceptionDetails);
    } else if (result.result) {
      // Execution succeeded
      response.result = result.result;
      
      // Log result type for debugging
      console.log(`📊 [JavaScript] Result type: ${result.result.type}, value:`, 
        result.result.type === 'object' ? `Object(${result.result.subtype || 'unknown'})` :
        result.result.type === 'undefined' ? 'undefined' :
        JSON.stringify(result.result.value).substring(0, 200));
    } else {
      // No result (should not happen with returnByValue: true)
      console.warn('⚠️ [JavaScript] No result returned from Runtime.evaluate');
    }

    return response;
  } catch (error) {
    console.error(`❌ [JavaScript] JavaScript execution failed:`, error);
    throw new Error(`JavaScript execution failed: ${error instanceof Error ? error.message : String(error)}`);
  } finally {
    // Remove console listener before detaching debugger
    if (consoleListener) {
      chrome.debugger.onEvent.removeListener(consoleListener);
      console.log('🔌 [JavaScript] Console listener removed');
    }
    
    // Detach debugger to clean up resources
    await debuggerManager.safeDetachDebugger(tabId);
  }
}

/**
 * Execute JavaScript and return primitive value directly
 * Simplified wrapper for common use cases
 */
export async function evaluateJavaScript(
  tabId: number,
  script: string,
  timeout: number = 30000,
): Promise<any> {
  const result = await executeJavaScript(tabId, script, true, false, timeout);
  
  if (!result.success) {
    throw new Error(result.error || 'JavaScript evaluation failed');
  }
  
  // Extract value from CDP result object
  if (result.result && result.result.type === 'undefined') {
    return undefined;
  }
  
  return result.result?.value;
}

export const javascript = {
  executeJavaScript,
  evaluateJavaScript,
};