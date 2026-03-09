# backend/api/__init__.py

from fastapi import APIRouter
from .upload import router as upload_router
from .solve import router as solve_router
from .hitl import router as hitl_router
from .session import router as session_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all routers
api_router.include_router(upload_router)
api_router.include_router(solve_router)
api_router.include_router(hitl_router)
api_router.include_router(session_router)

__all__ = ["api_router"]