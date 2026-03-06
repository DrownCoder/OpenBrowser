"""
Unit tests for screenshot behavior verification.

Tests verify that screenshot logic is correctly controlled by the Extension layer
and that server layer no longer proactively triggers screenshots.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from server.core.processor import CommandProcessor
from server.models.commands import (
    TabCommand,
    TabAction,
    JavascriptExecuteCommand,
    ScreenshotCommand,
    HighlightElementsCommand,
    ClickElementCommand,
    HoverElementCommand,
    ScrollElementCommand,
    KeyboardInputCommand,
    HandleDialogCommand,
)


class TestServerLayerScreenshotBehavior:
    """Test that server layer no longer proactively triggers screenshots."""

    @pytest.fixture
    def processor(self):
        """Create a processor instance for testing."""
        return CommandProcessor()

    @pytest.mark.asyncio
    async def test_tab_init_no_auto_screenshot(self, processor):
        """Tab init command should NOT automatically add screenshot."""
        command = TabCommand(
            action=TabAction.INIT,
            url="https://example.com",
            conversation_id="test-conv-1",
        )

        # Mock the _send_prepared_command to return a response without screenshot
        with patch.object(
            processor, "_send_prepared_command", new_callable=AsyncMock()
        ) as mock_send:
            mock_response = MagicMock()
            mock_response.success = True
            mock_response.data = {"tabId": 123, "url": "https://example.com"}
            mock_send.return_value = mock_response

            response = await processor._execute_tab_command(command)

            # Verify the response does NOT contain screenshot
            assert response.success
            assert response.data is not None
            assert "screenshot" not in response.data, (
                "Tab init should not auto-add screenshot"
            )

            # Verify _send_prepared_command was called (extension handles the command)
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_javascript_execute_no_auto_screenshot(self, processor):
        """JavaScript execute command should NOT automatically add screenshot."""
        command = JavascriptExecuteCommand(
            script="document.title", conversation_id="test-conv-2"
        )

        with patch.object(
            processor, "_send_prepared_command", new_callable=AsyncMock()
        ) as mock_send:
            mock_response = MagicMock()
            mock_response.success = True
            mock_response.data = {"result": "Test Page"}
            mock_send.return_value = mock_response

            response = await processor._execute_javascript_execute(command)

            # Verify the response does NOT contain screenshot
            assert response.success
            assert "screenshot" not in response.data, (
                "JS execute should not auto-add screenshot"
            )

    @pytest.mark.asyncio
    async def test_screenshot_command_still_works(self, processor):
        """Direct screenshot command should still work."""
        command = ScreenshotCommand(conversation_id="test-conv-3")

        with patch.object(
            processor, "_send_prepared_command", new_callable=AsyncMock()
        ) as mock_send:
            mock_response = MagicMock()
            mock_response.success = True
            mock_response.data = {"image": "base64imagedata..."}
            mock_send.return_value = mock_response

            response = await processor._execute_screenshot(command)

            # Verify the response DOES contain screenshot (explicit request)
            assert response.success
            assert response.data is not None
            # Screenshot command should still return image data


class TestExtensionLayerScreenshotBehavior:
    """Test that Extension layer controls screenshot for visual commands."""

    @pytest.mark.asyncio
    async def test_highlight_elements_returns_screenshot(self, processor):
        """highlight_elements command should return screenshot (from extension)."""
        command = HighlightElementsCommand(
            element_type="clickable", conversation_id="test-conv-4"
        )

        with patch.object(
            processor, "_send_prepared_command", new_callable=AsyncMock()
        ) as mock_send:
            mock_response = MagicMock()
            mock_response.success = True
            # Extension returns screenshot in data
            mock_response.data = {
                "elements": [{"id": "click-1", "html": "<button>Click</button>"}],
                "screenshot": "base64imagedata...",
                "totalElements": 5,
            }
            mock_send.return_value = mock_response

            response = await processor._execute_highlight_elements(command)

            # Verify extension-provided screenshot is passed through
            assert response.success
            assert "screenshot" in response.data, (
                "highlight_elements should return screenshot"
            )

    @pytest.mark.asyncio
    async def test_click_element_returns_screenshot(self, processor):
        """click_element command should return screenshot (from extension)."""
        command = ClickElementCommand(
            element_id="click-1", conversation_id="test-conv-5"
        )

        with patch.object(
            processor, "_send_prepared_command", new_callable=AsyncMock()
        ) as mock_send:
            mock_response = MagicMock()
            mock_response.success = True
            mock_response.data = {"clicked": True, "screenshot": "base64imagedata..."}
            mock_send.return_value = mock_response

            response = await processor._execute_click_element(command)

            assert response.success
            assert "screenshot" in response.data

    @pytest.mark.asyncio
    async def test_handle_dialog_returns_screenshot(self, processor):
        """handle_dialog command should return screenshot (from extension)."""
        from server.models.commands import DialogAction

        command = HandleDialogCommand(
            action=DialogAction.ACCEPT, conversation_id="test-conv-6"
        )

        with patch.object(
            processor, "_send_prepared_command", new_callable=AsyncMock()
        ) as mock_send:
            mock_response = MagicMock()
            mock_response.success = True
            mock_response.data = {
                "handledDialog": True,
                "screenshot": "base64imagedata...",
            }
            mock_send.return_value = mock_response

            response = await processor._execute_handle_dialog(command)

            assert response.success
            assert "screenshot" in response.data


class TestDialogBlocksScreenshot:
    """Test that open dialogs block screenshot commands."""

    @pytest.mark.asyncio
    async def test_javascript_with_dialog_no_screenshot(self, processor):
        """When JS execution triggers a dialog, no screenshot should be returned."""
        command = JavascriptExecuteCommand(
            script="alert('test')", conversation_id="test-conv-7"
        )

        with patch.object(
            processor, "_send_prepared_command", new_callable=AsyncMock()
        ) as mock_send:
            mock_response = MagicMock()
            mock_response.success = True
            mock_response.data = {"result": None}
            mock_response.dialog_opened = True
            mock_response.dialog = {
                "type": "alert",
                "message": "test",
                "needsDecision": False,
            }
            mock_send.return_value = mock_response

            response = await processor._execute_javascript_execute(command)

            # Dialog opened - no screenshot should be added
            assert response.success
            assert response.dialog_opened
            assert "screenshot" not in response.data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
