# backend/app/models/__init__.py

from .domain import (
    ParsedProblem,
    RoutingDecision,
    SolutionStep,
    SolverOutput,
    VerificationCheck,
    VerifierOutput,
    ExplanationSection,
    ExplainerOutput
)

from .schemas import (
    UploadResponse,
    SolveRequest,
    SolveResponse,
    HITLDecisionRequest,
    HITLDecisionResponse,
    SessionSummary
)

from .database import (
    SessionDB,
    DocumentDB,
    InteractionDB
)

__all__ = [
    # Domain Models (Agents)
    "ParsedProblem",
    "RoutingDecision",
    "SolverOutput",
    "VerifierOutput",
    "ExplainerOutput",
    
    # API Schemas
    "UploadResponse",
    "SolveRequest",
    "SolveResponse",
    "HITLDecisionRequest",
    "HITLDecisionResponse",
    
    # Database Models
    "SessionDB",
    "DocumentDB",
    "InteractionDB"
]