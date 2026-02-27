"""Health check and API info endpoints"""

from fastapi import APIRouter

from server.websocket.manager import ws_manager

router = APIRouter(tags=["health"])


@router.get("/api")
async def api_info():
    """API info endpoint"""
    return {
        "name": "Local Chrome Server",
        "version": "0.1.0",
        "status": "running",
        "websocket_connected": ws_manager.is_connected(),
        "websocket_connections": ws_manager.get_connection_count(),
    }


@router.get("/health")
async def health():
    """Health check endpoint - checks server status, not Chrome extension connection"""
    # Server is healthy if it's running - WebSocket connection status is informational
    return {
        "status": "healthy",
        "websocket_connected": ws_manager.is_connected(),
        "websocket_connections": ws_manager.get_connection_count(),
    }
