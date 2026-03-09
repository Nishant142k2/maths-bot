import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from core.config import settings

# 1. Define the Verification Output Model
class VerificationCheck(BaseModel):
    check_name: str = Field(..., description="Name of the check (e.g., 'calculation', 'domain')")
    passed: bool = Field(..., description="Whether this check passed")
    details: str = Field(..., description="Explanation of the check result")
    severity: str = Field(..., description="Severity level: 'critical', 'warning', 'info'")

class VerifierOutput(BaseModel):
    solution_valid: bool = Field(..., description="Overall validity of the solution")
    correctness_score: float = Field(..., description="Confidence in correctness (0.0 to 1.0)")
    checks_performed: List[VerificationCheck] = Field(..., description="List of all verification checks")
    issues_found: List[str] = Field(default_factory=list, description="List of issues discovered")
    edge_cases_considered: List[str] = Field(default_factory=list, description="Edge cases that were checked")
    domain_constraints_met: bool = Field(..., description="Whether all domain constraints are satisfied")
    units_consistent: bool = Field(..., description="Whether units are consistent throughout")
    hitl_required: bool = Field(..., description="True if human review is needed")
    hitl_reason: Optional[str] = Field(None, description="Reason for HITL if required")
    suggested_corrections: List[str] = Field(default_factory=list, description="Suggested fixes for issues")
    verification_method: str = Field(..., description="Method used to verify (e.g., 'reverse_calculation', 'substitution')")

# 2. Define the Verifier Agent Class
class VerifierAgent:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Using gemini-1.5-pro for more careful verification (can use flash for speed)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def _get_system_prompt(self) -> str:
        return """
        You are an expert Math Verifier/Critic for a JEE tutoring system.
        Your role is to CRITICALLY evaluate solutions produced by the Solver Agent.

        VERIFICATION CHECKS TO PERFORM:
        1. **Calculation Accuracy**: Re-verify all numerical calculations
        2. **Domain Constraints**: Check if solution respects constraints (e.g., x > 0, integer only)
        3. **Units Consistency**: Ensure units are consistent throughout (if applicable)
        4. **Edge Cases**: Consider boundary conditions, division by zero, negative roots, etc.
        5. **Logical Flow**: Verify each step logically follows from the previous
        6. **Answer Format**: Check if final answer is properly boxed and formatted
        7. **Method Appropriateness**: Verify the solving method matches the problem type

        HITL TRIGGER CONDITIONS:
        - Correctness score below 0.7
        - Any 'critical' severity check fails
        - Domain constraints violated
        - Multiple calculation errors found
        - Ambiguous or multiple valid answers possible
        - Complex problem with high stakes (JEE-level)

        SEVERITY LEVELS:
        - 'critical': Solution is wrong or unsafe to present
        - 'warning': Minor issues but solution is usable
        - 'info': Observations that don't affect correctness

        Output ONLY valid JSON. No markdown formatting.
        """

    def _build_prompt(
        self, 
        parsed_problem: dict, 
        solution: dict, 
        routing_decision: dict,
        rag_context: List[dict] = []
    ) -> str:
        """Build the complete verification prompt"""
        
        rag_text = ""
        if rag_context:
            rag_text = "\n\nRETRIEVED CONTEXT FOR REFERENCE:\n"
            for i, chunk in enumerate(rag_context):
                rag_text += f"[Source {i+1}]: {chunk.get('content', '')}\n"

        prompt = f"""
        {self._get_system_prompt()}

        ORIGINAL PROBLEM:
        {json.dumps(parsed_problem, indent=2)}

        SOLVER'S SOLUTION:
        {json.dumps(solution, indent=2)}

        ROUTING DECISION:
        {json.dumps(routing_decision, indent=2)}

        {rag_text}

        Output JSON Schema:
        {{
            "solution_valid": boolean,
            "correctness_score": float (0.0 to 1.0),
            "checks_performed": [
                {{
                    "check_name": "string",
                    "passed": boolean,
                    "details": "string",
                    "severity": "string (critical/warning/info)"
                }}
            ],
            "issues_found": ["string"],
            "edge_cases_considered": ["string"],
            "domain_constraints_met": boolean,
            "units_consistent": boolean,
            "hitl_required": boolean,
            "hitl_reason": "string or null",
            "suggested_corrections": ["string"],
            "verification_method": "string"
        }}
        """
        return prompt

    async def verify(
        self,
        parsed_problem: dict,
        solution: dict,
        routing_decision: dict,
        rag_context: List[dict] = []
    ) -> VerifierOutput:
        """
        Main verification method that evaluates the solver's output.
        """
        prompt = self._build_prompt(parsed_problem, solution, routing_decision, rag_context)
        
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
            verification_data = json.loads(text_response)
            
            # Enforce HITL threshold from settings
            if verification_data.get("correctness_score", 1.0) < settings.HITL_CONFIDENCE_THRESHOLD:
                verification_data["hitl_required"] = True
                if not verification_data.get("hitl_reason"):
                    verification_data["hitl_reason"] = f"Correctness score {verification_data['correctness_score']} below threshold {settings.HITL_CONFIDENCE_THRESHOLD}"
            
            # Check for critical failures
            checks = verification_data.get("checks_performed", [])
            critical_failures = [c for c in checks if c.get("severity") == "critical" and not c.get("passed")]
            if critical_failures:
                verification_data["hitl_required"] = True
                verification_data["hitl_reason"] = f"Critical verification failures: {len(critical_failures)} check(s) failed"
            
            return VerifierOutput(**verification_data)

        except Exception as e:
            # Fallback: Conservative approach - trigger HITL on error
            return VerifierOutput(
                solution_valid=False,
                correctness_score=0.3,
                checks_performed=[
                    VerificationCheck(
                        check_name="verification_process",
                        passed=False,
                        details=f"Verifier encountered error: {str(e)}",
                        severity="critical"
                    )
                ],
                issues_found=[f"Verification failed: {str(e)}"],
                edge_cases_considered=[],
                domain_constraints_met=False,
                units_consistent=False,
                hitl_required=True,
                hitl_reason=f"Verifier agent error: {str(e)}",
                suggested_corrections=["Manual review required"],
                verification_method="error"
            )

# 3. Singleton Instance for easy import
verifier_agent = VerifierAgent()