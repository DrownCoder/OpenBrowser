"""
OpenBrowser Agent Module

Provides AI agent capabilities for browser automation with visual feedback.
"""

from server.agent.manager import agent_manager, OpenBrowserAgentManager
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

__all__ = [
    # Manager
    "agent_manager",
    "OpenBrowserAgentManager",
    # API functions
    "create_agent_conversation",
    "process_agent_message",
    "get_conversation_info",
    "delete_conversation",
    "list_conversations",
    "initialize_agent",
    # Components
    "QueueVisualizer",
    "ConversationState",
    "SSEEvent",
]
