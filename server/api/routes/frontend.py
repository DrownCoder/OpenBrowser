"""Frontend serving endpoints"""

import os
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["frontend"])

# Get frontend directory path
FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "frontend",
)
STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "static",
)

# Create directories if they don't exist
os.makedirs(FRONTEND_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)


@router.get("/", response_class=HTMLResponse)
async def get_frontend():
    """Serve the frontend interface"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(
            content="<h1>OpenBrowserAgent</h1><p>Frontend template not found.</p>"
        )


@router.get("/agent-ui", response_class=HTMLResponse)
async def get_agent_ui():
    """Alternative route for agent UI"""
    return await get_frontend()


@router.get("/sessions.html", response_class=HTMLResponse)
async def get_sessions_page():
    """Serve the sessions management page"""
    sessions_path = os.path.join(FRONTEND_DIR, "sessions.html")
    if os.path.exists(sessions_path):
        with open(sessions_path, "r") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(
            content="<h1>Sessions</h1><p>Sessions page not found.</p>", status_code=404
        )
