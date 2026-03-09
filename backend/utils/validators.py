# backend/app/utils/validators.py

import re
from typing import Optional, Tuple

class InputValidators:
    """Input validation utilities"""
    
    @staticmethod
    def validate_math_text(text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that text appears to be a math problem.
        Returns (is_valid, error_message)
        """
        if not text or len(text.strip()) < 5:
            return False, "Input text is too short"
        
        if len(text) > 5000:
            return False, "Input text is too long (max 5000 characters)"
        
        # Check for math-related keywords
        math_keywords = [
            "solve", "find", "calculate", "equation", "function",
            "derivative", "integral", "probability", "algebra",
            "x", "y", "z", "=", "+", "-", "*", "/", "^"
        ]
        
        has_math_content = any(keyword in text.lower() for keyword in math_keywords)
        
        if not has_math_content:
            return False, "Input does not appear to be a math problem"
        
        return True, None

    @staticmethod
    def validate_session_id(session_id: str) -> Tuple[bool, Optional[str]]:
        """Validate UUID session ID format"""
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        
        if not uuid_pattern.match(session_id):
            return False, "Invalid session ID format"
        
        return True, None

    @staticmethod
    def validate_hitl_decision(decision: str) -> Tuple[bool, Optional[str]]:
        """Validate HITL decision value"""
        allowed = ["approve", "reject", "correct"]
        
        if decision.lower() not in allowed:
            return False, f"Invalid decision. Must be one of: {allowed}"
        
        return True, None

    @staticmethod
    def validate_file_type(content_type: str) -> Tuple[bool, Optional[str]]:
        """Validate file content type"""
        allowed = [
            "image/jpeg", "image/jpg", "image/png", "image/webp",
            "audio/mp3", "audio/wav", "audio/mpeg", "audio/webm"
        ]
        
        if content_type.lower() not in allowed:
            return False, f"Invalid file type. Allowed: {allowed}"
        
        return True, None

# Singleton for easy import
validators = InputValidators()