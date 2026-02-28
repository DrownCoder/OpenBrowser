from enum import Enum
from typing import Optional, List, Tuple, Literal, Union
from pydantic import BaseModel, Field, validator
import re


class MouseButton(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class ScrollDirection(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class TabAction(str, Enum):
    OPEN = "open"
    CLOSE = "close"
    LIST = "list"
    SWITCH = "switch"
    INIT = "init"
    REFRESH = "refresh"


class BaseCommand(BaseModel):
    """Base command model with common fields"""
    command_id: Optional[str] = Field(
        default=None,
        description="Optional unique identifier for tracking command execution"
    )
    timestamp: Optional[float] = Field(
        default=None,
        description="Timestamp when command was created (epoch seconds)"
    )
    tab_id: Optional[int] = Field(
        default=None,
        description="Tab ID to target (None = current managed tab)"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Conversation ID for session isolation (None = default session)"
    )


class MouseMoveCommand(BaseCommand):
    """Move mouse to absolute position in preset coordinate system"""
    type: Literal["mouse_move"] = "mouse_move"
    x: int = Field(
        description="X coordinate in preset coordinate system (0 to 1280, left to right)",
        ge=0,
        le=1280
    )
    y: int = Field(
        description="Y coordinate in preset coordinate system (0 to 720, top to bottom)",
        ge=0,
        le=720
    )
    duration: Optional[float] = Field(
        default=0.1,
        description="Duration of movement in seconds (for animation)",
        gt=0,
        le=5.0
    )


class MouseClickCommand(BaseCommand):
    """Click at current mouse position"""
    type: Literal["mouse_click"] = "mouse_click"
    button: MouseButton = Field(default=MouseButton.LEFT)
    double: bool = Field(default=False, description="Double click if True")
    count: int = Field(default=1, ge=1, le=3, description="Number of clicks (1-3)")


class MouseScrollCommand(BaseCommand):
    """Scroll at current mouse position"""
    type: Literal["mouse_scroll"] = "mouse_scroll"
    direction: ScrollDirection = Field(default=ScrollDirection.DOWN)
    amount: int = Field(default=100, ge=1, le=1000, description="Scroll amount in pixels")


class ResetMouseCommand(BaseCommand):
    """Reset mouse position to screen center"""
    type: Literal["reset_mouse"] = "reset_mouse"


class KeyboardTypeCommand(BaseCommand):
    """Type text at current focus"""
    type: Literal["keyboard_type"] = "keyboard_type"
    text: str = Field(description="Text to type", max_length=1000)
    
    @validator('text')
    def validate_text(cls, v):
        # Remove control characters except newline, tab
        v = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', v)
        return v


class KeyboardPressCommand(BaseCommand):
    """Press special key"""
    type: Literal["keyboard_press"] = "keyboard_press"
    key: str = Field(
        description="Key to press (e.g., 'Enter', 'Escape', 'Tab', 'Backspace')",
        max_length=50
    )
    modifiers: List[str] = Field(
        default_factory=list,
        description="Modifier keys (e.g., ['Control', 'Shift'])"
    )


class ScreenshotCommand(BaseCommand):
    """Capture screenshot"""
    type: Literal["screenshot"] = "screenshot"
    include_cursor: bool = Field(
        default=True,
        description="Whether to include mouse cursor in screenshot"
    )
    include_visual_mouse: bool = Field(
        default=True,
        description="Whether to include visual mouse pointer in screenshot"
    )
    quality: int = Field(
        default=90,  # 保持与扩展一致，PNG忽略此参数，JPEG使用
        ge=1,
        le=100,
        description="JPEG quality (1-100), PNG format ignores this parameter"
    )


class TabCommand(BaseCommand):
    """Tab management command"""
    type: Literal["tab"] = "tab"
    action: TabAction
    url: Optional[str] = Field(
        default=None,
        description="URL for open action, tab ID for close/switch"
    )
    
    @validator('url')
    def validate_url(cls, v, values):
        action = values.get('action')
        if action in [TabAction.OPEN, TabAction.INIT]:
            if not v:
                raise ValueError(f"URL is required for {action} action")
            # Ensure URL has protocol
            if not re.match(r'^https?://', v):
                v = f'https://{v}'
        return v


class GetTabsCommand(BaseCommand):
    """Get list of all tabs"""
    type: Literal["get_tabs"] = "get_tabs"
    managed_only: bool = Field(
        default=True,
        description="If true, only return managed tabs (in OpenBrowser tab group)"
    )


class JavascriptExecuteCommand(BaseCommand):
    """Execute JavaScript code in browser tab"""
    type: Literal["javascript_execute"] = "javascript_execute"
    script: str = Field(
        description="JavaScript code to execute"
    )
    return_by_value: bool = Field(
        default=True,
        description="If true, returns result as serializable JSON value"
    )
    await_promise: bool = Field(
        default=False,
        description="If true, waits for Promise resolution"
    )
    timeout: int = Field(
        default=30000,
        ge=100,
        le=120000,
        description="Execution timeout in milliseconds (100-120000)"
    )


class DialogAction(str, Enum):
    """Dialog handling action"""
    ACCEPT = "accept"
    DISMISS = "dismiss"


class HandleDialogCommand(BaseCommand):
    """Handle an open JavaScript dialog (confirm/prompt)"""
    type: Literal["handle_dialog"] = "handle_dialog"
    action: DialogAction = Field(
        description="Action to take: 'accept' or 'dismiss'"
    )
    prompt_text: Optional[str] = Field(
        default=None,
        description="Text to enter for prompt dialogs"
    )


class GetGroundedElementsCommand(BaseCommand):
    """Extract interactive elements with selectors and bounding boxes for visual grounding"""
    type: Literal["get_grounded_elements"] = "get_grounded_elements"
    max_elements: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum number of elements to return (1-500, default 100)"
    )
    include_hidden: bool = Field(
        default=False,
        description="If true, include hidden/disabled elements (default false)"
    )


class GetAccessibilityTreeCommand(BaseCommand):
    """Get accessibility tree from the page for AI agent context"""
    type: Literal["get_accessibility_tree"] = "get_accessibility_tree"
    max_elements: Optional[int] = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum number of elements to return (1-500, default 50)"
    )


class HighlightElementsCommand(BaseCommand):
    """Highlight interactive elements on the page for visual selection"""
    type: Literal["highlight_elements"] = "highlight_elements"
    element_types: Optional[List[str]] = Field(
        default=["clickable"],
        description="Types of elements to highlight (e.g., 'clickable', 'input', 'link')"
    )
    limit: Optional[int] = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of elements to highlight (1-100)"
    )
    offset: Optional[int] = Field(
        default=0,
        ge=0,
        description="Offset for pagination (0-based)"
    )


class ClickElementCommand(BaseCommand):
    """Click a highlighted element by its ID"""
    type: Literal["click_element"] = "click_element"
    element_id: str = Field(
        description="Element ID from highlight response"
    )


class HoverElementCommand(BaseCommand):
    """Hover over a highlighted element by its ID"""
    type: Literal["hover_element"] = "hover_element"
    element_id: str = Field(
        description="Element ID from highlight response"
    )


class ScrollElementCommand(BaseCommand):
    """Scroll a highlighted element in a direction"""
    type: Literal["scroll_element"] = "scroll_element"
    element_id: str = Field(
        description="Element ID from highlight response"
    )
    direction: str = Field(
        default="down",
        description="Scroll direction: 'up', 'down', 'left', 'right'"
    )


class KeyboardInputCommand(BaseCommand):
    """Type text into a highlighted element by its ID"""
    type: Literal["keyboard_input"] = "keyboard_input"
    element_id: str = Field(
        description="Element ID from highlight response"
    )
    text: str = Field(
        description="Text to input into the element"
    )

class CommandResponse(BaseModel):
    """Response from command execution"""
    success: bool
    command_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[dict] = None
    timestamp: float = Field(default_factory=lambda: time.time())


class ScreenshotResponse(CommandResponse):
    """Response for screenshot command"""
    data: Optional[dict] = Field(
        default=None,
        description="Screenshot data including image base64"
    )


class TabsResponse(CommandResponse):
    """Response for get tabs command"""
    data: Optional[dict] = Field(
        default=None,
        description="Tab list data"
    )


# Union type for all possible commands
Command = Union[
    MouseMoveCommand,
    MouseClickCommand,
    MouseScrollCommand,
    ResetMouseCommand,
    KeyboardTypeCommand,
    KeyboardPressCommand,
    ScreenshotCommand,
    TabCommand,
    GetTabsCommand,
    JavascriptExecuteCommand,
    HandleDialogCommand,
    GetGroundedElementsCommand,
    GetAccessibilityTreeCommand,
    HighlightElementsCommand,
    ClickElementCommand,
    HoverElementCommand,
    ScrollElementCommand,
    KeyboardInputCommand,
]


# Helper function to parse command from dict
def parse_command(data: dict) -> Command:
    """Parse command from dictionary based on type field"""
    cmd_type = data.get('type')
    if not cmd_type:
        raise ValueError("Command must have 'type' field")
    
    command_map = {
        "mouse_move": MouseMoveCommand,
        "mouse_click": MouseClickCommand,
        "mouse_scroll": MouseScrollCommand,
        "reset_mouse": ResetMouseCommand,
        "keyboard_type": KeyboardTypeCommand,
        "keyboard_press": KeyboardPressCommand,
        "screenshot": ScreenshotCommand,
        "tab": TabCommand,
        "get_tabs": GetTabsCommand,
        "javascript_execute": JavascriptExecuteCommand,
        "handle_dialog": HandleDialogCommand,
        "get_grounded_elements": GetGroundedElementsCommand,
        "get_accessibility_tree": GetAccessibilityTreeCommand,
        "highlight_elements": HighlightElementsCommand,
        "click_element": ClickElementCommand,
        "hover_element": HoverElementCommand,
        "scroll_element": ScrollElementCommand,
        "keyboard_input": KeyboardInputCommand,
    }
    
    if cmd_type not in command_map:
        raise ValueError(f"Unknown command type: {cmd_type}")
    
    return command_map[cmd_type](**data)


import time  # Import at end to avoid circular import in default_factory