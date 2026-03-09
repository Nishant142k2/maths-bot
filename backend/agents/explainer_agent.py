import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from core.config import settings

# 1. Define the Explanation Output Model
class ExplanationSection(BaseModel):
    section_title: str = Field(..., description="Title of this explanation section")
    content: str = Field(..., description="Educational content for this section")
    key_takeaways: List[str] = Field(default_factory=list, description="Important points to remember")

class ExplainerOutput(BaseModel):
    introduction: str = Field(..., description="Friendly introduction to the problem type")
    concept_review: str = Field(..., description="Brief review of relevant mathematical concepts")
    step_by_step_explanation: List[ExplanationSection] = Field(..., description="Detailed walkthrough of each solution step")
    common_mistakes: List[str] = Field(default_factory=list, description="Common pitfalls students make on this type of problem")
    practice_tips: List[str] = Field(default_factory=list, description="Tips for solving similar problems")
    final_summary: str = Field(..., description="Concise summary of the solution")
    difficulty_level: str = Field(..., description="Problem difficulty: Easy, Medium, or Hard")
    estimated_time: str = Field(..., description="Estimated time to solve (e.g., '3-5 minutes')")
    related_topics: List[str] = Field(default_factory=list, description="Topics to study for similar problems")
    confidence_indicator: float = Field(..., description="Overall confidence in explanation quality (0.0 to 1.0)")
    student_friendly: bool = Field(..., description="Whether explanation is appropriate for JEE students")

# 2. Define the Explainer Agent Class
class ExplainerAgent:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Using gemini-1.5-flash for speed (can use pro for more detailed explanations)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def _get_system_prompt(self) -> str:
        return """
        You are an expert JEE Math Tutor/Explainer AI.
        Your goal is to transform verified mathematical solutions into CLEAR, EDUCATIONAL explanations.

        TEACHING PRINCIPLES:
        1. **Start Simple**: Begin with intuition before formal math
        2. **Show Why, Not Just How**: Explain the reasoning behind each step
        3. **Use Analogies**: When helpful, use real-world analogies
        4. **Highlight Key Concepts**: Bold important formulas and theorems
        5. **Warn About Pitfalls**: Point out common mistakes students make
        6. **Encourage Practice**: Provide tips for mastering similar problems
        7. **Age-Appropriate**: Write for JEE aspirants (16-18 years old)
        8. **No Condescension**: Be supportive and encouraging

        EXPLANATION STRUCTURE:
        1. Introduction: What type of problem is this?
        2. Concept Review: What math concepts are needed?
        3. Step-by-Step: Walk through each solution step with reasoning
        4. Common Mistakes: What do students usually get wrong?
        5. Practice Tips: How to get better at this problem type?
        6. Summary: Quick recap of the solution

        TONE:
        - Friendly and encouraging
        - Clear and precise
        - Educational, not just informative
        - JEE-focused (exam preparation context)

        Output ONLY valid JSON. No markdown formatting.
        """

    def _build_prompt(
        self,
        parsed_problem: dict,
        solution: dict,
        verification: dict,
        routing_decision: dict,
        rag_context: List[dict] = []
    ) -> str:
        """Build the complete explanation prompt"""
        
        rag_text = ""
        if rag_context:
            rag_text = "\n\nRETRIEVED KNOWLEDGE FOR REFERENCE:\n"
            for i, chunk in enumerate(rag_context):
                rag_text += f"[Source {i+1}]: {chunk.get('content', '')}\n"

        prompt = f"""
        {self._get_system_prompt()}

        ORIGINAL PROBLEM:
        {json.dumps(parsed_problem, indent=2)}

        VERIFIED SOLUTION:
        {json.dumps(solution, indent=2)}

        VERIFICATION RESULTS:
        {json.dumps(verification, indent=2)}

        ROUTING DECISION:
        {json.dumps(routing_decision, indent=2)}

        {rag_text}

        Output JSON Schema:
        {{
            "introduction": "string",
            "concept_review": "string",
            "step_by_step_explanation": [
                {{
                    "section_title": "string",
                    "content": "string",
                    "key_takeaways": ["string"]
                }}
            ],
            "common_mistakes": ["string"],
            "practice_tips": ["string"],
            "final_summary": "string",
            "difficulty_level": "string (Easy/Medium/Hard)",
            "estimated_time": "string",
            "related_topics": ["string"],
            "confidence_indicator": float (0.0 to 1.0),
            "student_friendly": boolean
        }}
        """
        return prompt

    async def explain(
        self,
        parsed_problem: dict,
        solution: dict,
        verification: dict,
        routing_decision: dict,
        rag_context: List[dict] = []
    ) -> ExplainerOutput:
        """
        Main explanation method that creates student-friendly output.
        """
        prompt = self._build_prompt(
            parsed_problem,
            solution,
            verification,
            routing_decision,
            rag_context
        )
        
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
            explanation_data = json.loads(text_response)
            
            # Ensure student_friendly is True only if confidence is high
            if explanation_data.get("confidence_indicator", 1.0) < 0.8:
                explanation_data["student_friendly"] = False
            
            return ExplainerOutput(**explanation_data)

        except Exception as e:
            # Fallback: Return basic explanation that triggers HITL review
            return ExplainerOutput(
                introduction="We encountered an issue generating the full explanation.",
                concept_review="This problem requires careful review.",
                step_by_step_explanation=[
                    ExplanationSection(
                        section_title="Solution Review Needed",
                        content=f"The automated explanation failed: {str(e)}. Please review the solution manually.",
                        key_takeaways=["Manual review required"]
                    )
                ],
                common_mistakes=[],
                practice_tips=["Review the verified solution steps carefully"],
                final_summary=solution.get("final_answer", "Answer unavailable"),
                difficulty_level="Medium",
                estimated_time="5-10 minutes",
                related_topics=[parsed_problem.get("topic", "General Math")],
                confidence_indicator=0.5,
                student_friendly=False
            )

# 3. Singleton Instance for easy import
explainer_agent = ExplainerAgent()