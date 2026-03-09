# backend/api/session.py

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from services.memory_service import memory_service
from utils.validators import validators
from utils.logger import logger
from utils.exceptions import SessionNotFoundException, ValidationException

router = APIRouter(prefix="/api/v1/session", tags=["Session"])

class SessionSummary(BaseModel):
    session_id: str
    media_type: str
    created_at: str
    status: str
    has_solution: bool

class SessionListResponse(BaseModel):
    sessions: List[SessionSummary]
    total: int

@router.get("/{session_id}", response_model=Dict[str, Any])
async def get_session(session_id: str):
    """
    Get complete session data.
    """
    try:
        # Validate session ID
        is_valid, error = validators.validate_session_id(session_id)
        if not is_valid:
            raise ValidationException(error)
        
        # Get session
        session = await memory_service.get_session_history(session_id)
        
        if not session:
            raise SessionNotFoundException(session_id)
        
        return {
            "success": True,
            "session": session
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except SessionNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Get session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=SessionListResponse)
async def list_sessions(limit: int = 10, offset: int = 0):
    """
    List recent sessions (for admin/debug).
    """
    try:
        from core.supabase_client import supabase
        
        response = supabase.table("sessions").select(
            "id, media_type, created_at, hitl_status, solution"
        ).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        sessions = []
        for row in response.data or []:
            sessions.append(SessionSummary(
                session_id=row["id"],
                media_type=row.get("media_type", "text"),
                created_at=row.get("created_at", ""),
                status=row.get("hitl_status", "pending"),
                has_solution=row.get("solution") is not None
            ))
        
        return SessionListResponse(
            sessions=sessions,
            total=len(sessions)
        )
        
    except Exception as e:
        logger.error(f"List sessions error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session (for cleanup).
    """
    try:
        # Validate session ID
        is_valid, error = validators.validate_session_id(session_id)
        if not is_valid:
            raise ValidationException(error)
        
        from core.supabase_client import supabase
        
        # Delete from sessions table
        supabase.table("sessions").delete().eq("id", session_id).execute()
        
        # Clear cache
        memory_service.cache_session(session_id, {})  # Effectively removes
        
        logger.info(f"Session deleted: {session_id}")
        
        return {"success": True, "message": "Session deleted"}
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Delete session error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))