"""
Text-to-Speech service for generating audio from text.
Supports multiple TTS providers.
"""
from __future__ import annotations

import os
import base64
import threading
import tempfile
import hashlib
from pathlib import Path
from typing import Optional

import pygame
from dotenv import load_dotenv

load_dotenv()


class TTSService:
    """Service for text-to-speech conversion"""

    def __init__(self, provider: str = "pyttsx3", cache_enabled: bool = True):
        """
        Initialize TTS service.

        Args:
            provider: "pyttsx3" (offline), "openai" (requires API key), "elevenlabs" (requires API key),
                or "google" (requires API key)
            cache_enabled: Whether to enable filesystem caching for TTS audio
        """
        print(f"--> Initializing TTS service with provider: {provider}")
        self.provider = provider.lower()
        self._engine = None
        self.cache_enabled = cache_enabled

        if self.cache_enabled:
            backend_dir = Path(__file__).resolve().parents[2]
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
            self._engine.setProperty("rate", 150)
            self._engine.setProperty("volume", 0.9)
        except ImportError:
            raise ValueError("pyttsx3 is not installed. Install it with: pip install pyttsx3")

    def _get_cache_key(
        self,
        text: str,
        language: str,
        voice_name: Optional[str],
        pitch: Optional[float],
        speaking_rate: Optional[float],
    ) -> str:
        """
        Generate a cache key from text and TTS parameters.
        """
        key_data = (
            f"{self.provider}:{text}:{language}:{voice_name or 'default'}:"
            f"{pitch or 0.0}:{speaking_rate or 1.0}"
        )
        hash_obj = hashlib.sha256(key_data.encode("utf-8"))
        return hash_obj.hexdigest()

    def _get_cache_path(self, cache_key: str) -> Optional[Path]:
        """Get the cache file path for a given cache key."""
        if not self.cache_dir:
            return None
        subdir = self.cache_dir / cache_key[:2]
        subdir.mkdir(exist_ok=True)
        return subdir / f"{cache_key}.mp3"

    def _load_from_cache(self, cache_path: Optional[Path]) -> Optional[bytes]:
        """Load audio data from cache file."""
        try:
            if cache_path and cache_path.exists():
                with open(cache_path, "rb") as file:
                    audio_data = file.read()
                print(f"TTS Cache: Loaded from cache ({len(audio_data)} bytes)")
                return audio_data
        except Exception as e:
            print(f"TTS Cache: Error loading from cache: {e}")
        return None

    def _save_to_cache(self, cache_path: Optional[Path], audio_data: bytes) -> None:
        """Save audio data to cache file."""
        try:
            if cache_path and self.cache_enabled:
                with open(cache_path, "wb") as file:
                    file.write(audio_data)
                print(f"TTS Cache: Saved to cache ({len(audio_data)} bytes)")
        except Exception as e:
            print(f"TTS Cache: Error saving to cache: {e}")

    def generate_speech(
        self,
        text: str,
        language: str = "fr",
        voice_name: Optional[str] = None,
        pitch: Optional[float] = None,
        speaking_rate: Optional[float] = None,
    ) -> Optional[bytes]:
        """
        Generate speech audio from text.
        """
        if not text or not text.strip():
            return None

        if self.cache_enabled:
            cache_key = self._get_cache_key(text, language, voice_name, pitch, speaking_rate)
            cache_path = self._get_cache_path(cache_key)
            cached_audio = self._load_from_cache(cache_path)
            if cached_audio:
                return cached_audio

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

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            try:
                self._engine.save_to_file(text, tmp_path)
                self._engine.runAndWait()
                with open(tmp_path, "rb") as file:
                    audio_data = file.read()
                return audio_data
            finally:
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
            voice = "nova"
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="wav",
            )
            return response.content

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
                "xi-api-key": api_key,
            }

            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            }

            response = requests.post(url, json=data, headers=headers, timeout=30)
            print(f"ElevenLabs TTS: Response status code: {response.status_code}")

            response.raise_for_status()
            audio_data = response.content
            print(f"ElevenLabs TTS: Received audio data, length: {len(audio_data)} bytes")
            return audio_data

        except ImportError:
            raise ValueError("requests package is not installed. Install it with: pip install requests")
        except requests.exceptions.RequestException as e:
            print(f"Error generating speech with ElevenLabs (RequestException): {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            return None
        except Exception as e:
            print(f"Error generating speech with ElevenLabs: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _generate_with_google(
        self,
        text: str,
        language: str = "fr",
        voice_name: Optional[str] = None,
        pitch: Optional[float] = None,
        speaking_rate: Optional[float] = None,
    ) -> Optional[bytes]:
        """Generate speech using Google Cloud Text-to-Speech API with service account"""
        try:
            from google.cloud import texttospeech

            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if not credentials_path:
                backend_dir = Path(__file__).resolve().parents[2]
                credentials_path = backend_dir / "google.json"
                if credentials_path.exists():
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)
                    print(f"Google TTS: Using service account from {credentials_path}")
                else:
                    raise ValueError(
                        "Google Cloud service account credentials not found. "
                        "Set GOOGLE_APPLICATION_CREDENTIALS environment variable or place "
                        "google.json in backend/"
                    )

            print(f"Google TTS: Using credentials from {credentials_path}")
            print(f"Google TTS: Text to convert: '{text}'")
            print(f"Google TTS: Language: {language}")

            client = texttospeech.TextToSpeechClient()

            language_code_map = {
                "en": "en-US",
                "fr": "fr-FR",
                "es": "es-ES",
                "de": "de-DE",
                "it": "it-IT",
            }
            google_language = language_code_map.get(language, "en-US")

            if not voice_name:
                voice_name_map = {
                    "en-US": "en-US-Standard-B",
                    "fr-FR": "fr-FR-Standard-B",
                    "es-ES": "es-ES-Standard-B",
                    "de-DE": "de-DE-Standard-B",
                    "it-IT": "it-IT-Standard-B",
                }
                voice_name = voice_name_map.get(google_language, "en-US-Standard-B")

            print(f"Google TTS: Voice: {voice_name}")

            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code=google_language,
                name=voice_name,
            )

            final_pitch = pitch if pitch is not None else 0.0
            final_speaking_rate = speaking_rate if speaking_rate is not None else 1.0

            final_pitch = max(-20.0, min(20.0, final_pitch))
            final_speaking_rate = max(0.25, min(4.0, final_speaking_rate))

            print(f"Google TTS: Pitch: {final_pitch}, Speaking Rate: {final_speaking_rate}")

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=final_speaking_rate,
                pitch=final_pitch,
                volume_gain_db=0.0,
            )

            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )
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
        """
        audio_data = self.generate_speech(text, language)
        if audio_data:
            return base64.b64encode(audio_data).decode("utf-8")
        return None

    def play_audio_async(self, audio_data: bytes, audio_format: str = "mp3", stt_service=None):
        """
        Play audio asynchronously in a separate thread.
        """

        def _play_audio():
            stt_was_active = False
            if stt_service and hasattr(stt_service, "is_active") and stt_service.is_active:
                stt_was_active = True
                print("Pausing STT audio frame transmission during TTS playback")
                try:
                    if hasattr(stt_service, "pause_for_tts"):
                        stt_service.pause_for_tts()
                    else:
                        stt_service.stop()
                except Exception as e:
                    print(f"Error pausing STT: {e}")
            try:
                pygame.mixer.init()
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{audio_format}"
                ) as tmp_file:
                    tmp_path = tmp_file.name
                    tmp_file.write(audio_data)

                try:
                    pygame.mixer.music.load(tmp_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                    pygame.mixer.music.stop()
                    pygame.mixer.quit()
                    print("Audio played successfully using pygame")
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

                print(f"Audio played successfully using pygame (format: {audio_format})")
            except Exception as e:
                print(f"Error playing audio: {e}")
                import traceback

                traceback.print_exc()
            finally:
                if stt_was_active and stt_service:
                    print("Resuming STT audio frame transmission after TTS playback")
                    try:
                        if hasattr(stt_service, "resume_after_tts"):
                            stt_service.resume_after_tts()
                        else:
                            stt_service.start(language="fr", model="nova-2")
                    except Exception as e:
                        print(f"Error resuming STT: {e}")

        thread = threading.Thread(target=_play_audio, daemon=True)
        thread.start()
        print(f"Started audio playback in background thread (format: {audio_format})")


_tts_service: Optional[TTSService] = None


def get_tts_service(provider: str = "pyttsx3") -> TTSService:
    """Get or create the global TTS service instance"""
    global _tts_service

    if _tts_service is None or _tts_service.provider != provider.lower():
        _tts_service = TTSService(provider=provider)

    return _tts_service


__all__ = ["get_tts_service", "TTSService"]
