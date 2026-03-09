# backend/models/database.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# Sessions Table

class SessionDB(BaseModel):
    id: str
    user_input: Optional[str] = None
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    ocr_text: Optional[str] = None
    parsed_problem: Optional[Dict[str, Any]] = None
    solution: Optional[Dict[str, Any]] = None
    hitl_status: str = "pending"
    hitl_feedback: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Documents Table (RAG Knowledge Base)

class DocumentDB(BaseModel):
    id: int
    content: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

# Interactions Table (Memory & Learning)

class InteractionDB(BaseModel):
    id: int
    session_id: str
    problem_embedding: Optional[List[float]] = None
    feedback_score: int  # 1 = correct, 0 = incorrect
    created_at: Optional[datetime] = None