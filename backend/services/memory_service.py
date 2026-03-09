# backend/app/services/memory_service.py

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from core.supabase_client import supabase

class MemoryService:
    """Service for memory and self-learning functionality"""
    
    def __init__(self):
        self.session_cache = {}  # In-memory cache for active sessions

    async def store_session(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Store complete session data for memory.
        Includes input, parsed problem, solution, verification, feedback.
        """
        try:
            # Store in sessions table (already done in graph.py)
            # This is for additional memory-specific data
            
            memory_data = {
                "session_id": session_id,
                "original_input": data.get("confirmed_text"),
                "media_type": data.get("media_type"),
                "parsed_problem": json.dumps(data.get("parsed_problem")),
                "solution": json.dumps(data.get("solution")),
                "verification": json.dumps(data.get("verification")),
                "explanation": json.dumps(data.get("explanation")),
                "agent_trace": json.dumps(data.get("agent_trace")),
                "created_at": data.get("created_at", datetime.now().isoformat())
            }
            
            # Update sessions table with full memory
            supabase.table("sessions").upsert(memory_data).execute()
            
            return True
            
        except Exception as e:
            print(f"Memory storage error: {str(e)}")
            return False

    async def store_feedback(
        self,
        session_id: str,
        feedback_type: str,  # "correct" or "incorrect"
        comment: Optional[str] = None
    ) -> bool:
        """
        Store user feedback for self-learning.
        This is used to improve future performance.
        """
        try:
            feedback_score = 1 if feedback_type == "correct" else 0
            
            # Update interactions table
            supabase.table("interactions").insert({
                "session_id": session_id,
                "feedback_score": feedback_score,
                "feedback_comment": comment,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            # Update session hitl_feedback
            supabase.table("sessions").update({
                "hitl_feedback": comment,
                "hitl_status": "completed" if feedback_type == "correct" else "rejected",
                "updated_at": datetime.now().isoformat()
            }).eq("id", session_id).execute()
            
            return True
            
        except Exception as e:
            print(f"Feedback storage error: {str(e)}")
            return False

    async def get_session_history(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete session history.
        """
        try:
            response = supabase.table("sessions").select("*").eq("id", session_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            return None
            
        except Exception as e:
            print(f"Session history retrieval error: {str(e)}")
            return None

    async def get_similar_solved_problems(
        self,
        problem_text: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find similar problems that were solved correctly.
        Used for pattern reuse in solving.
        """
        try:
            # Query interactions with high feedback scores
            response = supabase.table("interactions").select(
                "*, sessions(*)"
            ).eq("feedback_score", 1).limit(limit).execute()
            
            if response.data:
                return response.data
            
            return []
            
        except Exception as e:
            print(f"Similar problems retrieval error: {str(e)}")
            return []

    async def get_correction_patterns(self) -> List[Dict[str, Any]]:
        """
        Retrieve common correction patterns from HITL feedback.
        Used to improve OCR/ASR and parsing over time.
        """
        try:
            response = supabase.table("sessions").select(
                "ocr_text, user_input, hitl_feedback"
            ).not_.is_("hitl_feedback", None).limit(100).execute()
            
            if response.data:
                return response.data
            
            return []
            
        except Exception as e:
            print(f"Correction patterns retrieval error: {str(e)}")
            return []

    def cache_session(self, session_id: str, state: Dict[str, Any]):
        """Cache session state in memory for fast access"""
        self.session_cache[session_id] = {
            "state": state,
            "updated_at": datetime.now()
        }

    def get_cached_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached session state"""
        cached = self.session_cache.get(session_id)
        if cached:
            # Cache expires after 1 hour
            if datetime.now() - cached["updated_at"] < timedelta(hours=1):
                return cached["state"]
            else:
                del self.session_cache[session_id]
        return None

    def clear_expired_cache(self):
        """Clear expired cache entries"""
        now = datetime.now()
        expired = [
            sid for sid, data in self.session_cache.items()
            if now - data["updated_at"] >= timedelta(hours=1)
        ]
        for sid in expired:
            del self.session_cache[sid]

# Singleton instance
memory_service = MemoryService()