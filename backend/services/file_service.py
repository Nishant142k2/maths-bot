# backend/services/file_service.py

import uuid
from typing import Optional, Dict, Any
from core.supabase_client import supabase

class FileService:
    """Service for handling file uploads to Supabase Storage"""
    
    ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    ALLOWED_AUDIO_TYPES = ["audio/mp3", "audio/wav", "audio/mpeg", "audio/webm"]
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Upload file to Supabase Storage.
        Returns public URL and metadata.
        """
        try:
            # Validate file type
            if not self._validate_content_type(content_type):
                return {
                    "success": False,
                    "error": f"Invalid file type: {content_type}",
                    "url": None
                }
            
            # Validate file size
            if len(file_bytes) > self.MAX_FILE_SIZE:
                return {
                    "success": False,
                    "error": f"File too large. Max size: {self.MAX_FILE_SIZE / 1024 / 1024}MB",
                    "url": None
                }
            
            # Generate unique path
            extension = filename.split(".")[-1] if "." in filename else "bin"
            unique_filename = f"{session_id}_{uuid.uuid4()}.{extension}"
            
            # Determine bucket and path based on content type
            if content_type.startswith("image/"):
                bucket = "uploads"
                path = f"images/{unique_filename}"
                media_type = "image"
            elif content_type.startswith("audio/"):
                bucket = "uploads"
                path = f"audio/{unique_filename}"
                media_type = "audio"
            else:
                bucket = "uploads"
                path = f"misc/{unique_filename}"
                media_type = "misc"
            
            # Upload to Supabase Storage
            supabase.storage.from_(bucket).upload(path, file_bytes)
            
            # Get public URL
            public_url = supabase.storage.from_(bucket).get_public_url(path)
            
            return {
                "success": True,
                "url": public_url,
                "path": path,
                "media_type": media_type,
                "filename": unique_filename,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": None,
                "path": None,
                "media_type": None,
                "filename": None
            }

    def _validate_content_type(self, content_type: str) -> bool:
        """Validate file content type"""
        allowed = self.ALLOWED_IMAGE_TYPES + self.ALLOWED_AUDIO_TYPES
        return content_type.lower() in allowed

    async def delete_file(self, path: str) -> bool:
        """Delete file from Supabase Storage"""
        try:
            supabase.storage.from_("uploads").remove([path])
            return True
        except Exception:
            return False

    def get_file_url(self, path: str) -> str:
        """Get public URL for a file"""
        return supabase.storage.from_("uploads").get_public_url(path)

# Singleton instance
file_service = FileService()