# backend/app/api/solve.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
from pydantic import BaseModel
from core.config import settings
from agents.graph import (
    run_graph_initial,
    run_graph_resume,
    get_session_state,
    math_mentor_graph
)
from services.memory_service import memory_service
from utils.validators import validators
from utils.logger import logger
from utils.exceptions import SessionNotFoundException, AgentException, ValidationException
from utils.formatters import formatters

router = APIRouter(prefix="/api/v1/solve", tags=["Solve"])

class SolveRequest(BaseModel):
    session_id: str
    confirmed_text: str  # User-confirmed text after OCR/ASR review
    trigger_hitle: bool = False  # Force HITL for testing

class SolveResponse(BaseModel):
    session_id: str
    status: str  # "processing", "completed", "pending_approval", "error"
    answer: Optional[str] = None
    explanation: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    hitl_required: bool = False
    hitl_reason: Optional[str] = None
    agent_trace: list = []
    rag_sources: list = []
    error: Optional[str] = None

class HITLResponse(BaseModel):
    session_id: str
    status: str
    message: str

@router.post("/", response_model=SolveResponse)
async def solve_problem(request: SolveRequest, background_tasks: BackgroundTasks = None):
    """
    Trigger the multi-agent solving workflow.
    This starts the LangGraph with all 5 agents.
    """
    try:
        # Validate session ID
        is_valid, error = validators.validate_session_id(request.session_id)
        if not is_valid:
            raise ValidationException(error)
        
        # Validate text
        is_valid, error = validators.validate_math_text(request.confirmed_text)
        if not is_valid:
            raise ValidationException(error)
        
        logger.info(f"[Solve] Starting workflow for session: {request.session_id}")
        
        # Run the graph asynchronously
        # For production, this should be a background task with polling
        final_state = await run_graph_initial(
            session_id=request.session_id,
            confirmed_text=request.confirmed_text,
            media_type="text"  # Will be updated from session
        )
        
        # Build response
        status = "completed"
        if final_state.get("hitl_required"):
            status = "pending_approval"
        elif final_state.get("error_message"):
            status = "error"
        
        response = SolveResponse(
            session_id=request.session_id,
            status=status,
            answer=final_state.get("final_output", {}).get("answer") if final_state.get("final_output") else None,
            explanation=final_state.get("final_output", {}).get("explanation") if final_state.get("final_output") else None,
            confidence=final_state.get("final_output", {}).get("confidence", 0.0) if final_state.get("final_output") else 0.0,
            hitl_required=final_state.get("hitl_required", False),
            hitl_reason=final_state.get("hitl_reason"),
            agent_trace=formatters.format_agent_trace(final_state.get("agent_trace", [])),
            rag_sources=final_state.get("rag_sources", []),
            error=final_state.get("error_message")
        )
        
        logger.info(f"[Solve] Workflow complete for session: {request.session_id}, Status: {status}")
        
        return response
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except SessionNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Solve workflow error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}", response_model=SolveResponse)
async def get_solution_status(session_id: str):
    """
    Check status of solving workflow (for polling).
    """
    try:
        # Validate session ID
        is_valid, error = validators.validate_session_id(session_id)
        if not is_valid:
            raise ValidationException(error)
        
        # Get session state from Supabase
        state = await get_session_state(session_id)
        
        if not state:
            raise SessionNotFoundException(session_id)
        
        # Determine status
        status = "processing"
        if state.get("hitl_status") == "completed":
            status = "completed"
        elif state.get("hitl_status") == "pending_approval":
            status = "pending_approval"
        elif state.get("hitl_status") == "error":
            status = "error"
        
        # Build response
        response = SolveResponse(
            session_id=session_id,
            status=status,
            answer=state.get("solution", {}).get("final_answer") if state.get("solution") else None,
            explanation=state.get("explanation"),
            confidence=state.get("verification", {}).get("correctness_score", 0.0) if state.get("verification") else 0.0,
            hitl_required=state.get("hitl_required", False),
            hitl_reason=state.get("hitl_reason"),
            agent_trace=formatters.format_agent_trace(state.get("agent_trace", [])),
            rag_sources=state.get("rag_sources", []),
            error=state.get("error_message")
        )
        
        return response
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except SessionNotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error(f"Solution status check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/feedback", response_model=HITLResponse)
async def submit_feedback(session_id: str, feedback_type: str, comment: Optional[str] = None):
    """
    Submit user feedback for self-learning.
    feedback_type: "correct" or "incorrect"
    """
    try:
        # Validate session ID
        is_valid, error = validators.validate_session_id(session_id)
        if not is_valid:
            raise ValidationException(error)
        
        # Validate feedback type
        if feedback_type not in ["correct", "incorrect"]:
            raise ValidationException("Feedback type must be 'correct' or 'incorrect'")
        
        # Store feedback
        from services.memory_service import memory_service
        from services.rag_service import rag_service
        
        await memory_service.store_feedback(session_id, feedback_type, comment)
        
        # Get session for problem text
        session = await memory_service.get_session_history(session_id)
        if session and session.get("user_input"):
            # Store interaction for memory
            feedback_score = 1 if feedback_type == "correct" else 0
            await rag_service.store_interaction(
                session_id=session_id,
                problem_text=session["user_input"],
                feedback_score=feedback_score
            )
        
        logger.info(f"[Feedback] Received for session {session_id}: {feedback_type}")
        
        return HITLResponse(
            session_id=session_id,
            status="success",
            message=f"Feedback recorded: {feedback_type}"
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        logger.error(f"Feedback submission error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))