"""
Text-to-Speech service for generating audio from text.
Supports multiple TTS providers.
"""
import os
import io
import base64
import threading
import tempfile
import hashlib
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class TTSService:
    """Service for text-to-speech conversion"""
    
    def __init__(self, provider: str = "pyttsx3", cache_enabled: bool = True):
        """
        Initialize TTS service.
        
        Args:
            provider: "pyttsx3" (offline), "openai" (requires API key), "elevenlabs" (requires API key), or "google" (requires API key)
            cache_enabled: Whether to enable filesystem caching for TTS audio
        """
        print(f"--> Initializing TTS service with provider: {provider}")
        self.provider = provider.lower()
        self._engine = None
        self.cache_enabled = cache_enabled
        
        # Set up cache directory
        if self.cache_enabled:
            backend_dir = Path(__file__).parent
            self.cache_dir = backend_dir / "tts_cache"
            self.cache_dir.mkdir(exist_ok=True)
            print(f"TTS Cache directory: {self.cache_dir}")
        else:
            self.cache_dir = None
    
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
    
    def _get_cache_key(self, text: str, language: str, voice_name: Optional[str], 
                       pitch: Optional[float], speaking_rate: Optional[float]) -> str:
        """
        Generate a cache key from text and TTS parameters.
        
        Args:
            text: Text to convert to speech
            language: Language code
            voice_name: Voice name (optional)
            pitch: Pitch adjustment (optional)
            speaking_rate: Speaking rate (optional)
        
        Returns:
            Cache key (filename-safe hash)
        """
        # Create a unique key from all parameters
        key_data = f"{self.provider}:{text}:{language}:{voice_name or 'default'}:{pitch or 0.0}:{speaking_rate or 1.0}"
        # Generate hash for consistent, filesystem-safe filename
        hash_obj = hashlib.sha256(key_data.encode('utf-8'))
        return hash_obj.hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the cache file path for a given cache key."""
        if not self.cache_dir:
            return None
        # Use first 2 characters of hash for subdirectory to avoid too many files in one directory
        subdir = self.cache_dir / cache_key[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{cache_key}.mp3"
    
    def _load_from_cache(self, cache_path: Path) -> Optional[bytes]:
        """Load audio data from cache file."""
        try:
            if cache_path and cache_path.exists():
                with open(cache_path, 'rb') as f:
                    audio_data = f.read()
                print(f"TTS Cache: Loaded from cache ({len(audio_data)} bytes)")
                return audio_data
        except Exception as e:
            print(f"TTS Cache: Error loading from cache: {e}")
        return None
    
    def _save_to_cache(self, cache_path: Path, audio_data: bytes) -> None:
        """Save audio data to cache file."""
        try:
            if cache_path and self.cache_enabled:
                with open(cache_path, 'wb') as f:
                    f.write(audio_data)
                print(f"TTS Cache: Saved to cache ({len(audio_data)} bytes)")
        except Exception as e:
            print(f"TTS Cache: Error saving to cache: {e}")
    
    def generate_speech(self, text: str, language: str = "fr", voice_name: Optional[str] = None, 
                       pitch: Optional[float] = None, speaking_rate: Optional[float] = None) -> Optional[bytes]:
        """
        Generate speech audio from text.
        
        Args:
            text: Text to convert to speech
            language: Language code (e.g., "en", "fr")
            voice_name: Voice name (optional, for Google TTS)
            pitch: Pitch adjustment (optional, for Google TTS)
            speaking_rate: Speaking rate (optional, for Google TTS)
        
        Returns:
            Audio data as bytes (MP3/WAV format), or None if generation fails
        """
        if not text or not text.strip():
            return None
        
        # Check cache first
        if self.cache_enabled:
            cache_key = self._get_cache_key(text, language, voice_name, pitch, speaking_rate)
            cache_path = self._get_cache_path(cache_key)
            cached_audio = self._load_from_cache(cache_path)
            if cached_audio:
                return cached_audio
        
        # Generate audio if not in cache
        audio_data = None
        if self.provider == "pyttsx3":
            audio_data = self._generate_with_pyttsx3(text)
        elif self.provider == "openai":
            audio_data = self._generate_with_openai(text, language)
        elif self.provider == "elevenlabs":
            audio_data = self._generate_with_elevenlabs(text, language)
        elif self.provider == "google":
            audio_data = self._generate_with_google(text, language, voice_name, pitch, speaking_rate)
        else:
            raise ValueError(f"Unsupported TTS provider: {self.provider}")
        
        # Save to cache if generation was successful
        if audio_data and self.cache_enabled:
            cache_key = self._get_cache_key(text, language, voice_name, pitch, speaking_rate)
            cache_path = self._get_cache_path(cache_key)
            self._save_to_cache(cache_path, audio_data)
        
        return audio_data
    
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
        except ImportError:
            raise ValueError("openai package is not installed. Install it with: pip install openai")
        except Exception as e:
            print(f"Error generating speech with OpenAI: {e}")
            return None
    
    def _generate_with_elevenlabs(self, text: str, language: str = "en") -> Optional[bytes]:
        """Generate speech using ElevenLabs API"""
        try:
            import requests
            
            api_key = os.getenv("ELEVEN_LABS_API_KEY")
            voice_id = os.getenv("ELEVEN_LABS_VOICE_ID")
            
            print(f"ElevenLabs TTS: API key present: {bool(api_key)}, Voice ID: {voice_id}")
            
            if not api_key:
                raise ValueError("ELEVEN_LABS_API_KEY environment variable is required")
            if not voice_id:
                raise ValueError("ELEVEN_LABS_VOICE_ID environment variable is required")
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            print(f"ElevenLabs TTS: Calling URL: {url}")
            print(f"ElevenLabs TTS: Text to convert: '{text}'")
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",  # Use multilingual model
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            print(f"ElevenLabs TTS: Response status code: {response.status_code}")
            
            response.raise_for_status()
            
            # ElevenLabs returns MP3 format by default
            audio_data = response.content
            print(f"ElevenLabs TTS: Received audio data, length: {len(audio_data)} bytes")
            return audio_data
        
        except ImportError:
            raise ValueError("requests package is not installed. Install it with: pip install requests")
        except requests.exceptions.RequestException as e:
            print(f"Error generating speech with ElevenLabs (RequestException): {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None
        except Exception as e:
            print(f"Error generating speech with ElevenLabs: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_with_google(self, text: str, language: str = "fr", voice_name: Optional[str] = None,
                             pitch: Optional[float] = None, speaking_rate: Optional[float] = None) -> Optional[bytes]:
        """Generate speech using Google Cloud Text-to-Speech API with service account"""
        try:
            from google.cloud import texttospeech
            
            # Set up service account credentials
            # Check if GOOGLE_APPLICATION_CREDENTIALS is set, otherwise use google.json in backend/
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not credentials_path:
                # Default to google.json in the backend directory
                backend_dir = Path(__file__).parent
                credentials_path = backend_dir / "google.json"
                if credentials_path.exists():
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)
                    print(f"Google TTS: Using service account from {credentials_path}")
                else:
                    raise ValueError(
                        "Google Cloud service account credentials not found. "
                        "Set GOOGLE_APPLICATION_CREDENTIALS environment variable or place google.json in backend/"
                    )
            
            print(f"Google TTS: Using credentials from {credentials_path}")
            print(f"Google TTS: Text to convert: '{text}'")
            print(f"Google TTS: Language: {language}")
            
            # Initialize the client (will automatically use GOOGLE_APPLICATION_CREDENTIALS)
            client = texttospeech.TextToSpeechClient()
            
            # Map language code to Google Cloud voice
            language_code_map = {
                "en": "en-US",
                "fr": "fr-FR",
                "es": "es-ES",
                "de": "de-DE",
                "it": "it-IT",
            }
            google_language = language_code_map.get(language, "en-US")
            
            # Use provided voice_name or select default voice based on language
            if not voice_name:
                voice_name_map = {
                    "en-US": "en-US-Standard-B",  # Neutral voice
                    "fr-FR": "fr-FR-Standard-B",
                    "es-ES": "es-ES-Standard-B",
                    "de-DE": "de-DE-Standard-B",
                    "it-IT": "it-IT-Standard-B",
                }
                voice_name = voice_name_map.get(google_language, "en-US-Standard-B")
            
            print(f"Google TTS: Voice: {voice_name}")
            
            # Set the text input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Build the voice request
            # Note: Some voices don't support NEUTRAL gender, so we'll omit it
            # Google Cloud TTS will use the default gender for the selected voice
            voice = texttospeech.VoiceSelectionParams(
                language_code=google_language,
                name=voice_name
            )
            
            # Use provided pitch and speaking_rate or defaults
            final_pitch = pitch if pitch is not None else 0.0
            final_speaking_rate = speaking_rate if speaking_rate is not None else 1.0
            
            # Validate ranges
            final_pitch = max(-20.0, min(20.0, final_pitch))
            final_speaking_rate = max(0.25, min(4.0, final_speaking_rate))
            
            print(f"Google TTS: Pitch: {final_pitch}, Speaking Rate: {final_speaking_rate}")
            
            # Select the type of audio file you want returned
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=final_speaking_rate,
                pitch=final_pitch,
                volume_gain_db=0.0
            )
            
            # Perform the text-to-speech request
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # The response's audio_content is binary
            audio_data = response.audio_content
            print(f"Google TTS: Received audio data, length: {len(audio_data)} bytes")
            return audio_data
        
        except ImportError:
            raise ValueError(
                "google-cloud-texttospeech package is not installed. "
                "Install it with: pip install google-cloud-texttospeech"
            )
        except Exception as e:
            print(f"Error generating speech with Google Cloud TTS: {e}")
            import traceback
            traceback.print_exc()
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
    
    def play_audio_async(self, audio_data: bytes, audio_format: str = "mp3", stt_service=None):
        """
        Play audio asynchronously in a separate thread.
        
        Args:
            audio_data: Audio data as bytes
            audio_format: Audio format ("mp3", "wav", etc.)
            stt_service: Optional SpeechToTextService instance to pause during playback
        """
        def _play_audio():
            # Pause STT audio frame transmission if it's active to prevent feedback loop
            stt_was_active = False
            if stt_service and hasattr(stt_service, 'is_active') and stt_service.is_active:
                stt_was_active = True
                print("Pausing STT audio frame transmission during TTS playback")
                try:
                    # Use the new pause method instead of stopping the service
                    if hasattr(stt_service, 'pause_for_tts'):
                        stt_service.pause_for_tts()
                    else:
                        # Fallback to old method if new method doesn't exist
                        stt_service.stop()
                except Exception as e:
                    print(f"Error pausing STT: {e}")
            try:
                # Try pygame first (best for async playback)
                try:
                    import pygame
                    pygame.mixer.init()
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{audio_format}') as tmp_file:
                        tmp_path = tmp_file.name
                        tmp_file.write(audio_data)
                    
                    try:
                        pygame.mixer.music.load(tmp_path)
                        pygame.mixer.music.play()
                        
                        # Wait for playback to finish
                        while pygame.mixer.music.get_busy():
                            pygame.time.wait(100)
                        
                        pygame.mixer.music.stop()
                        pygame.mixer.quit()
                    finally:
                        # Clean up temp file
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                    
                    print(f"Audio played successfully using pygame (format: {audio_format})")
                    return
                except ImportError:
                    pass
                
                # Fallback to pydub with simpleaudio
                try:
                    from pydub import AudioSegment
                    from pydub.playback import play
                    
                    # Load audio based on format
                    if audio_format == "mp3":
                        audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
                    elif audio_format == "wav":
                        audio = AudioSegment.from_wav(io.BytesIO(audio_data))
                    else:
                        # Try to auto-detect
                        audio = AudioSegment.from_file(io.BytesIO(audio_data), format=audio_format)
                    
                    play(audio)
                    print(f"Audio played successfully using pydub (format: {audio_format})")
                    return
                except ImportError:
                    pass
                
                # Fallback to playsound (blocking but simple)
                try:
                    import playsound
                    
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{audio_format}') as tmp_file:
                        tmp_path = tmp_file.name
                        tmp_file.write(audio_data)
                    
                    try:
                        playsound.playsound(tmp_path, block=True)
                    finally:
                        # Clean up temp file
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                    
                    print(f"Audio played successfully using playsound (format: {audio_format})")
                    return
                except ImportError:
                    pass
                
                print("WARNING: No audio playback library available. Install pygame, pydub, or playsound.")
                
            except Exception as e:
                print(f"Error playing audio: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # Resume STT audio frame transmission after audio finishes playing
                if stt_was_active and stt_service:
                    print("Resuming STT audio frame transmission after TTS playback")
                    try:
                        # Use the new resume method instead of restarting the service
                        if hasattr(stt_service, 'resume_after_tts'):
                            stt_service.resume_after_tts()
                        else:
                            # Fallback to old method if new method doesn't exist
                            stt_service.start(language="fr", model="nova-2")
                    except Exception as e:
                        print(f"Error resuming STT: {e}")
        
        # Start playback in a separate thread
        thread = threading.Thread(target=_play_audio, daemon=True)
        thread.start()
        print(f"Started audio playback in background thread (format: {audio_format})")


# Global TTS service instance
_tts_service: Optional[TTSService] = None


def get_tts_service(provider: str = "pyttsx3") -> TTSService:
    """Get or create the global TTS service instance"""
    global _tts_service
    
    if _tts_service is None or _tts_service.provider != provider.lower():
        _tts_service = TTSService(provider=provider)
    
    return _tts_service

