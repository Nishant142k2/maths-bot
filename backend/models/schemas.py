# backend/app/models/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

# Upload Endpoints

class UploadResponse(BaseModel):
    session_id: str
    status: Literal["processing", "completed", "error"]
    media_url: Optional[str] = None
    media_type: Literal["image", "audio", "text"]
    extracted_text: Optional[str] = None
    confidence: float = 0.0
    needs_review: bool = True
    error: Optional[str] = None

class TextUploadRequest(BaseModel):
    text: str

# Solve Endpoints

class SolveRequest(BaseModel):
    session_id: str
    confirmed_text: str
    trigger_hitle: bool = False  # Typo preserved from previous code, should be trigger_hitl

class AgentTraceEntry(BaseModel):
    agent: str
    timestamp: str
    status: str
    confidence: Optional[float]
    summary: str

class SolveResponse(BaseModel):
    session_id: str
    status: Literal["processing", "completed", "pending_approval", "error"]
    answer: Optional[str] = None
    explanation: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    hitl_required: bool = False
    hitl_reason: Optional[str] = None
    agent_trace: List[AgentTraceEntry] = []
    rag_sources: List[str] = []
    error: Optional[str] = None

# HITL Endpoints

class HITLDecisionRequest(BaseModel):
    session_id: str
    decision: Literal["approve", "reject", "correct"]
    corrected_solution: Optional[str] = None
    feedback_comment: Optional[str] = None

class HITLDecisionResponse(BaseModel):
    session_id: str
    status: Literal["resumed", "completed", "rejected"]
    message: str
    solution: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None
    agent_trace: List[AgentTraceEntry] = []

class HITLStatusResponse(BaseModel):
    session_id: str
    hitl_status: Literal["pending", "approved", "rejected", "completed"]
    hitl_required: bool
    hitl_reason: Optional[str]
    current_step: str
    can_resume: bool

# Session Endpoints

class SessionSummary(BaseModel):
    session_id: str
    media_type: str
    created_at: str
    status: str
    has_solution: bool

class SessionListResponse(BaseModel):
    sessions: List[SessionSummary]
    total: int