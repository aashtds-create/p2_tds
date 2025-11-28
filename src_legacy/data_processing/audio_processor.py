"""
Audio processing handler
Uses Gemini Audio API for transcription (fast, reliable, no extra dependencies)
"""
import httpx
import logging
import os
import base64
import asyncio
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Rate limit handling
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 5  # seconds

class AudioProcessor:
    """
    Handles audio processing tasks (transcription, analysis)
    Uses Gemini Audio API - same API key as text processing
    """
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    async def process(self, url: str) -> Dict[str, Any]:
        """
        Download and transcribe audio file
        
        Args:
            url: Audio file URL
            
        Returns:
            Transcription text and metadata
        """
        try:
            logger.info(f"Downloading audio from {url}")
            
            # Download audio file
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                audio_bytes = response.content
            
            logger.info(f"Downloaded {len(audio_bytes)} bytes of audio")
            
            # Transcribe using Gemini
            if not self.gemini_api_key:
                logger.error("GEMINI_API_KEY not set!")
                return {"text": "", "error": "GEMINI_API_KEY not configured"}
            
            try:
                transcription = await self._transcribe_with_gemini(audio_bytes, url)
                logger.info(f"Transcription successful. Length: {len(transcription)} chars")
                logger.info(f"Transcription: {transcription[:200]}...")
                
                return {
                    "text": transcription,
                    "source": url,
                    "method": "gemini_audio"
                }
            except Exception as e:
                logger.error(f"Gemini transcription failed: {e}")
                return {"text": "", "error": str(e)}
            
        except Exception as e:
            logger.error(f"Audio processing failed for {url}: {e}")
            return {"text": "", "error": str(e)}
    
    async def _transcribe_with_gemini(self, audio_bytes: bytes, audio_url: str) -> str:
        """
        Transcribe audio using Gemini's multimodal API
        Supports: MP3, M4A, WAV, OPUS, OGG formats
        """
        # Detect MIME type from URL
        mime_type = "audio/mpeg"  # default
        if audio_url:
            if audio_url.endswith('.opus'):
                mime_type = "audio/opus"
            elif audio_url.endswith('.wav'):
                mime_type = "audio/wav"
            elif audio_url.endswith('.m4a'):
                mime_type = "audio/mp4"
            elif audio_url.endswith('.ogg'):
                mime_type = "audio/ogg"
            elif audio_url.endswith('.mp3'):
                mime_type = "audio/mpeg"
        
        logger.info(f"Using Gemini for audio transcription (MIME: {mime_type})")
        
        # Encode audio as base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Prepare Gemini API request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_api_key}"
        
        payload = {
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": audio_base64
                        }
                    },
                    {
                        "text": "Please transcribe this audio file. Return only the transcribed text, nothing else."
                    }
                ]
            }]
        }
        
        # Retry logic with exponential backoff
        for attempt in range(MAX_RETRIES):
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_delay = INITIAL_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Rate limited (429). Retrying in {retry_delay}s... (attempt {attempt + 1}/{MAX_RETRIES})")
                    await asyncio.sleep(retry_delay)
                    continue
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Gemini API error {response.status_code}: {error_detail}")
                    raise Exception(f"Gemini API returned {response.status_code}")
                
                result = response.json()
                
                # Extract transcription from response
                if "candidates" in result and result["candidates"]:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if parts and "text" in parts[0]:
                            return parts[0]["text"].strip()
                
                logger.error(f"Unexpected Gemini response format: {result}")
                raise Exception("Could not extract transcription from Gemini response")
        
        raise Exception(f"Gemini transcription failed after {MAX_RETRIES} retries")
