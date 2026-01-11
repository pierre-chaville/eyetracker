"""
Text-to-Speech service for generating audio from text.
Supports multiple TTS providers.
"""
import os
import io
import base64
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class TTSService:
    """Service for text-to-speech conversion"""
    
    def __init__(self, provider: str = "pyttsx3"):
        """
        Initialize TTS service.
        
        Args:
            provider: "pyttsx3" (offline) or "openai" (requires API key)
        """
        self.provider = provider.lower()
        self._engine = None
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine"""
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            # Set properties for better quality
            self._engine.setProperty('rate', 150)  # Speed of speech
            self._engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
        except ImportError:
            raise ValueError("pyttsx3 is not installed. Install it with: pip install pyttsx3")
    
    def generate_speech(self, text: str, language: str = "en") -> Optional[bytes]:
        """
        Generate speech audio from text.
        
        Args:
            text: Text to convert to speech
            language: Language code (e.g., "en", "fr")
        
        Returns:
            Audio data as bytes (WAV format), or None if generation fails
        """
        if not text or not text.strip():
            return None
        
        if self.provider == "pyttsx3":
            return self._generate_with_pyttsx3(text)
        elif self.provider == "openai":
            return self._generate_with_openai(text, language)
        else:
            raise ValueError(f"Unsupported TTS provider: {self.provider}")
    
    def _generate_with_pyttsx3(self, text: str) -> Optional[bytes]:
        """Generate speech using pyttsx3 (offline)"""
        try:
            if self._engine is None:
                self._init_pyttsx3()
            
            # Save to in-memory buffer
            import tempfile
            import wave
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            try:
                self._engine.save_to_file(text, tmp_path)
                self._engine.runAndWait()
                
                # Read the generated audio file
                with open(tmp_path, 'rb') as f:
                    audio_data = f.read()
                
                return audio_data
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        
        except Exception as e:
            print(f"Error generating speech with pyttsx3: {e}")
            return None
    
    def _generate_with_openai(self, text: str, language: str = "en") -> Optional[bytes]:
        """Generate speech using OpenAI TTS API"""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            
            client = OpenAI(api_key=api_key)
            
            # Map language to voice (OpenAI supports: alloy, echo, fable, onyx, nova, shimmer)
            # Use different voices for different languages if needed
            voice = "nova"  # Default voice
            
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="wav"
            )
            
            # Read audio data
            audio_data = response.content
            return audio_data
        
        except ImportError:
            raise ValueError("openai package is not installed. Install it with: pip install openai")
        except Exception as e:
            print(f"Error generating speech with OpenAI: {e}")
            return None
    
    def generate_speech_base64(self, text: str, language: str = "en") -> Optional[str]:
        """
        Generate speech and return as base64-encoded string.
        
        Args:
            text: Text to convert to speech
            language: Language code
        
        Returns:
            Base64-encoded audio data, or None if generation fails
        """
        audio_data = self.generate_speech(text, language)
        if audio_data:
            return base64.b64encode(audio_data).decode('utf-8')
        return None


# Global TTS service instance
_tts_service: Optional[TTSService] = None


def get_tts_service(provider: str = "pyttsx3") -> TTSService:
    """Get or create the global TTS service instance"""
    global _tts_service
    
    if _tts_service is None or _tts_service.provider != provider.lower():
        _tts_service = TTSService(provider=provider)
    
    return _tts_service

