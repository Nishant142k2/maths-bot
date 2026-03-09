# backend/app/models/domain.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

# ============================================================================
# Parser Agent Models
# ============================================================================

class ParsedProblem(BaseModel):
    problem_text: str = Field(..., description="Cleaned problem text")
    topic: str = Field(..., description="Algebra, Probability, Calculus, Linear Algebra")
    variables: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    needs_clarification: bool = Field(default=False)
    ambiguity_reason: Optional[str] = None

# ============================================================================
# Intent Router Models
# ============================================================================

class RoutingDecision(BaseModel):
    topic: Literal["Algebra", "Probability", "Calculus", "Linear Algebra", "General Math"]
    difficulty: Literal["Easy", "Medium", "Hard"]
    requires_calculation: bool
    requires_diagram: bool
    rag_query: str
    rag_categories: List[str]
    solver_strategy: Literal["symbolic", "numerical", "conceptual", "mixed"]
    out_of_scope: bool
    reroute_reason: Optional[str] = None

# ============================================================================
# Solver Agent Models
# ============================================================================

class SolutionStep(BaseModel):
    step_number: int
    description: str
    calculation: Optional[str] = None
    result: Optional[str] = None

class SolverOutput(BaseModel):
    problem_text: str
    topic: str
    steps: List[SolutionStep]
    final_answer: str
    method_used: str
    confidence_score: float
    tools_used: List[str]
    rag_sources_used: List[str]
    needs_verification: bool

# ============================================================================
# Verifier Agent Models
# ============================================================================

class VerificationCheck(BaseModel):
    check_name: str
    passed: bool
    details: str
    severity: Literal["critical", "warning", "info"]

class VerifierOutput(BaseModel):
    solution_valid: bool
    correctness_score: float
    checks_performed: List[VerificationCheck]
    issues_found: List[str]
    edge_cases_considered: List[str]
    domain_constraints_met: bool
    units_consistent: bool
    hitl_required: bool
    hitl_reason: Optional[str] = None
    suggested_corrections: List[str]
    verification_method: str

# ============================================================================
# Explainer Agent Models
# ============================================================================

class ExplanationSection(BaseModel):
    section_title: str
    content: str
    key_takeaways: List[str]

class ExplainerOutput(BaseModel):
    introduction: str
    concept_review: str
    step_by_step_explanation: List[ExplanationSection]
    common_mistakes: List[str]
    practice_tips: List[str]
    final_summary: str
    difficulty_level: str
    estimated_time: str
    related_topics: List[str]
    confidence_indicator: float
    student_friendly: bool