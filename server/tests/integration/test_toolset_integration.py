"""
Integration tests for OpenBrowserToolSet - Verifies 5-tool integration works correctly.

This test suite validates that all 5 OpenBrowser tools work together correctly,
share executor state for 2PC flow, maintain conversation isolation, and follow
the expected workflow patterns.
"""

import sys
import importlib.util
from pathlib import Path

import pytest

# Setup module mocks to avoid import errors from server/agent/__init__.py
import types

class MockTerminalTool:
    name = "terminal"

class MockFileEditorTool:
    name = "file_editor"

class MockTaskTrackerTool:
    name = "task_tracker"

# Create mock modules
terminal_module = types.ModuleType('openhands.tools.terminal')
terminal_module.TerminalTool = MockTerminalTool
sys.modules['openhands.tools.terminal'] = terminal_module

file_editor_module = types.ModuleType('openhands.tools.file_editor')
file_editor_module.FileEditorTool = MockFileEditorTool
sys.modules['openhands.tools.file_editor'] = file_editor_module

task_tracker_module = types.ModuleType('openhands.tools.task_tracker')
task_tracker_module.TaskTrackerTool = MockTaskTrackerTool
sys.modules['openhands.tools.task_tracker'] = task_tracker_module

preset_default_module = types.ModuleType('openhands.tools.preset.default')
preset_default_module.get_default_condenser = lambda: None
sys.modules['openhands.tools.preset.default'] = preset_default_module

# Parent modules
sys.modules['openhands.tools'] = types.ModuleType('openhands.tools')
sys.modules['openhands.tools.preset'] = types.ModuleType('openhands.tools.preset')

# Add server root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import modules directly to avoid triggering server/agent/__init__.py
def import_module_directly(module_path, module_name):
    """Import a module directly from a file path."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Import base module
BASE_MODULE_PATH = Path(__file__).parent.parent.parent / "agent" / "tools" / "base.py"
base_module = import_module_directly(BASE_MODULE_PATH, "base")

# Import toolset
TOOLSET_PATH = Path(__file__).parent.parent.parent / "agent" / "tools" / "toolset.py"
toolset_module = import_module_directly(TOOLSET_PATH, "toolset")
OpenBrowserToolSet = toolset_module.OpenBrowserToolSet

# Import state module
STATE_PATH = Path(__file__).parent.parent.parent / "agent" / "tools" / "state.py"
state_module = import_module_directly(STATE_PATH, "state")
OpenBrowserState = state_module.OpenBrowserState
PendingConfirmation = state_module.PendingConfirmation

# Import tool modules
def import_tool_module(module_name):
    """Import a tool module directly."""
    module_path = Path(__file__).parent.parent.parent / "agent" / "tools" / f"{module_name}.py"
    return import_module_directly(module_path, module_name)

# Import all tool modules
tab_tool_module = import_tool_module("tab_tool")
highlight_tool_module = import_tool_module("highlight_tool")
element_interaction_tool_module = import_tool_module("element_interaction_tool")
dialog_tool_module = import_tool_module("dialog_tool")
javascript_tool_module = import_tool_module("javascript_tool")


class TestToolSetIntegration:
    """Integration tests for OpenBrowserToolSet."""
    
    def test_all_five_tools_registered_correctly(self):
        """Test that all 5 tools are registered with correct names."""
        tools = OpenBrowserToolSet.create(None)
        
        # Should have exactly 5 tools
        assert len(tools) == 5
        
        # Check tool names
        tool_names = [tool.name for tool in tools]
        assert "tab" in tool_names
        assert "highlight" in tool_names
        assert "element_interaction" in tool_names
        assert "dialog" in tool_names
        assert "javascript" in tool_names
        
        # Check tool kinds (instead of isinstance due to import path differences)
        tool_map = {tool.name: tool for tool in tools}
        assert tool_map["tab"].kind == "TabTool"
        assert tool_map["highlight"].kind == "HighlightTool"
        assert tool_map["element_interaction"].kind == "ElementInteractionTool"
        assert tool_map["dialog"].kind == "DialogTool"
        assert tool_map["javascript"].kind == "JavaScriptTool"
    
    def test_tools_have_shared_state_capability(self):
        """Test that tools are designed to share executor state for 2PC."""
        # When tools are created with None executor, ToolSet creates a shared executor
        tools = OpenBrowserToolSet.create(None)
        
        # All tools should have the same executor instance for shared state
        executors = {tool.executor for tool in tools}
        assert len(executors) == 1, "All tools should share the same executor instance"
        assert next(iter(executors)) is not None, "Executor should be created when None is passed"
        
        # Verify the executor is a BrowserExecutor
        from server.agent.tools.browser_executor import BrowserExecutor
        assert isinstance(next(iter(executors)), BrowserExecutor)
        
        # Note: In production, the executor is shared across all tools
        # This enables 2PC state sharing across different tool types
    
    def test_conversation_isolation_in_state(self):
        """Test that OpenBrowserState provides conversation isolation."""
        state = OpenBrowserState()
        
        # Set pending confirmation for conversation 1
        state.set_pending(
            conversation_id="conv1",
            element_id="elem1",
            action_type="click",
            full_html="<button>Test</button>",
            extra_data={},
            screenshot_data_url=None
        )
        
        # Set pending confirmation for conversation 2
        state.set_pending(
            conversation_id="conv2",
            element_id="elem2",
            action_type="hover",
            full_html="<div>Hover me</div>",
            extra_data={},
            screenshot_data_url=None
        )
        
        # Verify isolation
        conv1_pending = state.get_pending("conv1")
        conv2_pending = state.get_pending("conv2")
        
        assert conv1_pending is not None
        assert conv1_pending.element_id == "elem1"
        assert conv1_pending.action_type == "click"
        
        assert conv2_pending is not None
        assert conv2_pending.element_id == "elem2"
        assert conv2_pending.action_type == "hover"
        
        # Confirmations should not cross contaminate
        assert state.get_pending("conv3") is None
        
        # Clear conversation 1
        state.clear_pending("conv1")
        assert state.get_pending("conv1") is None
        assert state.get_pending("conv2") is not None  # conv2 should still exist
    
    def test_tool_descriptions_are_focused_and_non_overlapping(self):
        """Test that each tool has a focused, non-overlapping description."""
        tools = OpenBrowserToolSet.create(None)
        
        descriptions = {}
        for tool in tools:
            assert tool.description, f"Tool {tool.name} has empty description"
            assert len(tool.description) > 50, f"Tool {tool.name} description too short"
            
            # Store for uniqueness check
            descriptions[tool.name] = tool.description
        
        # Check that descriptions are different (not identical)
        description_set = set(descriptions.values())
        # It's okay if descriptions are similar but should not be identical
        assert len(description_set) >= 3, "Tool descriptions should be mostly unique"
        
        # Check for focus areas in descriptions
        assert "tab" in descriptions["tab"].lower() or "browser" in descriptions["tab"].lower()
        assert "highlight" in descriptions["highlight"].lower() or "element" in descriptions["highlight"].lower()
        assert "click" in descriptions["element_interaction"].lower() or "interaction" in descriptions["element_interaction"].lower()
        assert "dialog" in descriptions["dialog"].lower()
        assert "javascript" in descriptions["javascript"].lower() or "script" in descriptions["javascript"].lower()
    
    def test_tool_action_types_match_expected(self):
        """Test that each tool uses the correct action type."""
        tools = OpenBrowserToolSet.create(None)
        
        # Get action types from imported modules
        TabAction = tab_tool_module.TabAction
        HighlightAction = highlight_tool_module.HighlightAction
        ElementInteractionAction = element_interaction_tool_module.ElementInteractionAction
        DialogHandleAction = dialog_tool_module.DialogHandleAction
        JavaScriptAction = javascript_tool_module.JavaScriptAction
        
        tool_map = {tool.name: tool for tool in tools}
        
        # Check action type names match (not exact class equality due to import paths)
        assert tool_map["tab"].action_type.__name__ == TabAction.__name__
        assert tool_map["highlight"].action_type.__name__ == HighlightAction.__name__
        assert tool_map["element_interaction"].action_type.__name__ == ElementInteractionAction.__name__
        assert tool_map["dialog"].action_type.__name__ == DialogHandleAction.__name__
        assert tool_map["javascript"].action_type.__name__ == JavaScriptAction.__name__
    
    def test_tool_annotations_reflect_capabilities(self):
        """Test that tool annotations correctly indicate capabilities."""
        tools = OpenBrowserToolSet.create(None)
        
        for tool in tools:
            assert tool.annotations is not None, f"Tool {tool.name} missing annotations"
            
            # Check annotations make sense for each tool type
            if tool.name == "tab":
                # Tab tool is destructive (closes tabs) and not read-only
                assert tool.annotations.destructiveHint is True
                assert tool.annotations.readOnlyHint is False
            
            elif tool.name == "highlight":
                # Highlight tool is read-only (doesn't modify page)
                assert tool.annotations.readOnlyHint is True
                assert tool.annotations.destructiveHint is False
            
            elif tool.name == "element_interaction":
                # Element interaction is destructive (clicks, inputs)
                assert tool.annotations.destructiveHint is True
                assert tool.annotations.readOnlyHint is False
            
            elif tool.name == "dialog":
                # Dialog tool may be marked as destructive or not
                # Either way is acceptable as long as readOnlyHint is False
                assert tool.annotations.readOnlyHint is False
            
            elif tool.name == "javascript":
                # JavaScript tool may be marked as destructive or not
                # Either way is acceptable as long as readOnlyHint is False
                assert tool.annotations.readOnlyHint is False
    
    def test_tool_workflow_coherence(self):
        """Test that tools work together in a coherent workflow."""
        # This test verifies the expected workflow between tools
        tools = OpenBrowserToolSet.create(None)
        tool_names = [tool.name for tool in tools]
        
        # Expected workflow: tab → highlight → element_interaction → dialog → javascript (fallback)
        # All tools should be present
        assert "tab" in tool_names  # Start session
        assert "highlight" in tool_names  # Discover elements
        assert "element_interaction" in tool_names  # Interact with elements
        assert "dialog" in tool_names  # Handle dialogs
        assert "javascript" in tool_names  # Fallback for complex operations
        
        # Check observation type consistency
        for tool in tools:
            # All tools should use OpenBrowserObservation
            assert tool.observation_type.__name__ == "OpenBrowserObservation"
    
    def test_state_pending_confirmation_structure(self):
        """Test that PendingConfirmation dataclass has expected structure."""
        # Create a sample pending confirmation
        pc = PendingConfirmation(
            element_id="abc123",
            action_type="click",
            full_html="<button>Click me</button>",
            extra_data={"test": "data"},
            screenshot_data_url="data:image/png;base64,..."
        )
        
        # Check structure
        assert pc.element_id == "abc123"
        assert pc.action_type == "click"
        assert pc.full_html == "<button>Click me</button>"
        assert pc.extra_data == {"test": "data"}
        assert pc.screenshot_data_url == "data:image/png;base64,..."
        
        # Test with minimal data
        pc2 = PendingConfirmation(
            element_id="def456",
            action_type="hover",
            full_html="<div>Hover</div>"
        )
        assert pc2.element_id == "def456"
        assert pc2.action_type == "hover"
        assert pc2.full_html == "<div>Hover</div>"
        assert pc2.extra_data == {}
        assert pc2.screenshot_data_url is None