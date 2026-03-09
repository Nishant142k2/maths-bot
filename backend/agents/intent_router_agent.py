import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from core.config import settings

# 1. Define the Routing Output Model
class RoutingDecision(BaseModel):
    topic: Literal["Algebra", "Probability", "Calculus", "Linear Algebra", "General Math"] = Field(
        ..., 
        description="The classified math topic"
    )
    difficulty: Literal["Easy", "Medium", "Hard"] = Field(
        ..., 
        description="Estimated difficulty level"
    )
    requires_calculation: bool = Field(
        ..., 
        description="Whether this problem needs numerical computation"
    )
    requires_diagram: bool = Field(
        ..., 
        description="Whether this problem involves graphs or geometric diagrams"
    )
    rag_query: str = Field(
        ..., 
        description="Optimized query for RAG retrieval based on the problem"
    )
    rag_categories: List[str] = Field(
        default_factory=list, 
        description="Which knowledge base categories to search (e.g., ['formulas', 'examples'])"
    )
    solver_strategy: Literal["symbolic", "numerical", "conceptual", "mixed"] = Field(
        ..., 
        description="Which solving approach to use"
    )
    out_of_scope: bool = Field(
        ..., 
        description="True if problem is outside supported math topics"
    )
    reroute_reason: Optional[str] = Field(
        None, 
        description="Explanation if out_of_scope is true"
    )

# 2. Define the Intent Router Agent Class
class IntentRouterAgent:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def _get_system_prompt(self) -> str:
        return """
        You are an Intent Router for a JEE Math Mentor AI system.
        Your job is to classify math problems and route them to the appropriate solver.

        SUPPORTED TOPICS (Scope):
        - Algebra: Equations, inequalities, polynomials, functions, sequences
        - Probability: Combinations, permutations, conditional probability, distributions
        - Calculus: Limits, derivatives, integrals, optimization (basic only)
        - Linear Algebra: Matrices, vectors, systems of equations, determinants

        OUT OF SCOPE (Trigger HITL):
        - Physics, Chemistry, Biology
        - Advanced Geometry, Trigonometry (beyond basics)
        - Olympiad-level problems
        - Non-math subjects

        ROUTING STRATEGIES:
        - "symbolic": For algebraic manipulation, equation solving
        - "numerical": For problems requiring calculation/computation
        - "conceptual": For theory, definitions, proofs
        - "mixed": For problems needing multiple approaches

        RAG CATEGORIES:
        - "formulas": Mathematical formulas and identities
        - "examples": Worked example problems
        - "mistakes": Common pitfalls and errors
        - "constraints": Domain restrictions and rules

        Output ONLY valid JSON. No markdown formatting.
        """

    async def route(self, parsed_problem: dict) -> RoutingDecision:
        """
        Takes parsed problem from Parser Agent and returns routing decision.
        """
        prompt = f"""
        {self._get_system_prompt()}

        Parsed Problem Input:
        {json.dumps(parsed_problem, indent=2)}

        Output JSON Schema:
        {{
            "topic": "string (one of: Algebra, Probability, Calculus, Linear Algebra, General Math)",
            "difficulty": "string (one of: Easy, Medium, Hard)",
            "requires_calculation": boolean,
            "requires_diagram": boolean,
            "rag_query": "string",
            "rag_categories": ["string"],
            "solver_strategy": "string (one of: symbolic, numerical, conceptual, mixed)",
            "out_of_scope": boolean,
            "reroute_reason": "string or null"
        }}
        """

        try:
            response = self.model.generate_content(prompt)
            text_response = response.text
            
            # Clean markdown code blocks if present
            if text_response.startswith("```"):
                text_response = text_response.split("```")[1]
                if text_response.startswith("json"):
                    text_response = text_response[4:]
            text_response = text_response.strip()

            # Validate against Pydantic Model
            routing_data = json.loads(text_response)
            return RoutingDecision(**routing_data)

        except Exception as e:
            # Fallback: Default to safe routing that triggers HITL
            return RoutingDecision(
                topic="Advanced Math",
                difficulty="Medium",
                requires_calculation=True,
                requires_diagram=False,
                rag_query=parsed_problem.get("problem_text", ""),
                rag_categories=["formulas"],
                solver_strategy="mixed",
                out_of_scope=True,
                reroute_reason=f"Router failed to classify: {str(e)}"
            )

# 3. Singleton Instance for easy import
intent_router = IntentRouterAgent()