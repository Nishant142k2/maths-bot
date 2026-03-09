# backend/app/utils/formatters.py

import re
from typing import Dict, Any

class MathFormatters:
    """Mathematical text formatting utilities"""
    
    @staticmethod
    def format_latex(text: str) -> str:
        """
        Convert plain math notation to LaTeX format.
        """
        # Replace common patterns
        text = re.sub(r'x\^(\d+)', r'x^{\1}', text)
        text = re.sub(r'sqrt\(([^)]+)\)', r'\\sqrt{\1}', text)
        text = re.sub(r'frac{([^}]+)}{([^}]+)}', r'\\frac{\1}{\2}', text)
        
        return text

    @staticmethod
    def format_for_display(solution: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format solution data for frontend display.
        """
        formatted = {
            "final_answer": solution.get("final_answer", ""),
            "steps": [],
            "confidence": solution.get("confidence_score", 0.0),
            "method": solution.get("method_used", "")
        }
        
        # Format steps for display
        for step in solution.get("steps", []):
            formatted["steps"].append({
                "number": step.get("step_number"),
                "description": step.get("description"),
                "calculation": step.get("calculation"),
                "result": step.get("result")
            })
        
        return formatted

    @staticmethod
    def format_agent_trace(trace: list) -> list:
        """
        Format agent trace for UI display.
        """
        formatted_trace = []
        for entry in trace:
            formatted_trace.append({
                "agent": entry.get("agent_name"),
                "timestamp": entry.get("timestamp"),
                "status": entry.get("status"),
                "confidence": entry.get("confidence"),
                "summary": str(entry.get("details", {}))[:100]  # Truncate for display
            })
        
        return formatted_trace

    @staticmethod
    def format_error_message(error: Exception, context: str = "") -> str:
        """
        Format error message for user-friendly display.
        """
        error_str = str(error)
        
        # Hide sensitive information
        sensitive_patterns = ["api_key", "token", "password", "secret"]
        for pattern in sensitive_patterns:
            if pattern.lower() in error_str.lower():
                error_str = "An internal error occurred"
                break
        
        if context:
            return f"{context}: {error_str}"
        
        return error_str

# Singleton for easy import
formatters = MathFormatters()