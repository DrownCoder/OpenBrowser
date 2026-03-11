"""
Base classes for OpenBrowser tool actions and observations.

This module provides the foundation classes that all OpenBrowser tool types
will inherit from, following the OpenHands SDK pattern.
"""

from collections.abc import Sequence
from typing import Any, Dict, List, Optional

from openhands.sdk import Action, ImageContent, Observation, TextContent
from pydantic import Field


class OpenBrowserAction(Action):
    """Base class for all OpenBrowser actions.

    This base class provides common fields needed by all browser automation
    actions, enabling proper type hierarchy and conversation isolation.
    """

    conversation_id: Optional[str] = Field(
        default=None, description="Conversation ID for session isolation"
    )


class OpenBrowserObservation(Observation):
    """Base observation returned by OpenBrowser tools after each action.

    This class contains the common fields shared by all OpenBrowser tool
    observations, providing a consistent interface for success/failure
    reporting, screenshots, and tab information.
    """

    success: bool = Field(description="Whether the operation succeeded")
    screenshot_data_url: Optional[str] = Field(
        default=None,
        description="Screenshot as data URL (base64 encoded PNG, 1280x720 pixels)",
    )
    message: Optional[str] = Field(default=None, description="Result message")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    tabs: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of current tabs"
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
    # Tab creation tracking
    new_tabs_created: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of new tabs created during operation (tabId, url, title, loading)"
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
        """Convert observation to LLM content format with markdown formatting."""
        content_items: list[TextContent | ImageContent] = []
        text_parts: list[str] = []

        # Operation Status Section
        text_parts.append("## Operation Status")
        text_parts.append("")
        if not self.success:
            text_parts.append("**Status**: FAILED")
            if self.error:
                text_parts.append(f"**Error**: {self.error}")
        else:
            text_parts.append("**Status**: SUCCESS")
            if self.message:
                text_parts.append(f"**Action**: {self.message}")

        text_parts.append("")

        # Join text parts and create TextContent
        if text_parts:
            text_content = "\n".join(text_parts)
            content_items.append(TextContent(text=text_content))

        # Add screenshot if available
        if self.screenshot_data_url:
            content_items.append(ImageContent(image_urls=[self.screenshot_data_url]))

        return content_items
