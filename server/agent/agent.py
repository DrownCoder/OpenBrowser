"""
OpenBrowserAgent - AI agent for browser automation with visual feedback.

This module provides backward-compatible imports from the refactored agent components.
All functionality has been moved to dedicated modules:
- manager.py: OpenBrowserAgentManager class
- api.py: Public API functions
- visualizer.py: QueueVisualizer for SSE streaming
- conversation.py: ConversationState dataclass
"""

# Import all components from their new locations
from server.agent.manager import (
    agent_manager,
    OpenBrowserAgentManager,
)
from server.agent.api import (
    create_agent_conversation,
    process_agent_message,
    get_conversation_info,
    delete_conversation,
    list_conversations,
    initialize_agent,
)
from server.agent.visualizer import QueueVisualizer
from server.agent.conversation import ConversationState
from server.api.sse import SSEEvent

# Maintain backward compatibility - export all symbols that were previously in this file
__all__ = [
    # Classes
    "SSEEvent",
    "QueueVisualizer",
    "ConversationState",
    "OpenBrowserAgentManager",
    # Instances
    "agent_manager",
    # Functions
    "create_agent_conversation",
    "process_agent_message",
    "get_conversation_info",
    "delete_conversation",
    "list_conversations",
    "initialize_agent",
]
