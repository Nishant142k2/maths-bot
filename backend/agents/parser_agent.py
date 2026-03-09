import google.generativeai as genai
import json 
from pydantic import BaseModel , Field
from typing import List , Optional
from core.config import settings 

class ParsedProblem(BaseModel) : 
    problem_text : str = Field(... , description="The clean standarized text of the math problem " )
    topic : str = Field(... , description="One of : Algebra , Probablity , Calculus , Linear Algebra , General Math") 
    variables : List[str] = Field(default_factory= list , description="Any Constraints e.g., ['x > 0', 'integer only']).") 
    needs_clarification: bool = Field(..., description="True if information is missing, ambiguous, or out of scope.") 
    ambiguity_reason: Optional[str] = Field(None, description="Explanation of why clarification is needed.")  
    
class ParserAgent : 
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY) 
        self.model = genai.GenerativeModel('gemini-1.5 flash') 
    
    def _get_system_prompt(self) -> str :
        return  """
        You are an expert Math Problem Parser for a JEE-style tutoring system.
        Your goal is to convert raw text into a structured JSON format.
        
        SCOPE LIMITATIONS:
        - Only support: Algebra, Probability, Basic Calculus (limits, derivatives, optimization), Linear Algebra.
        - If the problem is outside this scope (e.g., History, Physics, Complex Geometry), set needs_clarification=true.
        
        INSTRUCTIONS:
        1. Clean any OCR/ASR noise (e.g., fix '1ook' to 'look', 'x²' to 'x^2').
        2. Identify variables and constraints explicitly.
        3. Detect Ambiguity: If the problem lacks necessary data to solve (e.g., "Find x" without an equation), set needs_clarification=true.
        4. Output ONLY valid JSON. No markdown formatting.
        """ 
    async def parse(self, raw_text: str) -> ParsedProblem:
        """
        Takes confirmed OCR/ASR text and returns structured problem data.
        """
        prompt = f"""
           {self._get_system_prompt()} 
           Raw Input Text : 
           "{raw_text}"  
           Output JSON Schema : 
           {{
           "problem_text" : "string" ,
           "topic" : "string ,
           "variables": ["string"],
           "constraints": ["string"],
           "needs_clarification": boolean,
           "ambiguity_reason": "string or null"
           }}      
        """ 
        try : 
            response = self.model.generate_content(prompt) 
            text_response = text_response.split("```") 

            #Clean Markdown 
            if text_response.startswith("```") : 
                text_response = text_response.split("```")[1]
                if text_response.startswith("json"):
                    text_response = text_response[4:]
            text_response = text_response.strip()
            parsed_data = json.loads(text_response) 
            return ParsedProblem(**parsed_data) 

        except Exception as e :
            # Fallback if LLM fails or returns invalid JSON
            # In production, you might retry. Here we return a safe default that triggers HITL.
            return ParsedProblem(
                problem_text=raw_text,
                topic="General Math",
                variables=[],
                constraints=[],
                needs_clarification=True,
                ambiguity_reason=f"Parser failed to structure input: {str(e)}"
            )
parser_agent = ParserAgent()