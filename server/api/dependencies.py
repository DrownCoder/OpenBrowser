"""Shared FastAPI dependencies for dependency injection"""

from server.core.config import config
from server.core.processor import command_processor
from server.core.llm_config import llm_config_manager
from server.core.session_manager import session_manager
from server.websocket.manager import ws_manager


def get_config():
    """Get server configuration"""
    return config


def get_command_processor():
    """Get command processor instance"""
    return command_processor


def get_llm_config_manager():
    """Get LLM config manager instance"""
    return llm_config_manager


def get_session_manager():
    """Get session manager instance"""
    return session_manager


def get_ws_manager():
    """Get WebSocket manager instance"""
    return ws_manager
