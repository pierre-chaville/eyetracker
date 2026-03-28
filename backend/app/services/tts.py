"""
Text-to-Speech service for generating audio from text.
Supports multiple TTS providers.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

import pygame

from app.utils.logging import get_logger

logger = get_logger(__name__)


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
        logger.info("Initializing TTS service", extra={"provider": provider})
        self.provider = provider.lower()
        self._engine = None
        self.cache_enabled = cache_enabled

        if self.cache_enabled:
            backend_dir = Path(__file__).resolve().parents[2]
            self.cache_dir = backend_dir / "tts_cache"
            self.cache_dir.mkdir(exist_ok=True)
            logger.debug("TTS cache directory: %s", self.cache_dir)
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
                logger.debug("TTS cache hit: %s bytes", len(audio_data))
                return audio_data
        except Exception as e:
            logger.warning("TTS cache load failed: %s", e, exc_info=True)
        return None

    def _save_to_cache(self, cache_path: Optional[Path], audio_data: bytes) -> None:
        """Save audio data to cache file."""
        try:
            if cache_path and self.cache_enabled:
                with open(cache_path, "wb") as file:
                    file.write(audio_data)
                logger.debug("TTS cache saved: %s bytes", len(audio_data))
        except Exception as e:
            logger.warning("TTS cache save failed: %s", e, exc_info=True)

    async def generate_speech(
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
            audio_data = await asyncio.to_thread(
                self._generate_with_pyttsx3, text
            )
        elif self.provider == "openai":
            audio_data = await asyncio.to_thread(
                self._generate_with_openai, text, language
            )
        elif self.provider == "elevenlabs":
            audio_data = await self._generate_with_elevenlabs(text, language)
        elif self.provider == "google":
            audio_data = await asyncio.to_thread(
                self._generate_with_google,
                text,
                language,
                voice_name,
                pitch,
                speaking_rate,
            )
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
            logger.exception("Error generating speech with pyttsx3: %s", e)
            return None

    def _generate_with_openai(self, text: str, language: str = "en") -> Optional[bytes]:
        """Generate speech using OpenAI TTS API (retry, timeout)."""
        try:
            from openai import OpenAI

            from app.settings import get_settings
            from app.utils.retry import sync_with_retry_and_timing

            settings = get_settings()
            api_key = settings.openai_api_key
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY not set. Set it in .env or environment."
                )

            def _do_call() -> bytes:
                client = OpenAI(
                    api_key=api_key,
                    timeout=settings.http_timeout_seconds,
                )
                response = client.audio.speech.create(
                    model="tts-1",
                    voice="nova",
                    input=text,
                    response_format="wav",
                )
                return response.content

            return sync_with_retry_and_timing(
                logger,
                "OpenAI TTS",
                (ConnectionError, TimeoutError, OSError),
                _do_call,
            )
        except ImportError:
            raise ValueError(
                "openai package is not installed. Install it with: pip install openai"
            )
        except Exception as e:
            logger.exception("Error generating speech with OpenAI: %s", e)
            return None

    async def _generate_with_elevenlabs(
        self, text: str, language: str = "en"
    ) -> Optional[bytes]:
        """Generate speech using ElevenLabs API (httpx async, retry, timeout)."""
        import httpx

        from app.settings import get_settings
        from app.utils.retry import async_with_retry_and_timing

        settings = get_settings()
        api_key = settings.eleven_labs_api_key
        voice_id = settings.eleven_labs_voice_id

        if not api_key:
            raise ValueError(
                "ELEVEN_LABS_API_KEY not set. Set it in .env or environment."
            )
        if not voice_id:
            raise ValueError(
                "ELEVEN_LABS_VOICE_ID not set. Set it in .env or environment."
            )

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
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
        timeout = settings.http_timeout_seconds

        def _should_retry(e: BaseException) -> bool:
            if isinstance(e, httpx.RequestError):
                return True
            if isinstance(e, httpx.HTTPStatusError):
                return e.response.status_code >= 500
            return False

        from app.http_client import get_httpx_client

        shared_client = get_httpx_client()

        async def _do_request() -> bytes:
            if shared_client is not None:
                response = await shared_client.post(
                    url, json=data, headers=headers, timeout=timeout
                )
            else:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        url, json=data, headers=headers, timeout=timeout
                    )
            response.raise_for_status()
            return response.content

        try:
            return await async_with_retry_and_timing(
                logger,
                "ElevenLabs TTS",
                _do_request,
                retry_if=_should_retry,
            )
        except httpx.HTTPStatusError as e:
            logger.warning(
                "ElevenLabs TTS HTTP error: %s %s",
                e.response.status_code,
                (e.response.text or "")[:200],
            )
            return None
        except httpx.RequestError as e:
            logger.exception("ElevenLabs TTS request failed: %s", e)
            return None
        except Exception as e:
            logger.exception("ElevenLabs TTS error: %s", e)
            return None

    def _generate_with_google(
        self,
        text: str,
        language: str = "fr",
        voice_name: Optional[str] = None,
        pitch: Optional[float] = None,
        speaking_rate: Optional[float] = None,
    ) -> Optional[bytes]:
        """Generate speech using Google Cloud Text-to-Speech API (retry, timeout)."""
        try:
            from google.cloud import texttospeech

            from app.settings import get_settings
            from app.utils.retry import sync_with_retry_and_timing

            settings = get_settings()
            credentials_path = settings.google_application_credentials
            if not credentials_path:
                backend_dir = Path(__file__).resolve().parents[2]
                default_path = backend_dir / "google.json"
                if default_path.exists():
                    credentials_path = str(default_path)
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                    logger.debug("Google TTS: using default credentials path")
                else:
                    raise ValueError(
                        "Google Cloud credentials not found. Set "
                        "GOOGLE_APPLICATION_CREDENTIALS in .env or place "
                        "google.json in backend/"
                    )
            else:
                credentials_path = str(credentials_path)

            logger.debug(
                "Google TTS request",
                extra={"text_length": len(text), "language": language},
            )

            language_code_map = {
                "en": "en-US",
                "fr": "fr-FR",
                "es": "es-ES",
                "de": "de-DE",
                "it": "it-IT",
            }
            google_language = language_code_map.get(language, "en-US")
            resolved_voice = voice_name
            if not resolved_voice:
                voice_name_map = {
                    "en-US": "en-US-Standard-B",
                    "fr-FR": "fr-FR-Standard-B",
                    "es-ES": "es-ES-Standard-B",
                    "de-DE": "de-DE-Standard-B",
                    "it-IT": "it-IT-Standard-B",
                }
                resolved_voice = voice_name_map.get(google_language, "en-US-Standard-B")

            final_pitch = max(-20.0, min(20.0, pitch if pitch is not None else 0.0))
            final_sr = max(0.25, min(4.0, speaking_rate if speaking_rate is not None else 1.0))

            def _do_call() -> bytes:
                client = texttospeech.TextToSpeechClient()
                synthesis_input = texttospeech.SynthesisInput(text=text)
                voice_params = texttospeech.VoiceSelectionParams(
                    language_code=google_language,
                    name=resolved_voice,
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=final_sr,
                    pitch=final_pitch,
                    volume_gain_db=0.0,
                )
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice_params,
                    audio_config=audio_config,
                )
                return response.audio_content

            audio_data = sync_with_retry_and_timing(
                logger,
                "Google TTS",
                (ConnectionError, TimeoutError, OSError),
                _do_call,
            )
            logger.debug("Google TTS: received %s bytes", len(audio_data))
            return audio_data

        except ImportError:
            raise ValueError(
                "google-cloud-texttospeech package is not installed. "
                "Install it with: pip install google-cloud-texttospeech"
            )
        except Exception as e:
            logger.exception("Error generating speech with Google Cloud TTS: %s", e)
            return None

    async def generate_speech_base64(
        self, text: str, language: str = "en"
    ) -> Optional[str]:
        """
        Generate speech and return as base64-encoded string.
        """
        audio_data = await self.generate_speech(text, language)
        if audio_data:
            return base64.b64encode(audio_data).decode("utf-8")
        return None

    _playback_lock = threading.Lock()

    _MAX_PLAYBACK_SECONDS = 30

    def play_audio_async(self, audio_data: bytes, audio_format: str = "mp3", stt_service=None):
        """Play audio asynchronously in a separate thread."""

        def _play_audio():
            if not self._playback_lock.acquire(timeout=2):
                logger.warning("TTS playback skipped – another playback is in progress")
                return

            tmp_path: Optional[str] = None
            stt_was_active = False
            try:
                if stt_service and hasattr(stt_service, "is_active") and stt_service.is_active:
                    stt_was_active = True
                    logger.debug("Pausing STT during TTS playback")
                    try:
                        if hasattr(stt_service, "pause_for_tts"):
                            stt_service.pause_for_tts()
                        else:
                            stt_service.stop()
                    except Exception as e:
                        logger.warning("Error pausing STT: %s", e, exc_info=True)

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=f".{audio_format}"
                ) as tmp_file:
                    tmp_path = tmp_file.name
                    tmp_file.write(audio_data)

                try:
                    pygame.mixer.quit()
                except Exception:
                    pass
                pygame.mixer.init()

                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()

                deadline = time.monotonic() + self._MAX_PLAYBACK_SECONDS
                while pygame.mixer.music.get_busy():
                    if time.monotonic() > deadline:
                        logger.warning("TTS playback exceeded %ss timeout, stopping", self._MAX_PLAYBACK_SECONDS)
                        break
                    pygame.time.wait(100)

                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                logger.debug("TTS playback finished (format: %s)", audio_format)
            except Exception as e:
                logger.exception("Error playing TTS audio: %s", e)
            finally:
                try:
                    pygame.mixer.quit()
                except Exception:
                    pass

                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        logger.debug("Could not delete temp file %s, will be cleaned up later", tmp_path)

                if stt_was_active and stt_service:
                    logger.debug("Resuming STT after TTS playback")
                    try:
                        if hasattr(stt_service, "resume_after_tts"):
                            stt_service.resume_after_tts()
                        else:
                            stt_service.start(language="fr", model="nova-2")
                    except Exception as e:
                        logger.warning("Error resuming STT: %s", e, exc_info=True)

                self._playback_lock.release()

        thread = threading.Thread(target=_play_audio, daemon=True)
        thread.start()
        logger.debug("TTS playback started in background (format: %s)", audio_format)


_tts_service: Optional[TTSService] = None


def get_tts_service(provider: str = "pyttsx3") -> TTSService:
    """Get or create the global TTS service instance"""
    global _tts_service

    if _tts_service is None or _tts_service.provider != provider.lower():
        _tts_service = TTSService(provider=provider)

    return _tts_service


__all__ = ["get_tts_service", "TTSService"]
