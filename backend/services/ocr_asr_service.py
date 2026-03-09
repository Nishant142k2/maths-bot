# backend/app/services/ocr_asr_service.py

import base64
import google.generativeai as genai
from typing import Optional, Dict, Any, Tuple
from core.config import settings
from core.supabase_client import supabase
import io

class OCRASRService:
    """Service for handling OCR (image) and ASR (audio) processing"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash-lite')
        self.audio_model = genai.GenerativeModel('gemini-2.0-flash-lite')

    async def process_image(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Process image file for OCR extraction.
        Returns extracted text and confidence indicators.
        """
        try:
            # Upload to Supabase Storage first
            storage_path = f"uploads/images/{filename}"
            supabase.storage.from_("uploads").upload(storage_path, file_bytes)
            media_url = supabase.storage.from_("uploads").get_public_url(storage_path)
            
            # Prepare image for Gemini
            image_data = {
                "mime_type" : "image/png",
                "data" : file_bytes
            }
            
            # OCR Prompt - Extract text ONLY, don't solve
            prompt = """
            You are an OCR assistant for math problems.
            
            TASK: Extract ALL text from this image exactly as written.
            
            RULES:
            1. Do NOT solve the problem
            2. Do NOT add any interpretation
            3. Preserve mathematical notation (e.g., x², √, ∫, Σ)
            4. If text is unclear, use [UNCLEAR] marker
            5. Output ONLY the extracted text, nothing else
            
            COMMON MATH PHRASES TO RECOGNIZE:
            - "square root of" → √
            - "raised to the power" → ^
            - "integral of" → ∫
            - "sum of" → Σ
            - "fraction" → use / notation
            
            Extracted Text:
            """
            
            response = self.vision_model.generate_content([prompt, image_data])
            extracted_text = response.text.strip()
            
            # Calculate confidence heuristics
            confidence = self._calculate_ocr_confidence(extracted_text)
            
            return {
                "success": True,
                "media_url": media_url,
                "media_type": "image",
                "extracted_text": extracted_text,
                "confidence": confidence,
                "needs_review": confidence < 0.7,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "media_url": None,
                "media_type": "image",
                "extracted_text": "",
                "confidence": 0.0,
                "needs_review": True,
                "error": str(e)
            }

    async def process_audio(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Process audio file for speech-to-text transcription.
        Returns transcript and confidence indicators.
        """
        try:
            # Upload to Supabase Storage first
            storage_path = f"uploads/audio/{filename}"
            supabase.storage.from_("uploads").upload(storage_path, file_bytes)
            media_url = supabase.storage.from_("uploads").get_public_url(storage_path)
            
            # Prepare audio for Gemini
            audio_data = {
                "mime_type" : "audio/wav",
                "data" : file_bytes
            }
            
            # ASR Prompt - Transcribe math speech accurately
            prompt = """
            You are a speech-to-text assistant for math problems.
            
            TASK: Transcribe the spoken math question exactly.
            
            RULES:
            1. Do NOT solve the problem
            2. Convert spoken math terms to written notation:
               - "x squared" → x²
               - "square root of x" → √x
               - "x raised to the power of 2" → x^2
               - "integral from a to b" → ∫[a to b]
               - "sum from i equals 1 to n" → Σ(i=1 to n)
            3. If audio is unclear, use [UNCLEAR] marker
            4. Output ONLY the transcribed text, nothing else
            
            Transcribed Text:
            """
            
            response = self.audio_model.generate_content([prompt, audio_data])
            transcript = response.text.strip()
            
            # Calculate confidence heuristics
            confidence = self._calculate_asr_confidence(transcript)
            
            return {
                "success": True,
                "media_url": media_url,
                "media_type": "audio",
                "extracted_text": transcript,
                "confidence": confidence,
                "needs_review": confidence < 0.7,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "media_url": None,
                "media_type": "audio",
                "extracted_text": "",
                "confidence": 0.0,
                "needs_review": True,
                "error": str(e)
            }

    def _calculate_ocr_confidence(self, text: str) -> float:
        """
        Heuristic confidence calculation for OCR output.
        Gemini doesn't provide explicit confidence scores.
        """
        if not text or len(text) < 5:
            return 0.2
        
        # Penalize unclear markers
        unclear_count = text.upper().count("[UNCLEAR]")
        if unclear_count > 0:
            return max(0.3, 0.8 - (unclear_count * 0.15))
        
        # Penalize very short responses
        if len(text) < 20:
            return 0.5
        
        # Penalize excessive question marks or garbage
        garbage_ratio = text.count("???") / max(1, len(text))
        if garbage_ratio > 0.1:
            return 0.4
        
        # Base confidence for clean text
        return 0.85

    def _calculate_asr_confidence(self, text: str) -> float:
        """
        Heuristic confidence calculation for ASR output.
        """
        if not text or len(text) < 5:
            return 0.2
        
        # Penalize unclear markers
        unclear_count = text.upper().count("[UNCLEAR]")
        if unclear_count > 0:
            return max(0.3, 0.8 - (unclear_count * 0.15))
        
        # Penalize very short responses
        if len(text) < 15:
            return 0.5
        
        # Check for math-specific terms (good sign)
        math_terms = ["x", "y", "z", "sqrt", "integral", "derivative", "equation", "solve", "find"]
        has_math_terms = any(term in text.lower() for term in math_terms)
        
        if has_math_terms:
            return 0.85
        
        return 0.6

# Singleton instance
ocr_asr_service = OCRASRService()