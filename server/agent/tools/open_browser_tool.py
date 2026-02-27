"""
OpenBrowserTool - AI tool for controlling Chrome browser with visual feedback.

This tool allows an AI agent to control a Chrome browser using the existing
Local Chrome Server infrastructure. After each operation, it returns both
textual information (current tab list, mouse position) and a screenshot
image for visual feedback.
"""

import time
import logging
import threading
import requests
from typing import Optional, List, Dict, Any, Literal, Union
from enum import Enum
from collections.abc import Sequence

from pydantic import Field, SecretStr
from openhands.sdk import Action, Observation, ImageContent, TextContent
from openhands.sdk.tool import ToolExecutor, ToolDefinition, register_tool

logger = logging.getLogger(__name__)

from server.core.processor import command_processor
from server.models.commands import (
    ScreenshotCommand,
    TabCommand, GetTabsCommand, JavascriptExecuteCommand,
    HandleDialogCommand, DialogAction,
    TabAction
)

logger = logging.getLogger(__name__)


class OpenBrowserAction(Action):
    """Browser automation action with unified parameter system"""
    type: str = Field(description="Type of browser operation: 'javascript_execute', 'tab', 'handle_dialog', 'view'")
    # JavaScript execution parameters
    script: Optional[str] = Field(default=None, description="JavaScript code to execute for javascript_execute")
    # Tab operation parameters
    action: Optional[str] = Field(default=None, description="Action for tab operations: 'init', 'open', 'close', 'switch', 'list', 'refresh'")
    url: Optional[str] = Field(default=None, description="URL for tab operations (required for init and open)")
    tab_id: Optional[int] = Field(default=None, description="Tab ID for tab operations (required for close, switch, refresh)")
    # Dialog handling parameters
    dialog_action: Optional[str] = Field(
        default=None, 
        description="Action for dialog handling: 'accept' or 'dismiss'"
    )
    prompt_text: Optional[str] = Field(
        default=None,
        description="Text to enter for prompt dialogs (only for handle_dialog with prompt)"
    )
    # Note: 'view' action requires no additional parameters

# --- Supported Action Types and Their Parameters ---
"""
Supported action types and their parameters:

1. javascript_execute - Execute JavaScript code in current tab
   Parameters: {
     "type": "javascript_execute",
     "script": str  # JavaScript code to execute
   }

2. tab - Tab management operations
   Parameters: {
     "type": "tab",
     "action": str,  # "init", "open", "close", "switch", "list", "refresh"
     "url": str (optional),  # URL for open/init actions
     "tab_id": int (optional)  # Tab ID for close, switch, and refresh actions
   }

3. view - Capture screenshot to see current page state
   Parameters: {
     "type": "view"  # No additional parameters needed
   }
"""


# --- Observation ---

class OpenBrowserObservation(Observation):
    """Observation returned by OpenBrowserTool after each action"""
    
    success: bool = Field(description="Whether the operation succeeded")
    message: Optional[str] = Field(default=None, description="Result message")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    tabs: List[Dict[str, Any]] = Field(default_factory=list, description="List of current tabs")
    mouse_position: Optional[Dict[str, int]] = Field(
        default=None,
        description="Current mouse position in preset coordinate system (x, y)"
    )
    screenshot_data_url: Optional[str] = Field(
        default=None,
        description="Screenshot as data URL (base64 encoded PNG, 1280x720 pixels)"
)
    javascript_result: Optional[Any] = Field(
        default=None,
        description="Result of JavaScript execution (if action was javascript_execute)"
    )
    console_output: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Console output captured during JavaScript execution (list of {type, args, timestamp})"
    )
    # Dialog-related fields
    dialog_opened: Optional[bool] = Field(
        default=None,
        description="Whether a dialog is currently open"
    )
    dialog: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dialog information if a dialog is open (type, message, needsDecision)"
    )
    @property
    def to_llm_content(self) -> Sequence[TextContent | ImageContent]:
        """Convert observation to LLM content format"""
        import json
        
        content_items = []
        text_parts = []
        
        # Operation Status Section
        text_parts.append("## Operation Status")
        text_parts.append("")
        if not self.success:
            text_parts.append(f"**Status**: FAILED")
            text_parts.append(f"**Error**: {self.error}")
        else:
            text_parts.append(f"**Status**: SUCCESS")
            # For JavaScript operations, show minimal confirmation
            if self.javascript_result is not None and self.message:
                # Extract just "Executed JavaScript" without the script content
                if "Executed JavaScript:" in self.message:
                    text_parts.append("**Action**: JavaScript code executed successfully")
                else:
                    text_parts.append(f"**Action**: {self.message}")
            elif self.message:
                text_parts.append(f"**Action**: {self.message}")
        
        text_parts.append("")
        
        # JavaScript Result Section (if applicable)
        if self.javascript_result is not None:
            text_parts.append("## Execution Result")
            text_parts.append("")
            
            # Format result based on type
            if isinstance(self.javascript_result, (dict, list)):
                try:
                    # Pretty-print JSON with indentation
                    result_str = json.dumps(self.javascript_result, indent=2, ensure_ascii=False)
                    if len(result_str) > 50000:
                        result_str = result_str[:50000] + "\n... (output truncated)"
                    text_parts.append("```json")
                    text_parts.append(result_str)
                    text_parts.append("```")
                except (TypeError, ValueError):
                    # Fallback to string representation
                    result_str = str(self.javascript_result)
                    if len(result_str) > 50000:
                        result_str = result_str[:50000] + "... (truncated)"
                    text_parts.append("```")
                    text_parts.append(result_str)
                    text_parts.append("```")
            else:
                # For non-dict/list results (strings, numbers, etc.)
                result_str = str(self.javascript_result)
                if len(result_str) > 50000:
                    result_str = result_str[:50000] + "... (truncated)"
                text_parts.append("```")
                text_parts.append(result_str)
                text_parts.append("```")
            text_parts.append("")
        
        # Console Output Section (if applicable)
        if self.console_output and len(self.console_output) > 0:
            text_parts.append("## Console Output")
            text_parts.append("")
            
            for entry in self.console_output:
                console_type = entry.get('type', 'log')
                args = entry.get('args', [])
                timestamp = entry.get('timestamp')
                
                # Format console type with emoji
                type_emoji = {
                    'log': '📝',
                    'warn': '⚠️',
                    'error': '❌',
                    'info': 'ℹ️',
                    'debug': '🔍',
                    'table': '📊',
                    'trace': '🔍',
                    'dir': '📁'
                }.get(console_type, '📝')
                
                # Format arguments
                formatted_args = []
                for arg in args:
                    if arg is None:
                        formatted_args.append('undefined')
                    elif isinstance(arg, str):
                        formatted_args.append(arg)
                    elif isinstance(arg, (dict, list)):
                        try:
                            formatted_args.append(json.dumps(arg, indent=2, ensure_ascii=False))
                        except:
                            formatted_args.append(str(arg))
                    else:
                        formatted_args.append(str(arg))
                
                # Join multiple arguments
                args_str = ' '.join(formatted_args)
                if len(args_str) > 1000:
                    args_str = args_str[:1000] + "... (truncated)"
                
# Add console line with type
                text_parts.append(f"{type_emoji} **[{console_type}]** {args_str}")
            
            text_parts.append("")
        
        # Dialog Section (if applicable)
        if self.dialog_opened and self.dialog:
            text_parts.append("## ⚠️ Dialog Opened")
            text_parts.append("")
            dialog_type = self.dialog.get('type', 'unknown')
            dialog_message = self.dialog.get('message', '')
            needs_decision = self.dialog.get('needsDecision', False)
            
            text_parts.append(f"**Type**: {dialog_type}")
            text_parts.append(f"**Message**: \"{dialog_message}\"")
            text_parts.append(f"**Needs Decision**: {'Yes' if needs_decision else 'No'}")
            text_parts.append("")
            
            if needs_decision:
                text_parts.append("**Action Required**: Use `handle_dialog` to respond.")
                text_parts.append("- To accept: `{\"type\": \"handle_dialog\", \"dialog_action\": \"accept\"}`")
                text_parts.append("- To dismiss: `{\"type\": \"handle_dialog\", \"dialog_action\": \"dismiss\"}`")
                text_parts.append("- For prompts: `{\"type\": \"handle_dialog\", \"dialog_action\": \"accept\", \"prompt_text\": \"your text\"}`")
            else:
                text_parts.append("**Note**: This dialog was auto-accepted (no decision needed).")
            text_parts.append("")
        
        # Browser State Section
        if self.tabs:
            text_parts.append("## Browser State")
            text_parts.append("")
            text_parts.append(f"**Open Tabs** ({len(self.tabs)}):")
            text_parts.append("")
            for i, tab in enumerate(self.tabs, 1):
                active_marker = "●" if tab.get('active') else "○"
                title = tab.get('title', 'No title')[:50]
                url = tab.get('url', 'No URL')
                # ✅ FIX: Use 'tabId' (from Extension ManagedTab) or fallback to 'id'
                tab_id = tab.get('tabId') or tab.get('id', 'unknown')
                text_parts.append(f"{i}. {active_marker} **[{tab_id}]** {title}")
                text_parts.append(f"   URL: {url}")
            text_parts.append("")
        
        if self.mouse_position:
            text_parts.append("## Cursor Position")
            text_parts.append("")
            x = self.mouse_position['x']
            y = self.mouse_position['y']
            text_parts.append(f"**Coordinates**: ({x}, {y})")
            text_parts.append(f"**System**: Preset coordinate system (center: 0,0; right: +X; down: +Y)")
            text_parts.append("")
        
        text_content = "\n".join(text_parts)
        content_items.append(TextContent(text=text_content))
        
        # Add image content if screenshot is available
        if self.screenshot_data_url:
            content_items.append(ImageContent(image_urls=[self.screenshot_data_url]))
        
        return content_items

    @property
    def visualize(self):
        """Return Rich Text representation for visualization.
        
        This method is called by QueueVisualizer.on_event() to get text content
        for SSE streaming. We extract only TextContent from to_llm_content and
        ignore ImageContent, since images are extracted separately via the
        screenshot_data_url field.
        
        Returns:
            rich.text.Text: Rich Text object with formatted content
        """
        from rich.text import Text
        
        # Get all content from to_llm_content
        llm_content = self.to_llm_content
        
        # Extract only text content, ignore ImageContent
        # (images are extracted separately via screenshot_data_url in agent.py)
        text_parts = []
        for item in llm_content:
            if isinstance(item, TextContent):
                text_parts.append(item.text)
        
        # Combine all text parts
        full_text = "\n".join(text_parts) if text_parts else "[no content]"
        
        # Return as Rich Text object
        return Text(full_text)


# --- Executor ---

class OpenBrowserExecutor(ToolExecutor[OpenBrowserAction, OpenBrowserObservation]):
    """Executor for browser automation commands"""
    
    def __init__(self):
        self.conversation_id = None

    
    async def _execute_command(self, command) -> Any:
        """Execute command with conversation context"""
        logger.debug(f"DEBUG: _execute_command called with action_type={command.type}, conversation_id={self.conversation_id}")
        
        # Set conversation_id for multi-session support
        if hasattr(command, 'conversation_id'):
            command.conversation_id = self.conversation_id
        
        result = await command_processor.execute(command)
        logger.debug(f"DEBUG: _execute_command result: success={result.success if result else 'None'}")
        return result
    
    def _execute_action_sync(self, action: OpenBrowserAction) -> OpenBrowserObservation:
        """Execute a browser action synchronously via HTTP"""
        logger.debug(f"DEBUG: _execute_action_sync called with action_type={action.type}")
        try:
            # Get action type
            action_type = action.type
            
            # Convert to appropriate server command based on type
            result_dict = None
            message = ""
            javascript_result = None  # Store JavaScript execution result
            console_output = None  # Store console output from JavaScript execution
            
            if action_type == "tab":
                # Validate required parameters
                if action.action is None:
                    raise ValueError("tab requires action parameter")
                action_str = action.action
                # Convert action string to TabAction enum
                # TabAction enum values are uppercase, so convert 'open' -> 'OPEN'
                try:
                    action_enum = TabAction(action_str.upper())
                except ValueError:
                    # If direct conversion fails, try to map common values
                    action_map = {
                        'init': TabAction.INIT,
                        'open': TabAction.OPEN,
                        'close': TabAction.CLOSE,
                        'switch': TabAction.SWITCH,
                        'list': TabAction.LIST,
                        'refresh': TabAction.REFRESH
                    }
                    if action_str in action_map:
                        action_enum = action_map[action_str]
                    else:
                        raise ValueError(f"Invalid tab action: {action_str}")
                
                command = TabCommand(
                    action=action_enum,
                    url=action.url,
                    tab_id=action.tab_id,
                    conversation_id=self.conversation_id  # ✅ FIX: Pass conversation_id during creation
                )
                result_dict = self._execute_command_sync(command)
                
                if action_str == "open":
                    message = f"Opened tab with URL: {action.url}"
                elif action_str == "init":
                    message = f"Initialized session with URL: {action.url}"
                elif action_str == "close":
                    message = f"Closed tab ID: {action.tab_id}"
                elif action_str == "switch":
                    message = f"Switched to tab ID: {action.tab_id}"
                elif action_str == "refresh":
                    message = f"Refreshed tab ID: {action.tab_id}"
                elif action_str == "list":
                    message = "Listed tabs"
                else:
                    message = f"Tab action: {action_str}"
                    
            elif action_type == "javascript_execute":
                # Validate required parameters
                if action.script is None:
                    raise ValueError("javascript_execute requires script parameter")
                command = JavascriptExecuteCommand(
                    script=action.script,
                    conversation_id=self.conversation_id  # ✅ FIX: Pass conversation_id
                )
                result_dict = self._execute_command_sync(command)
                
                # Truncate long scripts for message
                script = action.script
                if len(script) > 50:
                    message = f"Executed JavaScript: '{script[:50]}...'"
                else:
                    message = f"Executed JavaScript: '{script}'"
                
                # Extract JavaScript execution result for observation
                if result_dict and result_dict.get('data'):
                    js_data = result_dict['data']
                    # JavaScript module returns result in 'result' field
                    if isinstance(js_data, dict):
                        # Extract console output if available
                        if 'consoleOutput' in js_data:
                            console_output = js_data['consoleOutput']
                            logger.debug(f"DEBUG: Captured console output: {len(console_output)} entries")
                        
                        if 'result' in js_data:
                            js_result = js_data['result']
                            # CDP result object has 'value' field when returnByValue is true
                            if isinstance(js_result, dict) and 'value' in js_result:
                                javascript_result = js_result['value']
                            else:
                                javascript_result = js_result
                        # Also check for direct 'value' in data
                        elif 'value' in js_data:
                            javascript_result = js_data['value']
                        else:
                            # If no result or value, use the entire data dict
                            javascript_result = js_data
                    else:
                        # If data is not a dict (e.g., string error), use it as result
                        javascript_result = js_data
                    
# If we have a result, update message to include it (only for successful executions)
                    if javascript_result is not None and result_dict.get('success'):
                        result_str = str(javascript_result)
                        if len(result_str) > 100:
                            result_str = result_str[:100] + '...'
                        message = f"{message} - Result: {result_str}"
                elif result_dict and result_dict.get('error'):
                    # If there's an error but no data, use error as javascript_result
                    javascript_result = result_dict['error']
            elif action_type == "handle_dialog":
                # Handle dialog action (accept or dismiss)
                if action.dialog_action is None:
                    raise ValueError("handle_dialog requires dialog_action parameter")
                
                dialog_action_str = action.dialog_action
                try:
                    dialog_action = DialogAction(dialog_action_str.lower())
                except ValueError:
                    raise ValueError(f"Invalid dialog action: {dialog_action_str}. Must be 'accept' or 'dismiss'")
                
                command = HandleDialogCommand(
                    action=dialog_action,
                    prompt_text=action.prompt_text,
                    conversation_id=self.conversation_id
                )
                result_dict = self._execute_command_sync(command)
                
                message = f"Dialog handled: {dialog_action_str}"
                
            elif action_type == "view":
                # View action: capture screenshot to see current page state
                # No server command needed - just capture screenshot
                result_dict = None
                message = "Captured page view"
                
            else:
                raise ValueError(f"Unknown action type: {action_type}")
            
            # Determine what data to collect based on action type
            tabs_data = []
            mouse_position = None
            screenshot_data_url = None
            
            # Only capture screenshot for 'view' action
            if action_type == "view":
                logger.debug(f"DEBUG: Getting screenshot for view action (sync)...")
                # Wait for page to render
                time.sleep(1)
                screenshot_result = self._get_screenshot_sync()
                logger.debug(f"DEBUG: screenshot_result: success={screenshot_result.get('success')}, data keys={list(screenshot_result.get('data', {}).keys()) if screenshot_result.get('data') else 'None'}")
                
                if screenshot_result.get('success') and screenshot_result.get('data'):
                    # Try to extract image data
                    image_data = None
                    data = screenshot_result['data']
                    if 'imageData' in data:
                        image_data = data['imageData']
                    elif 'image_data' in data:
                        image_data = data['image_data']
                    
                    if image_data:
                        # Ensure it's a data URL
                        if isinstance(image_data, str) and image_data.startswith('data:image/'):
                            screenshot_data_url = image_data
                        elif isinstance(image_data, str):
                            # Convert base64 to data URL
                            screenshot_data_url = f"data:image/png;base64,{image_data}"
                        else:
                            logger.debug(f"DEBUG: Unexpected image_data type: {type(image_data)}")
            
            # Collect tabs data only for tab operations
            if action_type == "tab":
                logger.debug(f"DEBUG: Getting tabs after tab action (sync)...")
                tabs_result = self._get_tabs_sync()
                logger.debug(f"DEBUG: tabs_result: success={tabs_result.get('success')}, data keys={list(tabs_result.get('data', {}).keys()) if tabs_result.get('data') else 'None'}")
                
                if tabs_result.get('success') and tabs_result.get('data') and 'tabs' in tabs_result['data']:
                    tabs_data = tabs_result['data']['tabs']
            
            # Extract success and dialog info from result_dict
            success = True  # Default to True for view action
            error = None
            dialog_opened = None
            dialog = None
            
            if result_dict:
                success = result_dict.get('success', False)
                if 'error' in result_dict:
                    error = result_dict['error']
                elif 'message' in result_dict and 'error' in result_dict.get('data', {}):
                    error = result_dict['data']['error']
                
                # Extract dialog info if present
                if 'dialog_opened' in result_dict:
                    dialog_opened = result_dict['dialog_opened']
                if 'dialog' in result_dict:
                    dialog = result_dict['dialog']
                    # Update message for dialog scenarios
                    if dialog and success:
                        if dialog.get('needsDecision'):
                            message = f"Dialog opened: {dialog.get('type')} (\"{dialog.get('message')}\"). Use handle_dialog to respond."
                        else:
                            message = f"Dialog auto-accepted: {dialog.get('type')} (\"{dialog.get('message')}\")"
            
            return OpenBrowserObservation(
                success=success,
                message=message,
                error=error,
                tabs=tabs_data,
                mouse_position=mouse_position,
                screenshot_data_url=screenshot_data_url,
                javascript_result=javascript_result,
                console_output=console_output,
                dialog_opened=dialog_opened,
                dialog=dialog
            )
            
        except ValueError as e:
            # Provide friendly error message for missing parameters
            logger.error(f"ValueError (sync): {e} in action '{action.type}'")
            error_msg = f"Missing or invalid parameters for action '{action.type}': {e}"
            return OpenBrowserObservation(
                success=False,
                error=error_msg,
                tabs=[],
                mouse_position=None,
                screenshot_data_url=None,
                javascript_result=None,
                console_output=None,
                dialog_opened=None,
                dialog=None
            )
        except Exception as e:
            logger.debug(f"DEBUG: _execute_action_sync caught exception: {e}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error(f"Error executing browser action (sync): {e}")
            return OpenBrowserObservation(
                success=False,
                error=str(e),
                tabs=[],
                mouse_position=None,
                screenshot_data_url=None,
                javascript_result=None,
                console_output=None,
                dialog_opened=None,
                dialog=None
            )
    
    def __call__(self, action: OpenBrowserAction, conversation) -> OpenBrowserObservation:
        """Execute a browser action and return observation"""
        self.conversation_id = str(conversation._state.id)

        # Use synchronous HTTP API to avoid event loop competition with WebSocket
        logger.debug(f"DEBUG: OpenBrowserTool.__call__ called with action: {action.type}, conversation_id: {self.conversation_id}")
        logger.debug(f"DEBUG: Current thread: {threading.current_thread().name}")
        
        try:
            # Use synchronous execution (avoids event loop issues)
            logger.debug(f"DEBUG: Using synchronous HTTP API for tool execution")
            obs = self._execute_action_sync(action)
            logger.debug(f"DEBUG: OpenBrowserTool.__call__ returning observation: success={obs.success}, message={obs.message}, tabs_count={len(obs.tabs)}, has_screenshot={obs.screenshot_data_url is not None}")
            return obs
                
        except Exception as e:
            logger.debug(f"DEBUG: OpenBrowserTool.__call__ exception: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _execute_command_sync(self, command) -> Any:
        """Execute a command synchronously via HTTP with conversation context"""
        logger.debug(f"DEBUG: _execute_command_sync called with command type: {command.type if hasattr(command, 'type') else type(command).__name__}, conversation_id={self.conversation_id}")
        try:
            # Set conversation_id for multi-session support (backup if not set during creation)
            if hasattr(command, 'conversation_id'):
                if command.conversation_id is None:
                    command.conversation_id = self.conversation_id
                    logger.debug(f"🔍 Set conversation_id to {self.conversation_id}")
            
            # Convert command to dict using model_dump
            cmd_dict = command.model_dump()
            logger.info(f"🔍 Command dict: type={cmd_dict.get('type')}, conversation_id={cmd_dict.get('conversation_id')}")
            
            # Send HTTP POST to server - explicitly disable proxy for localhost
            response = requests.post(
                "http://127.0.0.1:8765/command",
                json=cmd_dict,
                timeout=30,
                proxies={'http': None, 'https': None}  # Disable proxy for local connections
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"DEBUG: _execute_command_sync returned: success={result.get('success')}")
            return result
        except Exception as e:
            logger.debug(f"DEBUG: _execute_command_sync exception: {e}")
            raise

    def _get_tabs_sync(self) -> Any:
        """Get current tab list synchronously"""
        logger.debug(f"DEBUG: _get_tabs_sync called, sending GetTabsCommand via HTTP")
        command = GetTabsCommand(
            managed_only=True,
            conversation_id=self.conversation_id  # ✅ FIX: Pass conversation_id
        )
        result = self._execute_command_sync(command)
        logger.debug(f"DEBUG: _get_tabs_sync result: success={result.get('success')}, data keys={list(result.get('data', {}).keys()) if result.get('data') else 'None'}")
        return result

    def _get_screenshot_sync(self) -> Any:
        """Capture screenshot synchronously"""
        logger.debug(f"DEBUG: _get_screenshot_sync called, sending ScreenshotCommand via HTTP")
        command = ScreenshotCommand(
            include_cursor=True,
            include_visual_mouse=True,
            quality=90,
            conversation_id=self.conversation_id  # ✅ FIX: Pass conversation_id
        )
        result = self._execute_command_sync(command)
        logger.debug(f"DEBUG: _get_screenshot_sync result: success={result.get('success')}, data keys={list(result.get('data', {}).keys()) if result.get('data') else 'None'}")
        return result


# --- Tool Definition ---

_OPEN_BROWSER_DESCRIPTION = """
Browser automation tool for controlling Chrome via JavaScript execution.

## Text-First, Visual-On-Demand Philosophy

Most browser operations can be done with text-only feedback:
- **javascript_execute**: Returns execution result and console output (no screenshot)
- **tab**: Returns current tab list (no screenshot)
- **handle_dialog**: Returns dialog status (no screenshot)

Use **view** action when you need visual context:
- After navigation to verify page loaded correctly
- When UI structure is unknown and you need to "see" the page
- After multiple operations to verify final state
- When you encounter unexpected behavior

This approach is **more efficient**: text operations are faster and cheaper than visual analysis.

---

## ⚠️ Important Notes Before You Start

- **React/Vue Applications**: Modern frameworks often ignore `.click()`. If a click doesn't work, immediately use [Full Event Sequence](#when-templates-dont-work).
- **2-Strike Rule**: If the same operation fails twice, switch to diagnostic mode immediately.
- **URL Navigation**: When UI interaction is complex (e.g., region switching), consider direct URL navigation as a faster alternative.

## 1. javascript_execute

```json
{
  "type": "javascript_execute",
  "script": "your JavaScript code here"
}
```

**Rules:**
- 30-second timeout
- Return values must be JSON-serializable (strings, numbers, plain objects, arrays). **Never return DOM nodes.**
- Use IIFE `(() => { ... })()` when you need `return` statements
- `console.log()` output is captured and visible
- Results over 50KB will be truncated

---

## Universal Templates

### Click by visible text

See something on screen? Click it. Replace `YOUR_TEXT` with any text you can see (partial match):

```javascript
(() => {
    const text = 'YOUR_TEXT';
    const leaf = Array.from(document.querySelectorAll('*'))
        .find(el => el.children.length === 0 && el.textContent.includes(text));
    if (!leaf) return 'not found';
    const target = leaf.closest('a, button, [role="button"], [onclick], [tabindex], tr, li') 
        || leaf.parentElement || leaf;
    target.click();
    return 'clicked: ' + target.tagName + ' | ' + target.textContent.trim().substring(0, 50);
})()
```

This single pattern handles ~90% of click tasks. It finds the innermost element containing your text, walks up to the nearest interactive ancestor, and clicks it.

### Fill an input field

Locate by nearby label or placeholder text, set value, and **trigger events for framework compatibility**:

```javascript
(() => {
    // Find the label, then find its associated input
    const label = Array.from(document.querySelectorAll('label'))
        .find(l => l.textContent.includes('LABEL_TEXT'));
    const input = label?.querySelector('input,textarea,select')
        || label?.nextElementSibling
        || document.querySelector('input[placeholder*="PLACEHOLDER_TEXT"]');
    if (!input) return 'input not found';
    input.focus();
    input.value = 'YOUR_VALUE';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    return 'filled';
})()
```

For checkboxes/radios: set `.checked = true`, then dispatch `change`.
For `<select>`: set `.value`, then dispatch `change`.

### Scroll the page

`window.scrollBy()` often fails because the real scroll container is an inner `<div>`, not `window`. Use this instead:

```javascript
(() => {
    // Find the actual scrollable container
    const el = Array.from(document.querySelectorAll('*'))
        .filter(e => e.scrollHeight > e.clientHeight
            && getComputedStyle(e).overflowY !== 'visible'
            && e.scrollHeight - e.clientHeight > 100)
        .sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight))[0];
    if (el) { el.scrollBy(0, 400); return 'scrolled'; }
    // Fallback to window
    window.scrollBy(0, 400);
    return 'scrolled window';
})()
```

---

## When Templates Don't Work

### Step 1: Dispatch Full Event Sequence (React/Vue Required)

Some frameworks (React, Vue) ignore `.click()`. Simulate the real mouse interaction:

```javascript
(() => {
    const text = 'YOUR_TEXT';
    const leaf = Array.from(document.querySelectorAll('*'))
        .find(el => el.children.length === 0 && el.textContent.includes(text));
    if (!leaf) return 'not found';
    const target = leaf.closest('a, button, [role="button"], [onclick], tr, li')
        || leaf.parentElement || leaf;
    ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(type => {
        target.dispatchEvent(new PointerEvent(type, { bubbles: true, cancelable: true }));
    });
    return 'events dispatched: ' + target.tagName;
})()
```

Also try `dblclick` for file explorers, tree views, or items that open on double-click.

### Step 2: Inspect Structure First

When text appears multiple times or element not found, scan the page first:

```javascript
(() => {
    const keyword = 'YOUR_TEXT';
    return Array.from(document.querySelectorAll('*'))
        .filter(el => el.children.length === 0 && el.textContent.includes(keyword))
        .map(el => ({
            tag: el.tagName,
            text: el.textContent.trim().substring(0, 60),
            id: el.id,
            class: el.className?.toString?.().substring(0, 60),
            parentTag: el.parentElement?.tagName,
            parentClass: el.parentElement?.className?.toString?.().substring(0, 60)
        }));
})()
```

### Step 3: Diagnostic Checklist

If still not working, check these in order:

1. **Page still loading?** Check `document.readyState`
2. **Inside an iframe?** Access via `document.querySelector('iframe').contentDocument`
3. **Inside Shadow DOM?** Access via `element.shadowRoot`
4. **Need to scroll first?** Content may be lazy-loaded — scroll down, wait, retry
5. **Text mismatch?** Check for extra whitespace, different casing, or special characters

### Step 4: Alternative - Direct URL Navigation

When UI interaction is complex or unreliable, navigate directly via URL:

```javascript
window.location.href = "https://example.com/target-page";
```

**Common use cases:**
- Region/zone switching (e.g., `.../rdsList/cn-shanghai`)
- Page navigation when menus are complex
- Bypassing multi-step wizards

---

## Other Operations

**Extract data:**
```javascript
({ title: document.title, url: location.href })
```

**Wait for content (requires await_promise):**
```javascript
new Promise(resolve => {
    const check = () => {
        const el = document.querySelector('.loaded');
        if (el) resolve(el.textContent); else setTimeout(check, 100);
    };
    check();
})
```

---

## Common Errors

| Error | Fix |
|-------|-----|
| `Illegal return statement` | Wrap in IIFE: `(() => { return value; })()` |
| `:contains()` is not valid | That's jQuery-only. Use `.textContent.includes()` instead |
| Circular structure to JSON | Return `.textContent` / `.href` / `.value`, not the element itself |

---

## 2. tab

```json
{
  "type": "tab",
  "action": "open",
  "url": "https://example.com",
  "tab_id": 123
}
```

**Actions:** `init` | `open` | `close` | `switch` | `list` | `refresh`
- `init` / `open` require `url`
- `close` / `switch` / `refresh` require `tab_id`

---

## 3. handle_dialog

When JavaScript triggers a dialog (alert, confirm, prompt), the browser pauses execution. OpenBrowser detects dialogs automatically:

- **alert**: Auto-accepted (notification only)
- **confirm**: Requires decision - use `handle_dialog`
- **prompt**: Requires decision and text input - use `handle_dialog`

```json
{
  "type": "handle_dialog",
  "dialog_action": "accept",
  "prompt_text": "optional text for prompt dialogs"
}
```

**Parameters:**
- `dialog_action`: Required - either `"accept"` or `"dismiss"`
- `prompt_text`: Optional - text to enter for prompt dialogs

**Cascading Dialogs:**
After handling one dialog, another may appear (e.g., confirm → alert). OpenBrowser:
1. Returns info about the new dialog
2. Auto-accepts alerts
3. Requires another `handle_dialog` for confirm/prompt

**Example Flow:**
1. Click triggers `confirm('Delete?')`
2. OpenBrowser returns: `dialog_opened: true, dialog: {type: "confirm", message: "Delete?", needsDecision: true}`
3. You respond: `{"type": "handle_dialog", "dialog_action": "accept"}`
4. If alert follows, OpenBrowser auto-accepts and shows result

---

## 4. view

Capture a screenshot to see the current page state.

```json
{
  "type": "view"
}
```

**When to use:**
- After navigation (`tab init` / `tab open`) to verify page loaded correctly
- When UI structure is unknown and you need to "see" the page before interacting
- After multiple operations to verify the final state
- When you encounter unexpected behavior and need visual debugging

**When NOT to use:**
- After every single operation (wasteful)
- When JavaScript can extract the information you need (use `javascript_execute` instead)

**Example workflow:**
```json
{"type": "tab", "action": "init", "url": "https://example.com"}  // Text result only
{"type": "view"}  // Now see the page
{"type": "javascript_execute", "script": "...click..."}  // Text result
{"type": "view"}  // Verify the result
```

---

## Workflow Summary

1. **Navigate** to the page using `tab init` or `tab open` (text result)
2. **View** the page to understand its structure: `{"type": "view"}`
3. **Interact** using `javascript_execute` with the universal templates (text result)
4. **Verify** with another `view` when needed
5. **Escalate** if operations fail (follow the 2-Strike Rule):
   - **1st failure**: Try full event sequence
   - **2nd failure**: Inspect structure, check iframes/Shadow DOM
   - **Still failing**: Consider direct URL navigation

**Efficiency Tip**: Use `view` sparingly. Most operations can be verified with JavaScript result checks or console output."""


class OpenBrowserTool(ToolDefinition[OpenBrowserAction, OpenBrowserObservation]):
    """Tool for browser automation with visual feedback"""
    
    name = "open_browser"
    
    @classmethod
    def create(cls, conv_state, terminal_executor=None) -> Sequence[ToolDefinition]:
        """Create OpenBrowserTool instance with executor"""
        # Create executor with conversation context
        executor = OpenBrowserExecutor()
        
        return [
            cls(
                description=_OPEN_BROWSER_DESCRIPTION,
                action_type=OpenBrowserAction,  # Use base Action type
                observation_type=OpenBrowserObservation,
                executor=executor,
            )
        ]


# Register the tool
register_tool("open_browser", OpenBrowserTool.create)