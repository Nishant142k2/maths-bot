import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from core.config import settings
import re

# 1. Define the Solution Output Model
class SolutionStep(BaseModel):
    step_number: int = Field(..., description="Sequential step number")
    description: str = Field(..., description="Human-readable description of this step")
    calculation: Optional[str] = Field(None, description="Mathematical calculation performed")
    result: Optional[str] = Field(None, description="Result of this step")

class SolverOutput(BaseModel):
    problem_text: str = Field(..., description="The problem being solved")
    topic: str = Field(..., description="Math topic")
    steps: List[SolutionStep] = Field(..., description="Step-by-step solution")
    final_answer: str = Field(..., description="Final answer in boxed format")
    method_used: str = Field(..., description="Solution method (e.g., 'quadratic formula', 'chain rule')")
    confidence_score: float = Field(..., description="Agent's confidence in solution (0.0 to 1.0)")
    tools_used: List[str] = Field(default_factory=list, description="Tools used (e.g., ['python_calculator', 'rag_context'])")
    rag_sources_used: List[str] = Field(default_factory=list, description="IDs or titles of RAG chunks referenced")
    needs_verification: bool = Field(..., description="True if solution should be verified by Verifier Agent")

# 2. Python Calculator Tool (for numerical computation)
class PythonCalculator:
    """Safe Python calculator for mathematical expressions"""
    
    @staticmethod
    def calculate(expression: str) -> Dict[str, Any]:
        """
        Safely evaluate mathematical expressions.
        Only allows safe math operations.
        """
        allowed_chars = set("0123456789+-*/().^% ")
        if not all(c in allowed_chars for c in expression):
            return {"success": False, "error": "Invalid characters in expression"}
        
        try:
            # Replace ^ with ** for Python exponentiation
            expression = expression.replace("^", "**")
            result = eval(expression)
            return {"success": True, "result": str(result)}
        except Exception as e:
            return {"success": False, "error": str(e)}

# 3. Define the Solver Agent Class
class SolverAgent:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.calculator = PythonCalculator()

    def _get_system_prompt(self) -> str:
        return """
        You are an expert JEE Math Solver AI.
        Your goal is to solve math problems accurately with clear step-by-step reasoning.

        RULES:
        1. Show ALL steps clearly - no skipped calculations
        2. Use proper mathematical notation (LaTeX-style where helpful)
        3. Box the final answer like: \\boxed{answer}
        4. If using RAG context, cite which formulas/concepts you're using
        5. For numerical calculations, you can use the Python calculator tool
        6. Be aware of domain constraints (e.g., x > 0, integer only)
        7. If you're unsure about any step, lower your confidence_score

        CONFIDENCE SCORING:
        - 0.9-1.0: Very confident, standard problem type
        - 0.7-0.9: Confident, but has some complexity
        - 0.5-0.7: Uncertain, unusual problem or multiple approaches
        - Below 0.5: Not confident, should trigger HITL

        Output ONLY valid JSON. No markdown formatting.
        """

    def _build_prompt(
        self, 
        parsed_problem: dict, 
        routing_decision: dict, 
        rag_context: List[dict]
    ) -> str:
        """Build the complete prompt with all context"""
        
        # Format RAG context
        rag_text = ""
        if rag_context:
            rag_text = "\n\nRETRIEVED KNOWLEDGE BASE CONTEXT:\n"
            for i, chunk in enumerate(rag_context):
                rag_text += f"[Source {i+1}]: {chunk.get('content', '')}\n"
        
        prompt = f"""
        {self._get_system_prompt()}

        PROBLEM TO SOLVE:
        {json.dumps(parsed_problem, indent=2)}

        ROUTING DECISION:
        {json.dumps(routing_decision, indent=2)}

        {rag_text}

        Output JSON Schema:
        {{
            "problem_text": "string",
            "topic": "string",
            "steps": [
                {{
                    "step_number": integer,
                    "description": "string",
                    "calculation": "string or null",
                    "result": "string or null"
                }}
            ],
            "final_answer": "string",
            "method_used": "string",
            "confidence_score": float (0.0 to 1.0),
            "tools_used": ["string"],
            "rag_sources_used": ["string"],
            "needs_verification": boolean
        }}
        """
        return prompt

    def _use_calculator(self, expression: str) -> Optional[str]:
        """Use Python calculator for numerical expressions"""
        result = self.calculator.calculate(expression)
        if result["success"]:
            return result["result"]
        return None

    async def solve(
        self, 
        parsed_problem: dict, 
        routing_decision: dict, 
        rag_context: List[dict] = []
    ) -> SolverOutput:
        """
        Main solve method that orchestrates the solution process.
        """
        prompt = self._build_prompt(parsed_problem, routing_decision, rag_context)
        
        try:
            response = self.model.generate_content(prompt)
            text_response = response.text
            
            # Clean markdown code blocks if present
            if text_response.startswith("```"):
                text_response = text_response.split("```")[1]
                if text_response.startswith("json"):
                    text_response = text_response[4:]
            text_response = text_response.strip()

            # Parse and validate JSON
            solution_data = json.loads(text_response)
            
            # Track tools used
            if rag_context:
                solution_data.setdefault("tools_used", []).append("rag_context")
            if solution_data.get("confidence_score", 1.0) < 0.7:
                solution_data["needs_verification"] = True
            
            return SolverOutput(**solution_data)

        except Exception as e:
            # Fallback: Return error state that triggers HITL
            return SolverOutput(
                problem_text=parsed_problem.get("problem_text", ""),
                topic=parsed_problem.get("topic", "General Math"),
                steps=[
                    SolutionStep(
                        step_number=1,
                        description="Solver encountered an error",
                        calculation=None,
                        result=str(e)
                    )
                ],
                final_answer="Unable to solve",
                method_used="error",
                confidence_score=0.3,
                tools_used=[],
                rag_sources_used=[],
                needs_verification=True
            )

# 4. Singleton Instance for easy import
solver_agent = SolverAgent()