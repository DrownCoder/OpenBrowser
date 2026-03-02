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
    TabCommand, GetTabsCommand, JavascriptExecuteCommand,
    HandleDialogCommand, DialogAction,
    TabAction, ScreenshotCommand,
    HighlightElementsCommand, ClickElementCommand, HoverElementCommand,
    ScrollElementCommand, KeyboardInputCommand,
    GetElementHtmlCommand
)

logger = logging.getLogger(__name__)


class OpenBrowserAction(Action):
    """Browser automation action with visual-first interaction support"""
    
    type: str = Field(
        description="Type of browser operation: 'tab', 'highlight_elements', 'click_element', 'hover_element', 'scroll_element', 'keyboard_input', 'handle_dialog', 'javascript_execute', 'confirm_click_element', 'confirm_hover_element', 'confirm_scroll_element', 'confirm_keyboard_input'"
    )
    
    # Tab operation parameters
    action: Optional[str] = Field(default=None, description="Tab action: init/open/close/switch/list/refresh")
    url: Optional[str] = Field(default=None, description="URL for tab operations")
    tab_id: Optional[int] = Field(default=None, description="Tab ID for operations")
    
    # Visual interaction parameters
    element_type: Optional[str] = Field(default="clickable", description="Single element type: clickable/scrollable/inputable/hoverable")
    element_id: Optional[str] = Field(default=None, description="Element ID from highlight response")
    page: Optional[int] = Field(default=1, ge=1, description="Page number for pagination (1-indexed)")
    # Scroll parameters
    direction: Optional[str] = Field(default="down", description="Scroll direction: up/down/left/right")
    
    # Keyboard input parameters
    text: Optional[str] = Field(default=None, description="Text to input")
    
    # Dialog handling
    dialog_action: Optional[str] = Field(default=None, description="Dialog action: accept/dismiss")
    prompt_text: Optional[str] = Field(default=None, description="Text for prompt dialogs")

    # JavaScript execution (fallback)
    script: Optional[str] = Field(default=None, description="JavaScript code (fallback)")

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
    # Visual interaction results
    highlighted_elements: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of elements highlighted on the screenshot"
    )
    total_elements: Optional[int] = Field(
        default=None,
        description="Total number of elements found"
    )
    element_id: Optional[str] = Field(
        default=None,
        description="ID of the element that was acted upon"
    )
    # 2PC Confirmation fields
    pending_confirmation: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Pending confirmation information for 2PC flow"
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
        
        # Highlighted Elements Section (if applicable)
        if self.highlighted_elements:
            text_parts.append("## Highlighted Elements")
            text_parts.append("")
            text_parts.append(f"**Total Elements**: {self.total_elements if self.total_elements is not None else len(self.highlighted_elements)}")
            text_parts.append("")
            # Format: id: <html> for each element
            element_descriptions = []
            for el in self.highlighted_elements:
                el_id = el.get('id', 'unknown')
                html = (el.get('html') or '').strip()
                if len(html) > 200:
                    html = html[:190] + '...(Truncated)'
                if html:
                    element_descriptions.append(f"{el_id}: {html}")
                else:
                    tag = el.get('tagName', '').upper()
                    element_descriptions.append(f"{el_id} ({tag})")
            text_parts.append('\n'.join(element_descriptions))
            text_parts.append("")
        
        # Pending Confirmation Section (2PC)
        if self.pending_confirmation:
            text_parts.append("## ⚠️ Action Pending Confirmation")
            text_parts.append("")
            text_parts.append("**IMPORTANT**: This action requires confirmation before execution.")
            text_parts.append("")
            text_parts.append(f"**Element ID**: {self.pending_confirmation.get('element_id', 'unknown')}")
            text_parts.append(f"**Action Type**: {self.pending_confirmation.get('action_type', 'unknown')}")
            text_parts.append("")
            text_parts.append("**Full HTML**:")
            text_parts.append("```html")
            full_html = self.pending_confirmation.get('full_html', '<not available>')
            # Truncate if too long
            if len(full_html) > 5000:
                full_html = full_html[:5000] + "\n... (truncated)"
            text_parts.append(full_html)
            text_parts.append("```")
            text_parts.append("")
            text_parts.append("**To confirm this action, use:**")
            action_type = self.pending_confirmation.get('action_type', '')
            element_id = self.pending_confirmation.get('element_id', '')
            confirm_cmd = f'{{"type": "confirm_{action_type}_element", "element_id": "{element_id}"}}'
            text_parts.append(f"```json\n{confirm_cmd}\n```")
            text_parts.append("")
            text_parts.append("**Or choose a different action to cancel this pending confirmation.**")
            text_parts.append("")
        
        if self.element_id:
            text_parts.append("## Element Action Result")
            text_parts.append("")
            text_parts.append(f"**Element ID**: {self.element_id}")
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
        # 2PC state: pending confirmations per conversation
        self.pending_confirmations: Dict[str, Dict[str, Any]] = {}
    
    async def _execute_command(self, command) -> Any:
        """Execute command with conversation context"""
        logger.debug(f"DEBUG: _execute_command called with action_type={command.type}, conversation_id={self.conversation_id}")
        
        # Set conversation_id for multi-session support
        if hasattr(command, 'conversation_id'):
            command.conversation_id = self.conversation_id
        
        result = await command_processor.execute(command)
        logger.debug(f"DEBUG: _execute_command result: success={result.success if result else 'None'}")
        return result
    
    def _get_element_full_html(self, element_id: str) -> str:
        """Get the full HTML of an element from extension's elementCache.
        
        This uses the cached HTML from highlight_elements instead of querying the DOM.
        The cached HTML is the original HTML captured at highlight time.
        """
        # Use GetElementHtmlCommand to get HTML from extension's elementCache
        command = GetElementHtmlCommand(
            element_id=element_id,
            conversation_id=self.conversation_id
        )
        result_dict = self._execute_command_sync(command)
        
        if result_dict and result_dict.get('success'):
            data = result_dict.get('data', {})
            html = data.get('html') if isinstance(data, dict) else None
            if html and isinstance(html, str):
                # Truncate to 10000 characters
                return html[:10000] + ('...' if len(html) > 10000 else '')
        else:
            logger.warning(f"Unexpected GetElementHtmlCommand response: {result_dict}")
        
        # Element not found in cache - return error message
        logger.warning(f"Element {element_id} not found in cache for conversation {self.conversation_id}")
        return "<element not found in cache>"

    
    def _clear_pending_confirmation(self):
        """Clear pending confirmation for current conversation"""
        if self.conversation_id in self.pending_confirmations:
            del self.pending_confirmations[self.conversation_id]
    
    def _set_pending_confirmation(self, element_id: str, action_type: str, full_html: str, extra_data: Dict[str, Any] = None):
        """Set pending confirmation for current conversation"""
        self.pending_confirmations[self.conversation_id] = {
            'element_id': element_id,
            'action_type': action_type,
            'full_html': full_html,
            'extra_data': extra_data or {}
        }
    
    def _get_pending_confirmation(self) -> Optional[Dict[str, Any]]:
        """Get pending confirmation for current conversation"""
        return self.pending_confirmations.get(self.conversation_id)
    
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

            elif action_type == "highlight_elements":
                # Single element type for stable collision-aware pagination
                element_type = action.element_type or "clickable"
                page = action.page or 1
                command = HighlightElementsCommand(
                    element_type=element_type,
                    page=page,
                    conversation_id=self.conversation_id
                )
                result_dict = self._execute_command_sync(command)
                
                # Check if command succeeded before accessing result data
                if result_dict is None:
                    raise RuntimeError("Chrome extension did not respond to highlight_elements command")
                if not result_dict.get('success', False):
                    ext_error = result_dict.get('error', 'Unknown error from Chrome extension')
                    raise RuntimeError(f"Chrome extension failed to highlight elements: {ext_error}")
                
                elements = result_dict.get('data', {}).get('elements', [])
                total_elements = result_dict.get('data', {}).get('totalElements', 0)
                total_pages = result_dict.get('data', {}).get('totalPages', 1)
                current_page = result_dict.get('data', {}).get('page', 1)
                message = f"Found {len(elements)} {element_type} elements on page {current_page}/{total_pages} (total: {total_elements})"
            # ========== 2PC Confirm Operations ==========
            elif action_type == "confirm_click_element":
                pending = self._get_pending_confirmation()
                if not pending or pending['action_type'] != 'click':
                    raise ValueError("No pending click confirmation found. Please call click_element first.")
                if pending['element_id'] != action.element_id:
                    raise ValueError(f"Element ID mismatch. Expected {pending['element_id']}, got {action.element_id}")
                # Execute actual click
                command = ClickElementCommand(
                    element_id=action.element_id,
                    conversation_id=self.conversation_id,
                    tab_id=action.tab_id
                )
                result_dict = self._execute_command_sync(command)
                if not result_dict or not result_dict.get('success'):
                    ext_error = result_dict.get('error', 'Unknown error') if result_dict else 'No response'
                    raise RuntimeError(f"Failed to click element: {ext_error}")
                message = f"Confirmed and clicked element: {action.element_id}"
                self._clear_pending_confirmation()
                
            elif action_type == "confirm_hover_element":
                pending = self._get_pending_confirmation()
                if not pending or pending['action_type'] != 'hover':
                    raise ValueError("No pending hover confirmation found. Please call hover_element first.")
                if pending['element_id'] != action.element_id:
                    raise ValueError(f"Element ID mismatch. Expected {pending['element_id']}, got {action.element_id}")
                command = HoverElementCommand(
                    element_id=action.element_id,
                    conversation_id=self.conversation_id,
                    tab_id=action.tab_id
                )
                result_dict = self._execute_command_sync(command)
                if not result_dict or not result_dict.get('success'):
                    ext_error = result_dict.get('error', 'Unknown error') if result_dict else 'No response'
                    raise RuntimeError(f"Failed to hover element: {ext_error}")
                message = f"Confirmed and hovered element: {action.element_id}"
                self._clear_pending_confirmation()
                
            elif action_type == "confirm_scroll_element":
                pending = self._get_pending_confirmation()
                if not pending or pending['action_type'] != 'scroll':
                    raise ValueError("No pending scroll confirmation found. Please call scroll_element first.")
                if pending['element_id'] != action.element_id:
                    raise ValueError(f"Element ID mismatch. Expected {pending['element_id']}, got {action.element_id}")
                command = ScrollElementCommand(
                    element_id=action.element_id,
                    direction=pending['extra_data'].get('direction', 'down'),
                    conversation_id=self.conversation_id,
                    tab_id=action.tab_id
                )
                result_dict = self._execute_command_sync(command)
                if not result_dict or not result_dict.get('success'):
                    ext_error = result_dict.get('error', 'Unknown error') if result_dict else 'No response'
                    raise RuntimeError(f"Failed to scroll element: {ext_error}")
                message = f"Confirmed and scrolled element: {action.element_id}"
                self._clear_pending_confirmation()
                
            elif action_type == "confirm_keyboard_input":
                pending = self._get_pending_confirmation()
                if not pending or pending['action_type'] != 'keyboard_input':
                    raise ValueError("No pending keyboard_input confirmation found. Please call keyboard_input first.")
                if pending['element_id'] != action.element_id:
                    raise ValueError(f"Element ID mismatch. Expected {pending['element_id']}, got {action.element_id}")
                command = KeyboardInputCommand(
                    element_id=action.element_id,
                    text=pending['extra_data'].get('text', ''),
                    conversation_id=self.conversation_id,
                    tab_id=action.tab_id
                )
                result_dict = self._execute_command_sync(command)
                if not result_dict or not result_dict.get('success'):
                    ext_error = result_dict.get('error', 'Unknown error') if result_dict else 'No response'
                    raise RuntimeError(f"Failed to input text: {ext_error}")
                message = f"Confirmed and input text to element: {action.element_id}"
                self._clear_pending_confirmation()
            
            # ========== 2PC Phase 1: Actions Requiring Confirmation ==========
            elif action_type == "click_element":
                if not action.element_id:
                    raise ValueError("click_element requires element_id parameter")
                # Get full HTML for confirmation
                full_html = self._get_element_full_html(action.element_id)
                # Store pending confirmation
                self._set_pending_confirmation(
                    element_id=action.element_id,
                    action_type='click',
                    full_html=full_html,
                    extra_data={'tab_id': action.tab_id}
                )
                # Return pending confirmation (no actual execution yet)
                result_dict = {'success': True, 'data': {}}
                message = f"Click action pending confirmation for element: {action.element_id}"
                
            elif action_type == "hover_element":
                if not action.element_id:
                    raise ValueError("hover_element requires element_id parameter")
                full_html = self._get_element_full_html(action.element_id)
                self._set_pending_confirmation(
                    element_id=action.element_id,
                    action_type='hover',
                    full_html=full_html,
                    extra_data={'tab_id': action.tab_id}
                )
                result_dict = {'success': True, 'data': {}}
                message = f"Hover action pending confirmation for element: {action.element_id}"
                
            elif action_type == "scroll_element":
                full_html = self._get_element_full_html(action.element_id) if action.element_id else "<page scroll>"
                self._set_pending_confirmation(
                    element_id=action.element_id or '',
                    action_type='scroll',
                    full_html=full_html,
                    extra_data={'direction': action.direction or 'down', 'tab_id': action.tab_id}
                )
                result_dict = {'success': True, 'data': {}}
                message = f"Scroll action pending confirmation for element: {action.element_id or 'page'}"
                
            elif action_type == "keyboard_input":
                if not action.element_id:
                    raise ValueError("keyboard_input requires element_id parameter")
                if not action.text:
                    raise ValueError("keyboard_input requires text parameter")
                full_html = self._get_element_full_html(action.element_id)
                self._set_pending_confirmation(
                    element_id=action.element_id,
                    action_type='keyboard_input',
                    full_html=full_html,
                    extra_data={'text': action.text, 'tab_id': action.tab_id}
                )
                result_dict = {'success': True, 'data': {}}
                message = f"Keyboard input action pending confirmation for element: {action.element_id}"
            else:
                raise ValueError(f"Unknown action type: {action_type}")
            
            # ========== Clear pending confirmation for non-confirm operations ==========
            # If action is not a confirm action and not a 2PC action, clear pending state
            if not action_type.startswith('confirm_') and action_type not in ['click_element', 'hover_element', 'scroll_element', 'keyboard_input']:
                self._clear_pending_confirmation()
            
            # Determine what data to collect based on action type
            tabs_data = []
            mouse_position = None
            screenshot_data_url = None
            

            # Collect tabs data only for tab operations
            if action_type == "tab":
                logger.debug(f"DEBUG: Getting tabs after tab action (sync)...")
                tabs_result = self._get_tabs_sync()
                logger.debug(f"DEBUG: tabs_result: success={tabs_result.get('success')}, data keys={list(tabs_result.get('data', {}).keys()) if tabs_result.get('data') else 'None'}")
                
                if tabs_result.get('success') and tabs_result.get('data') and 'tabs' in tabs_result['data']:
                    tabs_data = tabs_result['data']['tabs']

                # Capture screenshot after tab operations (except list)
                if action_str != "list":
                    try:
                        screenshot_cmd = ScreenshotCommand(
                            conversation_id=self.conversation_id
                        )
                        screenshot_result = self._execute_command_sync(screenshot_cmd)
                        if screenshot_result and screenshot_result.get('success'):
                            screenshot_data_url = screenshot_result.get('data', {}).get('screenshot')
                            logger.debug(f"DEBUG: Captured screenshot after tab '{action_str}', length={len(screenshot_data_url) if screenshot_data_url else 0}")
                    except Exception as e:
                        logger.warning(f"Failed to capture screenshot after tab action: {e}")
            
            # Capture screenshot after javascript_execute (if no dialog opened)
            if action_type == "javascript_execute" and result_dict:
                if not result_dict.get('dialog_opened', False):
                    try:
                        screenshot_cmd = ScreenshotCommand(
                            conversation_id=self.conversation_id
                        )
                        screenshot_result = self._execute_command_sync(screenshot_cmd)
                        if screenshot_result and screenshot_result.get('success'):
                            screenshot_data_url = screenshot_result.get('data', {}).get('screenshot')
                            logger.debug(f"DEBUG: Captured screenshot after javascript_execute, length={len(screenshot_data_url) if screenshot_data_url else 0}")
                    except Exception as e:
                        logger.warning(f"Failed to capture screenshot after javascript_execute: {e}")

            # Extract success and dialog info from result_dict
            success = True  # Default to True
            error = None
            dialog_opened = None
            dialog = None
            highlighted_elements = None
            total_elements = None
            
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
                
                if 'data' in result_dict and isinstance(result_dict['data'], dict):
                    # Extract screenshot from visual interaction commands
                    # highlight_elements returns data.screenshot (highlighted image)
                    # click/hover/scroll/keyboard_input return data.screenshot
                    if 'screenshot' in result_dict['data']:
                        screenshot_data_url = result_dict['data']['screenshot']
                        logger.debug(f"DEBUG: Extracted screenshot from result_dict['data']['screenshot'], length={len(screenshot_data_url) if screenshot_data_url else 0}")
                    
                    # Extract highlighted elements for highlight_elements action
                    if 'elements' in result_dict['data']:
                        highlighted_elements = result_dict['data']['elements']
                    if 'totalElements' in result_dict['data']:
                        total_elements = result_dict['data']['totalElements']
            # Get pending confirmation if exists
            pending_confirmation = self._get_pending_confirmation()
            
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
                dialog=dialog,
                highlighted_elements=highlighted_elements,
                total_elements=total_elements,
                pending_confirmation=pending_confirmation
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
                dialog=None,
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

        logger.debug(f"DEBUG: OpenBrowserTool.__call__ called with action: {action.type}, conversation_id: {self.conversation_id}")
        logger.debug(f"DEBUG: Current thread: {threading.current_thread().name}")
        
        try:
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



# --- Tool Definition ---

_OPEN_BROWSER_DESCRIPTION = """Browser automation with visual-first interaction.

## Core Philosophy

You SEE the page through screenshots. You IDENTIFY targets through visual element IDs. You OPERATE using those IDs.

JavaScript is a fallback, not your primary tool.

---

## Visual + Semantic Dual Recognition Strategy

**CRITICAL**: You must use BOTH visual cues AND HTML semantic information to precisely identify your target element.

### Two-Step Verification Process

```
1. VISUAL: Look at the screenshot - find blue boxes with element IDs
2. SEMANTIC: Read the HTML code - confirm this is the RIGHT element
3. DECISION: If HTML semantics don't match your intent, continue to next page
```

### How to Read Element Information

Each highlighted element shows:
```
Element ID: <html code>
```

**Example:**
```
abc123: <button class="btn-primary" type="submit">Submit</button>
def456: <a href="/cancel" class="link">Cancel</a>
```

### What to Check in HTML

Read the HTML code to understand what this element does:

**Key Information:**
- **Tag name**: What type of element is this?
- **Attributes**: class, type, href, aria-label, data-* etc.
- **Text content**: What text does it display?
- **Context**: Where is it located in the DOM?

**Logic:** The HTML should match your intent. If you want a "Submit" button, look for elements with submit-related semantics (class="submit", type="submit", text="Submit", etc.).

### Decision Rules

**Click the element IF:**
- Visual position matches your intent (e.g., "top right corner")
- HTML semantics match your goal (e.g., class="submit", type="submit")
- Text content matches what you're looking for

**Continue to next page IF:**
- No elements on current page match your semantic criteria
- HTML attributes don't align with your intent
- You're unsure which element is correct
- Multiple similar elements exist and you need more context

**ALWAYS paginate when uncertain - never guess.**

---

## Visual-First Workflow

```
1. highlight_elements - Capture screenshot with visual markers + HTML info
2. Analyze BOTH visual positions AND HTML semantics
3. Identify target by element_id that matches BOTH criteria
4. If no perfect match found, continue to next page (page=2, 3, ...)
5. Use click_element, hover_element, scroll_element, keyboard_input
6. Take screenshot to verify the result
7. If dialog appears, use handle_dialog
8. javascript_execute only as fallback for complex operations
```

### Example Flow

**Scenario**: You need to click the "Submit" button

1. `highlight_elements()` → You see:
   - abc123: <button class="cancel">Cancel</button>
   - def456: <button class="submit-btn" type="submit">Submit</button>
   - ghi789: <a href="/help">Need help?</a>

2. **Visual Check**: Locate blue boxes on screenshot

3. **Semantic Check**:
   - abc123: Has class="cancel" → WRONG element
   - def456: Has class="submit-btn", type="submit", text="Submit" → CORRECT!
   - ghi789: It's a link, not a button → WRONG element

4. **Decision**: `click_element(element_id="def456")`

5. Verify with screenshot

---

---

## Element ID Format

Element IDs are unique 6-character hexadecimal hashes (e.g., `a3f2b1`, `c8e4d2`).

Each element is assigned a stable hash based on its DOM position and attributes.
This hash remains consistent across `highlight_elements` calls for the same page state.

**Note**: All element operations require `tab_id` to specify which tab to operate on.
The active tab ID is shown in the Browser State section of the observation.

---

## Command Reference

### highlight_elements

Capture a screenshot with numbered visual markers on interactive elements of ONE type.

**Important**: Each call highlights only ONE element type at a time.

```json
{ "type": "highlight_elements" }                           // Default: clickable elements, page 1
{ "type": "highlight_elements", "element_type": "inputable" }  // Input fields
{ "type": "highlight_elements", "element_type": "scrollable" } // Scrollable areas
{ "type": "highlight_elements", "element_type": "hoverable" }  // Hoverable elements
{ "type": "highlight_elements", "page": 2 }                 // Next page of clickable elements
```

Parameters:
- `element_type`: Single type to highlight - "clickable" (default), "scrollable", "inputable", or "hoverable"
- `page`: Page number for pagination (1-indexed, default 1)

**When to Use Pagination**:
- If the element you want to interact with is NOT visible on the current page, increment `page` to see more elements
- Continue to the next page until you find the most appropriate element for your task
- Stay on the same `element_type` across pages to browse through all elements of that category
### click_element

Click an element by its visual ID.

```json
{ "type": "click_element", "element_id": "c8e4d2", "tab_id": 123 }
```

Use this for buttons, links, and any clickable element you identified from highlight_elements.

### hover_element

Hover over an element by its visual ID.

```json
{ "type": "hover_element", "element_id": "a3f2b1", "tab_id": 123 }
```

Use this to reveal tooltips, dropdown menus, or hover states.

### scroll_element

Scroll within an element by its visual ID, or scroll the entire page if no element_id is provided.

```json
{ "type": "scroll_element", "element_id": "d2f4a8", "direction": "down", "tab_id": 123 }
{ "type": "scroll_element", "element_id": "d2f4a8", "direction": "up", "tab_id": 123 }
{ "type": "scroll_element", "direction": "down", "tab_id": 123 }  // Scroll entire page
```

Parameters:
- `element_id`: (optional) Element ID from highlight response. If not provided, scrolls the entire page.
- `direction`: "up", "down", "left", or "right" (default: "down")

Use this to:
- Scroll within specific containers (when element_id is provided)
- Scroll the entire page (when element_id is omitted)
### keyboard_input

Type text into an input element by its visual ID.

```json
{ "type": "keyboard_input", "element_id": "b7c9e5", "text": "hello@example.com", "tab_id": 123 }
```

Use this for text inputs, textareas, and search boxes.

### tab

Manage browser tabs.

```json
{ "type": "tab", "action": "init", "url": "https://example.com" }
{ "type": "tab", "action": "open", "url": "https://example.com" }
{ "type": "tab", "action": "close", "tab_id": 123 }
{ "type": "tab", "action": "switch", "tab_id": 123 }
{ "type": "tab", "action": "list" }
```

- `init`: Create new session with isolated tab group
- `open`: Open URL in new tab
- `close`: Close specific tab
- `switch`: Switch to specific tab
- `list`: List all tabs

### handle_dialog

Handle browser dialogs (alert, confirm, prompt).

```json
{ "type": "handle_dialog", "dialog_action": "accept" }
{ "type": "handle_dialog", "dialog_action": "dismiss" }
{ "type": "handle_dialog", "dialog_action": "accept", "prompt_text": "my response" }
```

Dialog types:
- `alert`: Auto-accepted, no action needed
- `confirm`: Use accept or dismiss
- `prompt`: Use accept with prompt_text, or dismiss

### javascript_execute (Fallback)

Execute arbitrary JavaScript. Use only when visual commands cannot accomplish your goal.

```json
{ "type": "javascript_execute", "script": "(() => { return document.title; })()" }
```

Guidelines:
- 30-second timeout
- Return JSON-serializable values only (no DOM nodes)
- Use IIFE `(() => { ... })()` for return statements
- `console.log()` output is captured

---

## Workflow Summary

1. **Navigate**: `tab init` or `tab open`
2. **Highlight**: `highlight_elements` to get visual markers + HTML info
3. **Verify Dual Match**: 
   - Visually locate blue box on screenshot
   - Semantically verify HTML attributes (class, text, type)
   - If no perfect match, increment `page` and continue searching
4. **Act**: Use `click_element`, `keyboard_input`, `hover_element`, `scroll_element`
5. **Verify**: Take screenshot to confirm
6. **Handle**: If dialog opens, use `handle_dialog`
7. **Fallback**: Use `javascript_execute` only for complex operations

---

## Important Notes

- **Dual verification required**: Match BOTH visual position AND HTML semantics before acting
- **Always paginate if uncertain**: If the current page doesn't have the right element, use `page=2, 3, ...` to see more
- **HTML semantic hints**: Check `class`, `type`, `href`, `aria-label`, and text content
- **Always verify with screenshot** after significant operations
- **Hover before click** if you need to reveal hidden elements (menus, tooltips)
- **JavaScript is fallback** - try visual commands first

---

## Troubleshooting

| Issue | Solution |
|---|----------|
| Element not found | Refresh with highlight_elements, check element_id |
| Click has no effect | Try hover_element first to reveal |
| Complex interaction | Use javascript_execute as fallback |
| Page still loading | Wait and retry highlight_elements |

**2-Strike Rule**: If visual command fails twice, switch to javascript_execute fallback.
"""




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