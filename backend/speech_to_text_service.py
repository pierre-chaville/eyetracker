"""
Speech-to-text service using Deepgram.
Handles microphone audio capture and transcription with WebSocket event callbacks.
"""

import os
import threading
import time
from typing import Optional, Callable
from dotenv import load_dotenv

load_dotenv()

try:
    from deepgram import DeepgramClient
    from deepgram.listen import v1 as listen_v1
    import pyaudio
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = str(e)


class SpeechToTextService:
    """Service for handling speech-to-text transcription using Deepgram."""
    
    def __init__(self, on_speech_started: Optional[Callable] = None, 
                 on_transcription: Optional[Callable] = None,
                 on_error: Optional[Callable] = None):
        """
        Initialize the speech-to-text service.
        
        Args:
            on_speech_started: Callback function called when speech starts (no args)
            on_transcription: Callback function called with transcribed text (text: str)
            on_error: Callback function called on error (error: str)
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError(f"Required dependencies not available: {IMPORT_ERROR}")
        
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPGRAM_API_KEY not found in environment variables")
        
        self.on_speech_started = on_speech_started
        self.on_transcription = on_transcription
        self.on_error = on_error
        
        self.deepgram = None
        self.dg_connection = None
        self.audio = None
        self.stream = None
        self.receive_thread = None
        self.stream_thread = None
        self.running = False
        self.is_active = False
        
        # Audio configuration
        self.CHUNK = 8192
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
    
    def start(self, language: str = "fr", model: str = "nova-2"):
        """
        Start speech-to-text transcription.
        
        Args:
            language: Language code (default: "fr" for French)
            model: Deepgram model to use (default: "nova-2")
        """
        if self.is_active:
            return
        
        try:
            # Initialize Deepgram client
            self.deepgram = DeepgramClient(api_key=self.api_key)
            
            # Try to open microphone
            self.audio = pyaudio.PyAudio()
            
            # List available input devices
            input_devices = []
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info["maxInputChannels"] > 0:
                    input_devices.append((i, device_info))
            
            if not input_devices:
                raise Exception("No input devices found")
            
            # Try to open devices one by one until one works
            self.stream = None
            for device_index, device_info in input_devices:
                try:
                    # Try with device's native sample rate first, then fall back to 16000
                    for sample_rate in [
                        int(device_info["defaultSampleRate"]),
                        16000,
                        44100,
                        48000,
                    ]:
                        try:
                            self.stream = self.audio.open(
                                format=self.FORMAT,
                                channels=self.CHANNELS,
                                rate=sample_rate,
                                input=True,
                                input_device_index=device_index,
                                frames_per_buffer=self.CHUNK,
                            )
                            self.RATE = sample_rate
                            break
                        except Exception:
                            if sample_rate == 48000:
                                raise
                            continue
                    
                    if self.stream:
                        break
                except Exception:
                    continue
            
            if self.stream is None:
                raise Exception("Could not open any audio input device")
            
            # Create live transcription connection - use context manager pattern
            # We need to enter the context manager to get the connection object
            self.dg_connection = self.deepgram.listen.v1.connect(
                model=model,
                language=language,
                punctuate="true",
                encoding="linear16",
                channels="1",
                sample_rate=str(self.RATE),
                interim_results="true",
                endpointing="2000",
                vad_events="true",
            )
            
            # Enter the context manager to get the actual connection
            self.dg_connection_context = self.dg_connection.__enter__()
            
            # Register event handlers
            self.dg_connection_context.on(listen_v1.ListenV1Results, self._on_message)
            self.dg_connection_context.on(listen_v1.ListenV1Metadata, self._on_metadata)
            self.dg_connection_context.on(listen_v1.ListenV1SpeechStarted, self._on_speech_started)
            self.dg_connection_context.on(listen_v1.ListenV1UtteranceEnd, self._on_utterance_end)
            # Note: ListenV1Error may not be available in all SDK versions, handle errors in recv() instead
            
            self.running = True
            self.is_active = True
            
            # Start receiving messages in a separate thread
            self.receive_thread = threading.Thread(target=self._receive_messages, daemon=True)
            self.receive_thread.start()
            
            # Give the connection a moment to fully establish
            time.sleep(0.1)
            
            # Start streaming audio in a separate thread
            self.stream_thread = threading.Thread(target=self._stream_audio, daemon=True)
            self.stream_thread.start()
            
        except Exception as e:
            self.is_active = False
            if self.on_error:
                self.on_error(str(e))
            raise
    
    def stop(self):
        """Stop speech-to-text transcription."""
        if not self.is_active:
            return
        
        self.running = False
        self.is_active = False
        
        # Stop streaming
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
        
        # Close Deepgram connection
        if hasattr(self, 'dg_connection_context') and self.dg_connection_context:
            try:
                self.dg_connection_context.finish()
            except Exception:
                pass
        
        if hasattr(self, 'dg_connection') and self.dg_connection:
            try:
                self.dg_connection.__exit__(None, None, None)
            except Exception:
                pass
        
        # Terminate audio
        if self.audio:
            try:
                self.audio.terminate()
            except Exception:
                pass
        
        # Wait for threads to finish
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=1.0)
    
    def _on_message(self, result, **kwargs):
        """Handle transcription results."""
        try:
            if result.is_final:
                sentence = result.channel.alternatives[0].transcript
                if len(sentence) > 0 and self.on_transcription:
                    print(f"--> Transcription: {sentence}")
                    self.on_transcription(sentence)
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error in on_message: {e}")
    
    def _on_metadata(self, metadata, **kwargs):
        """Handle metadata."""
        pass
    
    def _on_speech_started(self, speech_started, **kwargs):
        """Handle speech started event."""
        if self.on_speech_started:
            print(f"--> Speech started")
            self.on_speech_started()
    
    def _on_utterance_end(self, utterance_end, **kwargs):
        """Handle utterance end event."""
        pass
    
    def _on_error(self, error, **kwargs):
        """Handle errors."""
        if self.on_error:
            self.on_error(f"Deepgram error: {error}")
    
    def _receive_messages(self):
        """Receive messages from Deepgram in a separate thread."""
        while self.running:
            try:
                if not hasattr(self, 'dg_connection_context') or not self.dg_connection_context:
                    break
                message = self.dg_connection_context.recv()
                if isinstance(message, listen_v1.ListenV1Results):
                    self._on_message(message)
                elif isinstance(message, listen_v1.ListenV1Metadata):
                    self._on_metadata(message)
                elif isinstance(message, listen_v1.ListenV1SpeechStarted):
                    self._on_speech_started(message)
                elif isinstance(message, listen_v1.ListenV1UtteranceEnd):
                    self._on_utterance_end(message)
                # Handle any other message types or errors
                else:
                    # If it's an error-like object, handle it
                    if hasattr(message, 'error') or (isinstance(message, Exception)):
                        self._on_error(message)
            except Exception as e:
                if self.running:
                    if self.on_error:
                        self.on_error(f"Error receiving message: {e}")
                break
    
    def _stream_audio(self):
        """Stream audio to Deepgram in a separate thread."""
        try:
            while self.running and self.stream:
                try:
                    if not hasattr(self, 'dg_connection_context') or not self.dg_connection_context:
                        break
                    data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                    if self.dg_connection_context and self.running:
                        self.dg_connection_context.send_media(data)
                except Exception as e:
                    if self.running:
                        if self.on_error:
                            self.on_error(f"Error streaming audio: {e}")
                    break
        except Exception as e:
            if self.on_error:
                self.on_error(f"Error in audio stream: {e}")
