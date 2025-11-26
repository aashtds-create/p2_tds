"""
Audio processing handler
Supports multiple transcription backends
"""
import httpx
import logging
import os
import tempfile
import base64
from typing import Any, Dict

logger = logging.getLogger(__name__)

class AudioProcessor:
    """
    Handles audio processing tasks (transcription, analysis)
    Supports multiple backends in order of preference:
    1. Gemini Audio API (multimodal, same API key as text processing)
    2. SpeechRecognition + Google (free, no API key)
    3. Local Whisper (fallback, slower but accurate)
    """
    
    def __init__(self):
        # Gemini API for audio transcription
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
            
            # Try transcription methods in order of preference
            transcription = None
            method = None
            
            # Method 1: Gemini Audio API (Primary - multimodal, same API key)
            if self.gemini_api_key:
                try:
                    transcription = await self._transcribe_with_gemini(audio_bytes, url)
                    method = "gemini_audio"
                    logger.info("Transcribed using Gemini Audio API")
                except Exception as e:
                    logger.warning(f"Gemini transcription failed: {e}, trying alternatives...")
            
            # Method 2: SpeechRecognition (Free fallback - Google Web Speech)
            if not transcription:
                try:
                    transcription = await self._transcribe_with_speech_recognition(audio_bytes)
                    method = "speech_recognition"
                    logger.info("Transcribed using SpeechRecognition (Google)")
                except ImportError:
                    logger.info("SpeechRecognition not available, trying local Whisper...")
                except Exception as e:
                    logger.warning(f"SpeechRecognition failed: {e}")
            
            # Method 3: Local Whisper (Last resort fallback)
            if not transcription:
                try:
                    transcription = await self._transcribe_with_local_whisper(audio_bytes)
                    method = "local_whisper"
                    logger.info("Transcribed using local Whisper model")
                except ImportError:
                    logger.info("Local Whisper not available")
                except Exception as e:
                    logger.warning(f"Local Whisper failed: {e}")
            
            if not transcription:
                logger.error("All transcription methods failed")
                return {"text": "", "error": "No transcription backend available"}
            
            logger.info(f"Transcription successful. Length: {len(transcription)} chars")
            logger.info(f"Transcription preview: {transcription[:200]}...")
            
            return {
                "text": transcription,
                "source": url,
                "method": method
            }
            
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
        
        # Prepare Gemini API request (use same model as text processing)
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
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            
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
    
    async def _transcribe_with_speech_recognition(self, audio_bytes: bytes) -> str:
        """
        Transcribe using SpeechRecognition library (FREE, NO API KEY!)
        Install: pip install SpeechRecognition pydub
        """
        import speech_recognition as sr
        from pydub import AudioSegment
        import io
        
        # Convert audio to WAV format (required by SpeechRecognition)
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        
        # Export to WAV in temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            audio.export(tmp_file.name, format="wav")
            tmp_path = tmp_file.name
        
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(tmp_path) as source:
                audio_data = recognizer.record(source)
                # Use Google Web Speech API (FREE, no key needed)
                text = recognizer.recognize_google(audio_data)
                return text
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    async def _transcribe_with_local_whisper(self, audio_bytes: bytes) -> str:
        """
        Transcribe using local Whisper model (NO API KEY NEEDED!)
        Install: pip install openai-whisper
        """
        import whisper
        
        # Save audio to temp file (Whisper needs a file path)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Load model (use 'base' for speed, 'small/medium/large' for accuracy)
            model = whisper.load_model("base")
            
            # Transcribe
            result = model.transcribe(tmp_path)
            return result["text"]
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
