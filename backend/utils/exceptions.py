# backend/utils/exceptions.py

class MathMentorException(Exception):
    """Base exception for Math Mentor application"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class OCRException(MathMentorException):
    """OCR processing failed"""
    def __init__(self, message: str = "OCR processing failed"):
        super().__init__(message, status_code=400)

class ASRException(MathMentorException):
    """ASR processing failed"""
    def __init__(self, message: str = "Audio transcription failed"):
        super().__init__(message, status_code=400)

class RAGException(MathMentorException):
    """RAG retrieval failed"""
    def __init__(self, message: str = "Knowledge retrieval failed"):
        super().__init__(message, status_code=500)

class AgentException(MathMentorException):
    """Agent processing failed"""
    def __init__(self, message: str = "Agent processing failed"):
        super().__init__(message, status_code=500)

class HITLException(MathMentorException):
    """HITL workflow error"""
    def __init__(self, message: str = "HITL workflow error"):
        super().__init__(message, status_code=400)

class SessionNotFoundException(MathMentorException):
    """Session not found"""
    def __init__(self, session_id: str):
        super().__init__(f"Session {session_id} not found", status_code=404)

class ValidationException(MathMentorException):
    """Input validation failed"""
    def __init__(self, message: str = "Invalid input"):
        super().__init__(message, status_code=400)