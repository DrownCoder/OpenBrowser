"""
OpenBrowser Agent Manager

Manages agent instances and conversations.
"""

import json
import logging
import queue
import threading
import time
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator

from pydantic import SecretStr
from openhands.sdk import (
    LLM,
    Agent,
    AgentContext,
    Conversation,
    Event,
    get_logger,
)
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.terminal import TerminalTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools.preset.default import get_default_condenser
from openhands.sdk.tool import Tool

from server.api.sse import SSEEvent
from server.agent.visualizer import QueueVisualizer
from server.agent.conversation import ConversationState
from server.core.llm_config import llm_config_manager
from server.core.session_manager import session_manager, SessionStatus
from server.agent.tools.open_browser_tool import OpenBrowserTool

logger = get_logger(__name__)


class OpenBrowserAgentManager:
    """Manages agent instances and conversations"""

    def __init__(self):
        self.conversations: Dict[str, ConversationState] = {}

        # Lazy initialization of LLM (only when needed)
        self._llm: Optional[LLM] = None

        # Default tools
        self.default_tools = [
            Tool(name="open_browser"),  # Our browser automation tool
            Tool(name=TerminalTool.name),  # Terminal access
            Tool(name=FileEditorTool.name),  # File editing
            Tool(name=TaskTrackerTool.name),  # Task tracking
        ]

    @property
    def llm(self) -> LLM:
        """Lazy initialization of LLM"""
        if self._llm is None:
            self._llm = self._create_default_llm()
        return self._llm

    def _create_default_llm(self) -> LLM:
        """Create default LLM configuration from config file"""
        # Load LLM configuration from file
        llm_config = llm_config_manager.get_llm_config()

        # Check if API key is configured
        if not llm_config.api_key:
            raise ValueError(
                "LLM API key is not configured. "
                "Please configure it through the web interface at http://localhost:8000/ "
                "Or use the API: POST /api/config/llm with {'api_key': 'your-key'}"
            )

        logger.info(
            f"Loading LLM configuration: model={llm_config.model}, base_url={llm_config.base_url}"
        )

        return LLM(
            usage_id="openbrowser-agent",
            model=llm_config.model,
            base_url=llm_config.base_url,
            api_key=SecretStr(llm_config.api_key),
        )

    def create_conversation(
        self, conversation_id: Optional[str] = None, cwd: str = "."
    ) -> str:
        """Create a new conversation with session management

        Args:
            conversation_id: Optional conversation ID (auto-generated if None)
            cwd: Working directory for the conversation (default: current directory)
        """
        import uuid

        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        if conversation_id in self.conversations:
            raise ValueError(f"Conversation {conversation_id} already exists")

        # Create session in session manager
        session_manager.create_session(
            conversation_id=conversation_id, working_directory=cwd
        )

        # Create agent with tools
        agent_context = AgentContext(current_datetime=datetime.now())
        agent = Agent(
            llm=self.llm,
            tools=self.default_tools,
            condenser=get_default_condenser(
                llm=self.llm.model_copy(update={"usage_id": "condenser"})
            ),
            agent_context=agent_context,
        )

        # Create visualizer (queue will be set when processing messages)
        visualizer = QueueVisualizer()

        # Create conversation with specified workspace and conversation_id
        conversation = Conversation(
            agent=agent,
            visualizer=visualizer,
            workspace=cwd,
            conversation_id=conversation_id,
        )

        # Store conversation state
        self.conversations[conversation_id] = ConversationState(
            conversation_id=conversation_id,
            conversation=conversation,
            visualizer=visualizer,
        )

        # Set conversation_id on visualizer for event persistence
        visualizer.set_conversation_id(conversation_id)

        logger.info(f"Created conversation: {conversation_id}")
        return conversation_id

    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)

    def get_or_create_conversation(
        self, conversation_id: str, cwd: str = "."
    ) -> ConversationState:
        """Get existing conversation or create a new one with the given ID

        Args:
            conversation_id: Conversation ID to get or create
            cwd: Working directory for the conversation (default: current directory)
        """
        conv_state = self.get_conversation(conversation_id)
        if conv_state:
            return conv_state

        # Conversation doesn't exist, create it
        if conversation_id in self.conversations:
            # Race condition: conversation was just created by another thread
            return self.conversations[conversation_id]

        # Create session in session manager (if not exists)
        if not session_manager.get_session(conversation_id):
            session_manager.create_session(
                conversation_id=conversation_id, working_directory=cwd
            )

        # Create new conversation with the given ID
        # Create agent with tools
        agent_context = AgentContext(current_datetime=datetime.now())
        agent = Agent(
            llm=self.llm, tools=self.default_tools, agent_context=agent_context
        )

        # Create visualizer (queue will be set when processing messages)
        visualizer = QueueVisualizer()

        # Create conversation with specified workspace and conversation_id
        conversation = Conversation(
            agent=agent,
            visualizer=visualizer,
            workspace=cwd,
            conversation_id=conversation_id,
        )

        # Store conversation state
        self.conversations[conversation_id] = ConversationState(
            conversation_id=conversation_id,
            conversation=conversation,
            visualizer=visualizer,
        )

        # Set conversation_id on visualizer for event persistence
        visualizer.set_conversation_id(conversation_id)

        logger.info(f"Created new conversation with ID: {conversation_id}")
        return self.conversations[conversation_id]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and cleanup resources"""
        if conversation_id in self.conversations:
            # Close conversation
            conv_state = self.conversations[conversation_id]
            try:
                conv_state.conversation.close()
            except Exception as e:
                logger.warning(f"Error closing conversation {conversation_id}: {e}")

            # Remove from memory
            del self.conversations[conversation_id]

            # Update session status to completed
            session_manager.update_session_status(
                conversation_id, SessionStatus.COMPLETED
            )

            # Cleanup command processor state
            from server.core.processor import command_processor

            command_processor.cleanup_conversation(conversation_id)

            logger.info(f"Deleted conversation: {conversation_id}")
            return True

        # Also try to delete from session manager even if not in memory
        # Return the actual result of the deletion operation
        success = session_manager.delete_session(conversation_id)
        if success:
            logger.info(f"Deleted session from database: {conversation_id}")
        return success

    def list_conversations(self, status: SessionStatus = None) -> List[Dict[str, Any]]:
        """List all conversations with enhanced session info

        Args:
            status: Optional status filter (active, idle, error, completed)
        """
        # Get in-memory conversations
        memory_conversations = {}
        for conv in self.conversations.values():
            memory_conversations[conv.conversation_id] = {
                "id": conv.conversation_id,
                "created_at": conv.created_at,
                "agent_id": id(conv.conversation.agent),
                "in_memory": True,
            }

        # Get persisted sessions
        persisted_sessions = session_manager.list_sessions(status=status)

        # Merge information
        result = []
        for session in persisted_sessions:
            conv_id = session.conversation_id
            session_dict = session.to_dict()
            if conv_id in memory_conversations:
                # Merge in-memory and persisted data
                merged = memory_conversations[conv_id].copy()
                merged.update(
                    {
                        "status": session.status.value,
                        "message_count": session.message_count,
                        "last_message_at": session.last_message_at.isoformat()
                        if session.last_message_at
                        else None,
                        "working_directory": session.working_directory,
                        "tags": session.tags,
                        "first_user_message": session.first_user_message,
                    }
                )
                result.append(merged)
            else:
                # Only persisted data (conversation not in memory)
                result.append(
                    {
                        "id": session.conversation_id,
                        "status": session.status.value,
                        "created_at": session.created_at.timestamp(),
                        "updated_at": session.updated_at.isoformat(),
                        "message_count": session.message_count,
                        "last_message_at": session.last_message_at.isoformat()
                        if session.last_message_at
                        else None,
                        "working_directory": session.working_directory,
                        "tags": session.tags,
                        "first_user_message": session.first_user_message,
                        "in_memory": False,
                    }
                )

        return result

    async def process_message(
        self, conversation_id: str, message_text: str, event_callback: callable = None
    ) -> AsyncGenerator[SSEEvent, None]:
        """Process a user message and stream events with session tracking"""
        conv_state = self.get_conversation(conversation_id)
        if not conv_state:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Update session status to active
        session_manager.update_session_status(
            conversation_id, SessionStatus.ACTIVE, increment_message_count=True
        )

        # Save user message for history
        try:
            session_manager.save_user_message(
                conversation_id=conversation_id, message_text=message_text
            )
        except Exception as e:
            logger.warning(f"Failed to save user message: {e}")

        # Set event callback on visualizer
        conv_state.visualizer.event_callback = event_callback

        try:
            # Send user message
            conv_state.conversation.send_message(message_text)

            # Run conversation (this will trigger visualizer callbacks)
            await conv_state.conversation.run_async()

            # Update session status to idle after successful completion
            session_manager.update_session_status(conversation_id, SessionStatus.IDLE)

            # Yield completion event
            yield SSEEvent("complete", {"conversation_id": conversation_id})

        except Exception as e:
            logger.error(f"Error processing message: {e}")

            # Update session status to error
            session_manager.update_session_status(conversation_id, SessionStatus.ERROR)

            yield SSEEvent(
                "error", {"conversation_id": conversation_id, "error": str(e)}
            )

        finally:
            # Clear callback
            conv_state.visualizer.event_callback = None


# Global agent manager instance
agent_manager = OpenBrowserAgentManager()
