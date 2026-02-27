"""
Conversation State Model

Dataclass for managing conversation state in memory.
"""

import time
from dataclasses import dataclass, field

from openhands.sdk import Conversation

from server.agent.visualizer import QueueVisualizer


@dataclass
class ConversationState:
    """State for a conversation"""

    conversation_id: str
    conversation: Conversation
    visualizer: QueueVisualizer
    created_at: float = field(default_factory=time.time)
