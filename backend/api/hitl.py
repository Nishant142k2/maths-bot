# backend/app/api/hitl.py

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel
from agents.graph import run_graph_resume, get_session_state
from services.memory_service import memory_service
from utils.validators import validators
from utils.logger import logger
from utils.exceptions import SessionNotFoundException, HITLException, ValidationException
from utils.formatters import formatters

router = APIRouter(prefix="/api/v1/hitl", tags=["HITL"])

class HITLDecisionRequest(BaseModel):
    session_id: str
    decision: str  # "approve", "reject", "correct"
    corrected_solution: Optional[str] = None  # If decision is "correct"
    feedback_comment: Optional[str] = None

class HITLDecisionResponse(BaseModel):
    session_id: str
    status: str  # "resumed", "completed", "rejected"
    message: str
    solution: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None
    agent_trace: list = []

class HITLStatusResponse(BaseModel):
    session_id: str
    hitl_status: str  # "pending", "approved", "rejected", "completed"
    hitl_required: bool
    hitl_reason: Optional[str]
    current_step: str  # Which agent paused
    can_resume: bool

@router.post("/decide", response_model=HITLDecisionResponse)
async def hitl_decision(request: HITLDecisionRequest):
    """
    Handle HITL decision (approve/reject/correct).
    Resumes the workflow if approved.
    """
    try:
        # Validate session ID
        is_valid, error = validators.validate_session_id(request.session_id)
        if not is_valid:
            raise ValidationException(error)
        
        # Validate decision
        is_valid, error = validators.validate_hitl_decision(request.decision)
        if not is_valid:
            raise ValidationException(error)
        
        logger.info(f"[HITL] Decision received for session {request.session_id}: {request.decision}")
        
        # Handle rejection
        if request.decision == "reject":
            # Update session status
            from core.supabase_client import supabase
            supabase.table("sessions").update({
                "hitl_status": "rejected",
                "hitl_feedback": request.feedback_comment or "User rejected solution",
                "updated_at": None  # Auto-generated
            }).eq("id", request.session_id).execute()
            
            return HITLDecisionResponse(
                session_id=request.session_id,
                status="rejected",
                message="Solution rejected by user",
                solution=None,
                explanation=None,
                agent_trace=[]
            )
        
        # Handle approval or correction - Resume workflow
        if request.decision in ["approve", "correct"]:
            # Resume the graph
            final_state = await run_graph_resume(
                session_id=request.session_id,
                hitl_decision=request.decision,
                corrected_solution=request.corrected_solution
            )
            
            # Determine status
            status = "completed" if final_state.get("hitl_status") == "completed" else "resumed"
            
            return HITLDecisionResponse(
                session_id=request.session_id,
                status=status,
                message=f"Workflow {status}. Decision: {request.decision}",
                solution=final_state.get("final_output", {}).get("answer") if final_state.get("final_output") else None,
                explanation=final_state.get("final_output", {}).get("explanation") if final_state.get("final_output") else None,
                agent_trace=formatters.format_agent_trace(final_state.get("agent_trace", []))
            )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except SessionNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"HITL decision error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/status", response_model=HITLStatusResponse)
async def get_hitl_status(session_id: str):
    """
    Check HITL status for a session.
    """
    try:
        # Validate session ID
        is_valid, error = validators.validate_session_id(session_id)
        if not is_valid:
            raise ValidationException(error)
        
        # Get session state
        state = await get_session_state(session_id)
        
        if not state:
            raise SessionNotFoundException(session_id)
        
        # Determine current step based on what's completed
        current_step = "unknown"
        if state.get("parsed_problem") and not state.get("routing_decision"):
            current_step = "router"
        elif state.get("routing_decision") and not state.get("solution"):
            current_step = "solver"
        elif state.get("solution") and not state.get("verification"):
            current_step = "verifier"
        elif state.get("verification") and not state.get("explanation"):
            current_step = "explainer"
        elif state.get("explanation"):
            current_step = "completed"
        
        can_resume = state.get("hitl_status") == "approved"
        
        return HITLStatusResponse(
            session_id=session_id,
            hitl_status=state.get("hitl_status", "pending"),
            hitl_required=state.get("hitl_required", False),
            hitl_reason=state.get("hitl_reason"),
            current_step=current_step,
            can_resume=can_resume
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except SessionNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"HITL status check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/history", response_model=Dict[str, Any])
async def get_session_history(session_id: str):
    """
    Get complete session history (for debugging and memory).
    """
    try:
        # Validate session ID
        is_valid, error = validators.validate_session_id(session_id)
        if not is_valid:
            raise ValidationException(error)
        
        # Get session history
        history = await memory_service.get_session_history(session_id)
        
        if not history:
            raise SessionNotFoundException(session_id)
        
        return {
            "session_id": session_id,
            "history": history,
            "agent_trace": formatters.format_agent_trace(history.get("agent_trace", [])),
            "memory_used": history.get("memory_used", False)
        }
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except SessionNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Session history error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))