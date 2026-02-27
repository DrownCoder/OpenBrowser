"""Configuration management endpoints"""

import os
from fastapi import APIRouter, HTTPException, Request

from server.core.llm_config import llm_config_manager, LLMConfig

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/llm")
async def get_llm_config():
    """Get LLM configuration (API key will be masked)"""
    try:
        config = llm_config_manager.get_llm_config()
        # Mask the API key for security
        masked_config = {
            "model": config.model,
            "base_url": config.base_url,
            "api_key": "********" if config.api_key else None,
            "has_api_key": config.api_key is not None and len(config.api_key) > 0,
        }
        return {"success": True, "config": masked_config}
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Error getting LLM config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm")
async def update_llm_config(request: Request):
    """Update LLM configuration"""
    try:
        data = await request.json()

        # Build LLMConfig object
        model = data.get("model", "dashscope/qwen3.5-plus")
        base_url = data.get(
            "base_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        api_key = data.get("api_key")

        # If api_key is the masked value, keep the existing one
        if api_key == "********":
            existing_config = llm_config_manager.get_llm_config()
            api_key = existing_config.api_key

        llm_config = LLMConfig(model=model, base_url=base_url, api_key=api_key)

        updated_config = llm_config_manager.set_llm_config(llm_config)

        return {
            "success": True,
            "message": "LLM configuration updated successfully",
            "config": {
                "model": updated_config.model,
                "base_url": updated_config.base_url,
                "api_key": "********" if updated_config.api_key else None,
                "has_api_key": updated_config.api_key is not None
                and len(updated_config.api_key) > 0,
            },
        }
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Error updating LLM config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cwd")
async def get_default_cwd():
    """Get default working directory"""
    try:
        cwd = llm_config_manager.get_default_cwd()
        return {"success": True, "default_cwd": cwd}
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Error getting default CWD: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cwd")
async def set_default_cwd(request: Request):
    """Set default working directory"""
    try:
        data = await request.json()
        cwd = data.get("cwd")

        if not cwd:
            raise HTTPException(status_code=400, detail="cwd field is required")

        # Validate that the directory exists
        if not os.path.isdir(cwd):
            raise HTTPException(
                status_code=400, detail=f"Directory does not exist: {cwd}"
            )

        updated_cwd = llm_config_manager.set_default_cwd(cwd)

        return {
            "success": True,
            "message": "Default working directory updated successfully",
            "default_cwd": updated_cwd,
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Error setting default CWD: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_full_config():
    """Get full application configuration (API key will be masked)"""
    try:
        config = llm_config_manager.get_full_config()
        return {
            "success": True,
            "config": {
                "llm": {
                    "model": config.llm.model,
                    "base_url": config.llm.base_url,
                    "api_key": "********" if config.llm.api_key else None,
                    "has_api_key": config.llm.api_key is not None
                    and len(config.llm.api_key) > 0,
                },
                "default_cwd": config.default_cwd,
                "is_configured": llm_config_manager.is_configured(),
            },
        }
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Error getting full config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
