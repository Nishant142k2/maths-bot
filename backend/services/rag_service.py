# backend/services/rag_service.py

import json
from typing import List, Dict, Any, Optional
from core.config import settings
from core.supabase_client import supabase
from core.gemini_client import get_embedding

class RAGService:
    """Service for RAG pipeline - vector search and knowledge retrieval"""
    
    def __init__(self):
        self.embedding_dimension = settings.EMBEDDING_DIMENSION
        self.top_k = settings.RAG_TOP_K

    async def search(
        self, 
        query: str, 
        categories: Optional[List[str]] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base for relevant chunks.
        Uses pgvector similarity search in Supabase.
        """
        try:
            # Generate embedding for query
            query_embedding = get_embedding(query)
            
            # Build SQL query for vector similarity
            # Using Supabase RPC for efficient pgvector search
            top_k = top_k or self.top_k
            
            # Method 1: Using raw SQL with vector similarity
            response = supabase.rpc(
                "match_documents",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.5,
                    "match_count": top_k,
                    "filter_categories": categories
                }
            ).execute()
            
            if response.data:
                chunks = []
                for item in response.data:
                    chunks.append({
                        "id": item.get("id"),
                        "content": item.get("content"),
                        "metadata": item.get("metadata", {}),
                        "similarity": item.get("similarity", 0.0)
                    })
                return chunks
            
            # Fallback: Simple select with ordering (if RPC not set up)
            return await self._fallback_search(query_embedding, categories, top_k)
            
        except Exception as e:
            print(f"RAG search error: {str(e)}")
            return []

    async def _fallback_search(
        self, 
        query_embedding: List[float], 
        categories: Optional[List[str]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Fallback search if RPC function not available"""
        query = supabase.table("documents").select(
            "id, content, metadata, embedding"
        )
        
        if categories:
            query = query.filter("metadata->>category", "in", f"({','.join(categories)})")
        
        response = query.limit(top_k).execute()
        
        chunks = []
        for item in response.data:
            chunks.append({
                "id": item["id"],
                "content": item["content"],
                "metadata": item.get("metadata", {}),
                "similarity": 0.0  # Can't calculate without RPC
            })
        
        return chunks

    async def find_similar_problems(
        self, 
        problem_text: str, 
        limit: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find similar solved problems from memory for pattern reuse.
        This implements the self-learning requirement.
        """
        try:
            # Search interactions table for similar past problems
            problem_embedding = get_embedding(problem_text)
            
            response = supabase.rpc(
                "match_interactions",
                {
                    "query_embedding": problem_embedding,
                    "match_threshold": 0.6,
                    "match_count": limit,
                    "min_feedback_score": 1  # Only successful solutions
                }
            ).execute()
            
            if response.data:
                return response.data
            
            return []
            
        except Exception as e:
            print(f"Similar problems search error: {str(e)}")
            return []

    async def ingest_document(
        self, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Ingest a new document into the knowledge base.
        Used for initial setup or dynamic learning.
        """
        try:
            # Generate embedding
            embedding = get_embedding(content)
            
            # Insert into documents table
            response = supabase.table("documents").insert({
                "content": content,
                "embedding": embedding,
                "metadata": metadata
            }).execute()
            
            return response.data is not None
            
        except Exception as e:
            print(f"Document ingestion error: {str(e)}")
            return False

    async def store_interaction(
        self,
        session_id: str,
        problem_text: str,
        feedback_score: int
    ) -> bool:
        """
        Store interaction for memory and self-learning.
        feedback_score: 1 = correct, 0 = incorrect
        """
        try:
            problem_embedding = get_embedding(problem_text)
            
            response = supabase.table("interactions").insert({
                "session_id": session_id,
                "problem_embedding": problem_embedding,
                "feedback_score": feedback_score
            }).execute()
            
            return response.data is not None
            
        except Exception as e:
            print(f"Interaction storage error: {str(e)}")
            return False

# Singleton instance
rag_service = RAGService()