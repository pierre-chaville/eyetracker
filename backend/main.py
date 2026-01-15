from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Set, Dict
from sqlmodel import Session, select
import uvicorn
import json
import os
import base64
from pathlib import Path
from datetime import datetime
import asyncio

from database import engine, create_db_and_tables, get_session
from models import (
    User, UserCreate, UserUpdate, UserResponse,
    Caregiver, CaregiverCreate, CaregiverUpdate, CaregiverResponse,
    CommunicationSession, CommunicationSessionCreate, CommunicationSessionUpdate, CommunicationSessionResponse,
    SessionStep, SessionStepCreate, SessionStepResponse, ChoiceData,
    EyeTrackingSetup, CommunicationSettings
)
from calibration import (
    CalibrationRequest,
    CalibrationResponse,
    process_calibration_data,
)
from llm import get_llm_service
from tts_service import get_tts_service
try:
    from stt_service import SpeechToTextService
except ImportError:
    # Speech-to-text service not available (missing dependencies)
    SpeechToTextService = None

app = FastAPI(title="Eye Tracker API", version="1.0.0")

# CORS middleware for Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Speech-to-text service instance
speech_to_text_service: Optional[SpeechToTextService] = None

# WebSocket connections for speech-to-text events
speech_websocket_connections: Set[WebSocket] = set()

# Event loop for broadcasting events
_event_loop: Optional[asyncio.AbstractEventLoop] = None


def get_event_loop():
    """Get or create event loop for broadcasting events."""
    global _event_loop
    if _event_loop is None or _event_loop.is_closed():
        try:
            _event_loop = asyncio.get_event_loop()
        except RuntimeError:
            _event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_event_loop)
    return _event_loop


async def broadcast_speech_event(event_type: str, data: dict):
    """Broadcast speech event to all connected WebSocket clients."""
    message = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    print(f"Broadcasting event: {event_type} to {len(speech_websocket_connections)} connections")
    disconnected = set()
    for connection in speech_websocket_connections.copy():
        try:
            await connection.send_json(message)
            print(f"Sent {event_type} to WebSocket client")
        except Exception as e:
            print(f"Error sending to WebSocket: {e}")
            disconnected.add(connection)
    # Remove disconnected connections
    speech_websocket_connections.difference_update(disconnected)
    print(f"Active WebSocket connections: {len(speech_websocket_connections)}")


def on_speech_started():
    """Callback when speech starts."""
    print("on_speech_started called")
    try:
        loop = get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_speech_event("speech_started", {}), loop)
        else:
            loop.run_until_complete(broadcast_speech_event("speech_started", {}))
    except Exception as e:
        print(f"Error in on_speech_started: {e}")


def on_transcription(text: str):
    """Callback when a sentence is transcribed."""
    print(f"on_transcription called with text: {text}")
    try:
        loop = get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_speech_event("transcription", {"text": text}), loop)
        else:
            loop.run_until_complete(broadcast_speech_event("transcription", {"text": text}))
    except Exception as e:
        print(f"Error in on_transcription: {e}")


def on_speech_error(error: str):
    """Callback on speech-to-text error."""
    print(f"on_speech_error called with error: {error}")
    try:
        loop = get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_speech_event("error", {"error": error}), loop)
        else:
            loop.run_until_complete(broadcast_speech_event("error", {"error": error}))
    except Exception as e:
        print(f"Error in on_speech_error: {e}")


# Initialize database on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.on_event("shutdown")
def on_shutdown():
    """Cleanup on shutdown."""
    global speech_to_text_service
    if speech_to_text_service:
        speech_to_text_service.stop()
        speech_to_text_service = None


class EyeTrackingStatus(BaseModel):
    is_active: bool
    calibration_status: Optional[str] = None


class GazePoint(BaseModel):
    x: float
    y: float
    timestamp: float


class CommunicationRequest(BaseModel):
    gaze_points: List[GazePoint]
    context: Optional[str] = None


class CommunicationResponse(BaseModel):
    interpreted_text: str
    confidence: float
    suggestions: List[str]


@app.get("/", tags=["general"])
async def root():
    return {"message": "Eye Tracker API", "status": "running"}


@app.get("/api/health", tags=["general"])
async def health_check():
    return {"status": "healthy"}


@app.post("/api/eye-tracking/start", tags=["eye-tracking"])
async def start_eye_tracking():
    """Start eye tracking session"""
    return {"success": True, "message": "Eye tracking started"}


@app.post("/api/eye-tracking/stop", tags=["eye-tracking"])
async def stop_eye_tracking():
    """Stop eye tracking session"""
    return {"success": True, "message": "Eye tracking stopped"}


@app.get("/api/eye-tracking/status", tags=["eye-tracking"])
async def get_eye_tracking_status():
    """Get current eye tracking status"""
    return {
        "is_active": False,
        "calibration_status": "not_calibrated"
    }


@app.post("/api/communication/interpret", tags=["communication"])
async def interpret_gaze(request: CommunicationRequest):
    """Interpret gaze points and generate communication suggestions using AI"""
    # TODO: Implement AI/LLM integration for interpreting gaze patterns
    return {
        "interpreted_text": "Hello",
        "confidence": 0.85,
        "suggestions": ["Hello", "Hi there", "Good morning"]
    }


class Choice(BaseModel):
    """A choice option for the communication grid"""
    id: str
    text: Optional[str] = None
    icon: Optional[str] = None
    probability: Optional[float] = None


class ChoicesResponse(BaseModel):
    """Response with available choices"""
    choices: List[Choice]


class ChoiceSelectionRequest(BaseModel):
    """Request to select a choice"""
    choice_id: str
    choice_text: Optional[str] = None
    current_text: Optional[str] = None
    session_id: Optional[int] = None
    step_number: Optional[int] = None


class ChoicesRequest(BaseModel):
    """Request for generating choices"""
    conversation_history: Optional[List[Dict[str, str]]] = []
    user_id: Optional[int] = None
    caregiver_id: Optional[int] = None
    current_text: Optional[str] = None
    session_id: Optional[int] = None
    step_number: Optional[int] = None


@app.post("/api/communication/choices", response_model=ChoicesResponse, tags=["communication"])
async def get_choices(request: ChoicesRequest, session: Session = Depends(get_session)):
    """
    Get available choices for the communication grid.
    Returns 2-8 choices based on context using LLM.
    """
    try:
        # Load config
        config = load_config()
        
        # Get user and caregiver info if provided
        user_notes = None
        caregiver_description = None
        
        if request.user_id:
            user = session.get(User, request.user_id)
            if user:
                user_notes = user.notes
        
        if request.caregiver_id:
            caregiver = session.get(Caregiver, request.caregiver_id)
            if caregiver:
                caregiver_description = caregiver.description
        
        # Get LLM service
        llm_service = get_llm_service(
            provider=config.provider,
            model=config.model,
            temperature=config.temperature
        )
        
        # Generate choices using LLM
        llm_choices = await llm_service.generate_choices(
            system_prompt=config.communicate_prompt,
            conversation_history=request.conversation_history or [],
            user_notes=user_notes,
            caregiver_description=caregiver_description,
            current_text=request.current_text
        )
        
        # Convert to Choice format with IDs
        choices = [
            Choice(
                id=str(i + 1),
                text=choice["text"],
                probability=choice["probability"]
            )
            for i, choice in enumerate(llm_choices)
        ]
        
        # Save step to session if session_id is provided
        if request.session_id and request.step_number is not None:
            try:
                # Determine message role based on conversation history
                message_role = None
                message_content = None
                if request.conversation_history:
                    last_message = request.conversation_history[-1]
                    message_role = last_message.get("role", "").lower()
                    message_content = last_message.get("content", "")
                    # Map 'user' to 'caregiver' and 'assistant' to 'user' for clarity
                    if message_role == "user":
                        message_role = "caregiver"
                    elif message_role == "assistant":
                        message_role = "user"
                
                # Prepare choices data
                choices_data = [{"text": c.text, "probability": c.probability} for c in choices]
                
                step = SessionStep(
                    session_id=request.session_id,
                    step_number=request.step_number,
                    message_role=message_role,
                    message_content=message_content,
                    choices_json=choices_data,
                    selected_choice_text=None  # Not selected yet
                )
                
                session.add(step)
                
                # Update session updated_at
                comm_session = session.get(CommunicationSession, request.session_id)
                if comm_session:
                    comm_session.updated_at = datetime.utcnow()
                    session.add(comm_session)
                
                session.commit()
            except Exception as e:
                print(f"Error saving session step: {e}")
                # Continue even if saving fails
        
        return ChoicesResponse(choices=choices)
    
    except Exception as e:
        print(f"Error generating choices: {e}")
        # Fallback to default choices
        choices = [
            Choice(id="1", text="Yes", icon="✓", probability=0.5),
            Choice(id="2", text="No", icon="✗", probability=0.5),
            Choice(id="3", text="More", icon="+", probability=0.3),
            Choice(id="4", text="Done", icon="✓", probability=0.2)
        ]
        return ChoicesResponse(choices=choices)


@app.post("/api/keyboard/predictions", tags=["keyboard"])
async def get_keyboard_predictions(request: ChoicesRequest, session: Session = Depends(get_session)):
    """
    Get predictive words for the keyboard based on current text.
    Returns up to 5 words suggested by LLM.
    """
    try:
        config = load_config()
        
        # Get user and caregiver info if provided
        user_notes = None
        caregiver_description = None
        
        if request.user_id:
            user = session.get(User, request.user_id)
            if user:
                user_notes = user.notes
        
        if request.caregiver_id:
            caregiver = session.get(Caregiver, request.caregiver_id)
            if caregiver:
                caregiver_description = caregiver.description
        
        # Use LLM to generate predictive words
        llm_service = get_llm_service()
        
        # Create a simple prompt for word prediction
        conversation_history = request.conversation_history or []
        current_text = request.current_text or ""
        
        # Determine which prompt to use based on current text
        # If current_text has multiple single letters (like "a e i"), use multiple letters prompt
        # Otherwise use regular keyboard prompt
        text_words = current_text.split() if current_text else []
        is_multiple_letters = len(text_words) > 1 and all(len(word) == 1 for word in text_words)
        
        system_prompt = (
            config.keyboard_multiple_letters_prompt if is_multiple_letters 
            else config.keyboard_prompt
        ) or "You are a helpful assistant that suggests words for text input."
        
        # Generate choices (words) using LLM
        choices = await llm_service.generate_choices(
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            user_notes=user_notes,
            caregiver_description=caregiver_description,
            current_text=current_text
        )
        
        # Extract words from choices (limit to 5)
        # choices is a list of dicts with "text" and "probability" keys
        words = [choice["text"] for choice in choices[:5] if choice.get("text")]
        
        return {"words": words}
    
    except Exception as e:
        print(f"Error generating keyboard predictions: {e}")
        # Fallback to empty list
        return {"words": []}


@app.post("/api/keyboard/tts", tags=["keyboard"])
async def keyboard_tts(request: dict, session: Session = Depends(get_session)):
    """
    Generate TTS for keyboard input (word or letter).
    """
    try:
        text = request.get("text", "")
        if not text:
            return {"audio_base64": None}
        
        # Determine TTS provider
        tts_provider = "pyttsx3"
        # Check for Google Cloud service account credentials
        google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not google_creds:
            backend_dir = Path(__file__).parent
            google_json_path = backend_dir / "google.json"
            if google_json_path.exists():
                google_creds = str(google_json_path)
        
        if google_creds:
            tts_provider = "google"
        elif os.getenv("ELEVEN_LABS_API_KEY") and os.getenv("ELEVEN_LABS_VOICE_ID"):
            tts_provider = "elevenlabs"
        elif load_config().provider == "openai" and os.getenv("OPENAI_API_KEY"):
            tts_provider = "openai"
        
        tts_service = get_tts_service(provider=tts_provider)
        
        # Get TTS config from settings
        tts_config = load_config()
        
        # Generate audio data with config values
        audio_data = tts_service.generate_speech(
            text=text,
            language=tts_config.tts_language or "fr",
            voice_name=tts_config.tts_voice_name if tts_config.tts_voice_name else None,
            pitch=tts_config.tts_pitch if tts_config.tts_pitch is not None else None,
            speaking_rate=tts_config.tts_speaking_rate if tts_config.tts_speaking_rate is not None else None
        )
        
        if audio_data:
            # Determine audio format based on provider
            if tts_provider == "google" or tts_provider == "elevenlabs":
                audio_format = "mp3"
            elif tts_provider == "openai":
                audio_format = "wav"
            else:  # pyttsx3
                audio_format = "wav"
            
            # Convert to base64 for frontend (if needed)
            import base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Play audio asynchronously in backend
            print(f"Playing keyboard TTS audio in backend (format: {audio_format})")
            tts_service.play_audio_async(audio_data, audio_format, stt_service=speech_to_text_service)
            
            return {"audio_base64": audio_base64}
        
        return {"audio_base64": None}
    
    except Exception as e:
        print(f"Error generating TTS for keyboard: {e}")
        return {"audio_base64": None}


@app.post("/api/communication/select", tags=["communication"])
async def select_choice(request: ChoiceSelectionRequest, db_session: Session = Depends(get_session)):
    """
    Handle selection of a choice.
    This triggers text-to-speech generation for the selected choice.
    """
    try:
        # Load config to get TTS provider preference
        config = load_config()
        
        # Default to pyttsx3 for offline TTS, but could be configurable
        tts_provider = "pyttsx3"
        
        # If Google Cloud service account is available, use Google Cloud TTS (lowest latency)
        # Check for GOOGLE_APPLICATION_CREDENTIALS or google.json file
        google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not google_creds:
            backend_dir = Path(__file__).parent
            google_json_path = backend_dir / "google.json"
            if google_json_path.exists():
                google_creds = str(google_json_path)
        
        if google_creds:
            tts_provider = "google"
        # Fallback to ElevenLabs if Google is not available
        elif os.getenv("ELEVEN_LABS_API_KEY") and os.getenv("ELEVEN_LABS_VOICE_ID"):
            tts_provider = "elevenlabs"
        # Fallback to OpenAI if neither Google nor ElevenLabs is available
        elif config.provider == "openai" and os.getenv("OPENAI_API_KEY"):
            tts_provider = "openai"
        
        # Get TTS service
        tts_service = get_tts_service(provider=tts_provider)
        
        # Generate speech for the selected choice text
        audio_base64 = None
        audio_data = None
        audio_format = "mp3"  # Default format (Google Cloud TTS returns MP3)
        
        if request.choice_text:
            # Get TTS config from settings
            tts_config = load_config()
            print(f"Generating TTS for text: '{request.choice_text}' using provider: {tts_provider}")
            
            # Generate audio data with config values
            audio_data = tts_service.generate_speech(
                text=request.choice_text,
                language=tts_config.tts_language or "en",
                voice_name=tts_config.tts_voice_name if tts_config.tts_voice_name else None,
                pitch=tts_config.tts_pitch if tts_config.tts_pitch is not None else None,
                speaking_rate=tts_config.tts_speaking_rate if tts_config.tts_speaking_rate is not None else None
            )
            
            if audio_data:
                # Determine audio format based on provider
                if tts_provider == "google" or tts_provider == "elevenlabs":
                    audio_format = "mp3"
                elif tts_provider == "openai":
                    audio_format = "wav"
                else:  # pyttsx3
                    audio_format = "wav"
                
                # Convert to base64 for frontend (if needed)
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                # Play audio asynchronously in backend
                # Pass STT service to pause it during playback
                print(f"Playing audio in backend (format: {audio_format})")
                tts_service.play_audio_async(audio_data, audio_format, stt_service=speech_to_text_service)
                
                print(f"TTS generated and playback started, audio length: {len(audio_data)} bytes")
            else:
                print("WARNING: TTS generation returned None")
        
        # Update session step with selected choice if session_id is provided
        if request.session_id and request.step_number is not None and request.choice_text:
            try:
                from sqlmodel import select as sql_select
                step_statement = sql_select(SessionStep).where(
                    SessionStep.session_id == request.session_id,
                    SessionStep.step_number == request.step_number
                )
                step = db_session.exec(step_statement).first()
                if step:
                    step.selected_choice_text = request.choice_text
                    step.timestamp = datetime.utcnow()
                    db_session.add(step)
                    
                    # Update session updated_at
                    comm_session = db_session.get(CommunicationSession, request.session_id)
                    if comm_session:
                        comm_session.updated_at = datetime.utcnow()
                        db_session.add(comm_session)
                    
                    db_session.commit()
            except Exception as e:
                print(f"Error updating session step with selected choice: {e}")
        
        return {
            "success": True,
            "message": f"Choice '{request.choice_id}' selected",
            "updated_text": request.current_text,
            "audio_base64": audio_base64
        }
    except Exception as e:
        print(f"Error in select_choice: {e}")
        import traceback
        traceback.print_exc()
        # Try to generate audio even if there's an error
        audio_base64 = None
        try:
            if request.choice_text:
                config = load_config()
                tts_provider = "pyttsx3"
                # Check for Google Cloud service account credentials
                google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                if not google_creds:
                    backend_dir = Path(__file__).parent
                    google_json_path = backend_dir / "google.json"
                    if google_json_path.exists():
                        google_creds = str(google_json_path)
                
                if google_creds:
                    tts_provider = "google"
                elif os.getenv("ELEVEN_LABS_API_KEY") and os.getenv("ELEVEN_LABS_VOICE_ID"):
                    tts_provider = "elevenlabs"
                elif config.provider == "openai" and os.getenv("OPENAI_API_KEY"):
                    tts_provider = "openai"
                tts_service = get_tts_service(provider=tts_provider)
                
                # Get TTS config from settings
                tts_config = load_config()
                
                # Generate audio data with config values
                audio_data = tts_service.generate_speech(
                    text=request.choice_text,
                    language=tts_config.tts_language or "en",
                    voice_name=tts_config.tts_voice_name if tts_config.tts_voice_name else None,
                    pitch=tts_config.tts_pitch if tts_config.tts_pitch is not None else None,
                    speaking_rate=tts_config.tts_speaking_rate if tts_config.tts_speaking_rate is not None else None
                )
                
                if audio_data:
                    # Determine audio format
                    if tts_provider == "google" or tts_provider == "elevenlabs":
                        audio_format = "mp3"
                    elif tts_provider == "openai":
                        audio_format = "wav"
                    else:
                        audio_format = "wav"
                    
                    # Convert to base64
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    # Play audio asynchronously in backend
                    tts_service.play_audio_async(audio_data, audio_format, stt_service=speech_to_text_service)
                else:
                    audio_base64 = None
        except Exception as tts_error:
            print(f"Error generating TTS in exception handler: {tts_error}")
        
        return {
            "success": True,
            "message": f"Choice '{request.choice_id}' selected",
            "updated_text": request.current_text,
            "audio_base64": audio_base64,
            "error": str(e)
        }


@app.post("/api/calibration/start", tags=["calibration"])
async def start_calibration():
    """Start calibration process"""
    return {"success": True, "message": "Calibration started"}


@app.post("/api/calibration/process", response_model=CalibrationResponse, tags=["calibration"])
async def process_calibration(request: CalibrationRequest, session: Session = Depends(get_session)):
    """Process calibration data and calculate averages for each position"""
    return process_calibration_data(request, session)


# Helper functions for JSON serialization/deserialization
def serialize_eye_tracking_setup(setup: Optional[EyeTrackingSetup]) -> Optional[dict]:
    """Serialize EyeTrackingSetup to dict for JSON storage"""
    if setup is None:
        return None
    return setup.model_dump()


def serialize_communication(comm: Optional[CommunicationSettings]) -> Optional[dict]:
    """Serialize CommunicationSettings to dict for JSON storage"""
    if comm is None:
        return None
    return comm.model_dump()


def deserialize_eye_tracking_setup(data: Optional[dict]) -> Optional[EyeTrackingSetup]:
    """Deserialize dict to EyeTrackingSetup"""
    if data is None:
        return None
    try:
        return EyeTrackingSetup(**data)
    except (TypeError, ValueError):
        return None


def deserialize_communication(data: Optional[dict]) -> Optional[CommunicationSettings]:
    """Deserialize dict to CommunicationSettings"""
    if data is None:
        return None
    try:
        return CommunicationSettings(**data)
    except (TypeError, ValueError):
        return None


def user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse"""
    return UserResponse(
        id=user.id,
        name=user.name,
        eye_tracking_setup=deserialize_eye_tracking_setup(user.eye_tracking_setup),
        calibration=user.calibration,
        communication=deserialize_communication(user.communication),
        created_at=user.created_at,
        updated_at=user.updated_at,
        is_active=user.is_active,
        notes=user.notes,
        gender=user.gender,
        age=user.age,
        voice=user.voice
    )


# User CRUD endpoints
@app.get("/api/users", response_model=List[UserResponse], tags=["users"])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    session: Session = Depends(get_session)
):
    """List all users with optional filtering"""
    statement = select(User)
    
    if active_only:
        statement = statement.where(User.is_active == True)
    
    statement = statement.offset(skip).limit(limit)
    users = session.exec(statement).all()
    
    return [user_to_response(user) for user in users]


@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["users"])
async def get_user(user_id: int, session: Session = Depends(get_session)):
    """Get a specific user by ID"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    return user_to_response(user)


@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["users"])
async def create_user(user_data: UserCreate, session: Session = Depends(get_session)):
    """Create a new user"""
    # Serialize Pydantic models to JSON strings
    eye_tracking_json = serialize_eye_tracking_setup(user_data.eye_tracking_setup)
    communication_json = serialize_communication(user_data.communication)
    
    # Create user
    user = User(
        name=user_data.name,
        eye_tracking_setup=eye_tracking_json,
        calibration=user_data.calibration,
        communication=communication_json,
        notes=user_data.notes,
        gender=user_data.gender,
        age=user_data.age,
        voice=user_data.voice
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user_to_response(user)


@app.put("/api/users/{user_id}", response_model=UserResponse, tags=["users"])
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: Session = Depends(get_session)
):
    """Update an existing user"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # Update fields if provided
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.eye_tracking_setup is not None:
        user.eye_tracking_setup = serialize_eye_tracking_setup(user_data.eye_tracking_setup)
    if user_data.calibration is not None:
        user.calibration = user_data.calibration
    if user_data.communication is not None:
        user.communication = serialize_communication(user_data.communication)
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.notes is not None:
        user.notes = user_data.notes
    if user_data.gender is not None:
        user.gender = user_data.gender
    if user_data.age is not None:
        user.age = user_data.age
    if user_data.voice is not None:
        user.voice = user_data.voice
    
    # Update timestamp
    user.updated_at = datetime.utcnow()
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user_to_response(user)


@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
async def delete_user(user_id: int, session: Session = Depends(get_session)):
    """Delete a user"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    session.delete(user)
    session.commit()
    return None


# Caregiver CRUD endpoints
@app.get("/api/caregivers", response_model=List[CaregiverResponse], tags=["caregivers"])
async def list_caregivers(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """List all caregivers"""
    statement = select(Caregiver).offset(skip).limit(limit)
    caregivers = session.exec(statement).all()
    
    return [caregiver_to_response(caregiver) for caregiver in caregivers]


@app.get("/api/caregivers/{caregiver_id}", response_model=CaregiverResponse, tags=["caregivers"])
async def get_caregiver(caregiver_id: int, session: Session = Depends(get_session)):
    """Get a specific caregiver by ID"""
    caregiver = session.get(Caregiver, caregiver_id)
    if not caregiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Caregiver with id {caregiver_id} not found"
        )
    return caregiver_to_response(caregiver)


@app.post("/api/caregivers", response_model=CaregiverResponse, status_code=status.HTTP_201_CREATED, tags=["caregivers"])
async def create_caregiver(caregiver_data: CaregiverCreate, session: Session = Depends(get_session)):
    """Create a new caregiver"""
    caregiver = Caregiver(
        name=caregiver_data.name,
        gender=caregiver_data.gender,
        description=caregiver_data.description
    )
    
    session.add(caregiver)
    session.commit()
    session.refresh(caregiver)
    
    return caregiver_to_response(caregiver)


@app.put("/api/caregivers/{caregiver_id}", response_model=CaregiverResponse, tags=["caregivers"])
async def update_caregiver(
    caregiver_id: int,
    caregiver_data: CaregiverUpdate,
    session: Session = Depends(get_session)
):
    """Update an existing caregiver"""
    caregiver = session.get(Caregiver, caregiver_id)
    if not caregiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Caregiver with id {caregiver_id} not found"
        )
    
    # Update fields if provided
    if caregiver_data.name is not None:
        caregiver.name = caregiver_data.name
    if caregiver_data.gender is not None:
        caregiver.gender = caregiver_data.gender
    if caregiver_data.description is not None:
        caregiver.description = caregiver_data.description
    
    # Update timestamp
    caregiver.updated_at = datetime.utcnow()
    
    session.add(caregiver)
    session.commit()
    session.refresh(caregiver)
    
    return caregiver_to_response(caregiver)


@app.delete("/api/caregivers/{caregiver_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["caregivers"])
async def delete_caregiver(caregiver_id: int, session: Session = Depends(get_session)):
    """Delete a caregiver"""
    caregiver = session.get(Caregiver, caregiver_id)
    if not caregiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Caregiver with id {caregiver_id} not found"
        )
    
    session.delete(caregiver)
    session.commit()
    return None


# Helper function for caregiver responses
def caregiver_to_response(caregiver: Caregiver) -> CaregiverResponse:
    """Convert Caregiver model to CaregiverResponse"""
    return CaregiverResponse(
        id=caregiver.id,
        name=caregiver.name,
        gender=caregiver.gender,
        description=caregiver.description,
        created_at=caregiver.created_at,
        updated_at=caregiver.updated_at
    )


# Communication Session CRUD endpoints
@app.post("/api/communication/sessions", response_model=CommunicationSessionResponse, status_code=status.HTTP_201_CREATED, tags=["communication"])
async def create_session(session_data: CommunicationSessionCreate, db_session: Session = Depends(get_session)):
    """Create a new communication session"""
    session = CommunicationSession(
        user_id=session_data.user_id,
        caregiver_id=session_data.caregiver_id
    )
    
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    return session_to_response(session, db_session)


@app.get("/api/communication/sessions", response_model=List[CommunicationSessionResponse], tags=["communication"])
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    caregiver_id: Optional[int] = None,
    db_session: Session = Depends(get_session)
):
    """List all communication sessions with optional filtering"""
    statement = select(CommunicationSession)
    
    if user_id is not None:
        statement = statement.where(CommunicationSession.user_id == user_id)
    if caregiver_id is not None:
        statement = statement.where(CommunicationSession.caregiver_id == caregiver_id)
    
    statement = statement.order_by(CommunicationSession.started_at.desc()).offset(skip).limit(limit)
    sessions = db_session.exec(statement).all()
    
    return [session_to_response(session, db_session) for session in sessions]


@app.get("/api/communication/sessions/{session_id}", response_model=CommunicationSessionResponse, tags=["communication"])
async def get_communication_session(session_id: int, db_session: Session = Depends(get_session)):
    """Get a specific communication session by ID with all steps"""
    session = db_session.get(CommunicationSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {session_id} not found"
        )
    return session_to_response(session, db_session)


@app.put("/api/communication/sessions/{session_id}", response_model=CommunicationSessionResponse, tags=["communication"])
async def update_session(
    session_id: int,
    session_data: CommunicationSessionUpdate,
    db_session: Session = Depends(get_session)
):
    """Update an existing communication session (e.g., set ended_at)"""
    session = db_session.get(CommunicationSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {session_id} not found"
        )
    
    if session_data.ended_at is not None:
        session.ended_at = session_data.ended_at
    
    session.updated_at = datetime.utcnow()
    
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    return session_to_response(session, db_session)


@app.delete("/api/communication/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["communication"])
async def delete_session(session_id: int, db_session: Session = Depends(get_session)):
    """Delete a communication session and all its steps"""
    session = db_session.get(CommunicationSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {session_id} not found"
        )
    
    # Delete all steps first
    steps_statement = select(SessionStep).where(SessionStep.session_id == session_id)
    steps = db_session.exec(steps_statement).all()
    for step in steps:
        db_session.delete(step)
    
    db_session.delete(session)
    db_session.commit()
    return None


@app.post("/api/communication/sessions/{session_id}/steps", response_model=SessionStepResponse, status_code=status.HTTP_201_CREATED, tags=["communication"])
async def create_session_step(
    session_id: int,
    step_data: SessionStepCreate,
    db_session: Session = Depends(get_session)
):
    """Create a new step in a communication session"""
    # Verify session exists
    session = db_session.get(CommunicationSession, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {session_id} not found"
        )
    
    # Convert choices list to JSON
    choices_json = None
    if step_data.choices:
        choices_json = [{"text": c.get("text", ""), "probability": c.get("probability", 0.0)} for c in step_data.choices]
    
    step = SessionStep(
        session_id=session_id,
        step_number=step_data.step_number,
        message_role=step_data.message_role,
        message_content=step_data.message_content,
        choices_json=choices_json,
        selected_choice_text=step_data.selected_choice_text
    )
    
    db_session.add(step)
    db_session.commit()
    db_session.refresh(step)
    
    # Update session updated_at
    session.updated_at = datetime.utcnow()
    db_session.add(session)
    db_session.commit()
    
    return step_to_response(step)


# Helper functions for session responses
def step_to_response(step: SessionStep) -> SessionStepResponse:
    """Convert SessionStep model to SessionStepResponse"""
    choices = None
    if step.choices_json:
        choices = [ChoiceData(text=c.get("text", ""), probability=c.get("probability", 0.0)) for c in step.choices_json]
    
    return SessionStepResponse(
        id=step.id,
        session_id=step.session_id,
        step_number=step.step_number,
        message_role=step.message_role,
        message_content=step.message_content,
        choices=choices,
        selected_choice_text=step.selected_choice_text,
        timestamp=step.timestamp
    )


def session_to_response(session: CommunicationSession, db_session: Session) -> CommunicationSessionResponse:
    """Convert CommunicationSession model to CommunicationSessionResponse with steps"""
    # Get all steps for this session
    steps_statement = select(SessionStep).where(SessionStep.session_id == session.id).order_by(SessionStep.step_number)
    steps = db_session.exec(steps_statement).all()
    
    return CommunicationSessionResponse(
        id=session.id,
        user_id=session.user_id,
        caregiver_id=session.caregiver_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        created_at=session.created_at,
        updated_at=session.updated_at,
        steps=[step_to_response(step) for step in steps]
    )


# Configuration file path
CONFIG_FILE = Path(__file__).parent / "config.json"


# Configuration models
class EyeTrackingConfig(BaseModel):
    """Eye tracking configuration model"""
    eye_used: str = "both"  # "left", "right", or "both"
    dwell_time: float = 2.0  # Dwell time in seconds


class ConfigModel(BaseModel):
    """Application configuration model"""
    provider: str = "openai"  # openai, anthropic, google, azure
    model: str = ""
    temperature: float = 0.7
    communicate_prompt: str = ""  # Prompt for communication page
    keyboard_prompt: str = ""  # Prompt for keyboard page (single letters/words)
    keyboard_multiple_letters_prompt: str = ""  # Prompt for keyboard page (multiple letters selected)
    header_height_adjustment: int = 0  # in px
    menu_width_adjustment: int = 0  # in px
    # TTS configuration
    tts_language: str = "fr"  # Language code for TTS (e.g., "fr", "en", "es")
    tts_voice_name: str = ""  # Voice name (e.g., "fr-FR-Standard-B" for Google, empty for default)
    tts_pitch: float = 0.0  # Pitch adjustment (-20.0 to 20.0 semitones)
    tts_speaking_rate: float = 1.0  # Speaking rate (0.25 to 4.0)
    # Eye tracking configuration
    eye_tracking: EyeTrackingConfig = EyeTrackingConfig()


class ConfigResponse(BaseModel):
    """Configuration response model"""
    provider: str
    model: str
    temperature: float
    communicate_prompt: str
    keyboard_prompt: str
    keyboard_multiple_letters_prompt: str
    header_height_adjustment: int
    menu_width_adjustment: int
    tts_language: str
    tts_voice_name: str
    tts_pitch: float
    tts_speaking_rate: float
    eye_tracking: EyeTrackingConfig


def load_config() -> ConfigModel:
    """Load configuration from config.json file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle backward compatibility: migrate old 'prompt' to 'communicate_prompt'
                if 'prompt' in data and 'communicate_prompt' not in data:
                    data['communicate_prompt'] = data['prompt']
                    del data['prompt']
                # Handle backward compatibility: add default keyboard prompts if missing
                if 'keyboard_prompt' not in data:
                    data['keyboard_prompt'] = "You are a helpful assistant that suggests words for text input using eye tracking. Based on the conversation history and current text, suggest 5 words that the user might want to type next."
                if 'keyboard_multiple_letters_prompt' not in data:
                    data['keyboard_multiple_letters_prompt'] = "You are a helpful assistant that suggests words for text input using eye tracking. The user has selected multiple letters. Based on the conversation history, current text, and the selected letters, suggest 5 words that match or could be formed from these letters."
                # Handle backward compatibility: if eye_tracking is missing, add defaults
                if 'eye_tracking' not in data:
                    data['eye_tracking'] = {'eye_used': 'both', 'dwell_time': 2.0}
                return ConfigModel(**data)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # If file is corrupted, return default config
            print(f"Error loading config: {e}")
            return ConfigModel()
    else:
        # Return default config if file doesn't exist
        return ConfigModel()


def save_config(config: ConfigModel) -> None:
    """Save configuration to config.json file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save configuration: {str(e)}"
        )


# Configuration endpoints
@app.get("/api/config", response_model=ConfigResponse, tags=["setup"])
async def get_config():
    """Get current configuration"""
    config = load_config()
    return ConfigResponse(**config.model_dump())


@app.put("/api/config", response_model=ConfigResponse, tags=["setup"])
async def update_config(config: ConfigModel):
    """Update configuration"""
    # Validate provider
    valid_providers = ["openai", "anthropic", "google", "azure"]
    if config.provider not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider. Must be one of: {', '.join(valid_providers)}"
        )
    
    # Validate temperature
    if not 0 <= config.temperature <= 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Temperature must be between 0 and 2"
        )
    
    # Validate eye tracking configuration
    if config.eye_tracking:
        if config.eye_tracking.eye_used not in ["left", "right", "both"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="eye_used must be one of: left, right, both"
            )
        if config.eye_tracking.dwell_time < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="dwell_time must be a positive number"
            )
    
    save_config(config)
    return ConfigResponse(**config.model_dump())


# Speech-to-text WebSocket endpoint
@app.websocket("/ws/speech-to-text")
async def websocket_speech_to_text(websocket: WebSocket):
    """WebSocket endpoint for speech-to-text events."""
    await websocket.accept()
    speech_websocket_connections.add(websocket)
    print(f"WebSocket client connected. Total connections: {len(speech_websocket_connections)}")
    
    # Send initial connection confirmation
    await websocket.send_json({
        "type": "connected",
        "data": {"message": "WebSocket connected"},
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            try:
                data = await websocket.receive_text()
                # Echo back or handle client messages if needed
                await websocket.send_json({"type": "pong", "data": data})
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        speech_websocket_connections.discard(websocket)
        print(f"WebSocket client disconnected. Total connections: {len(speech_websocket_connections)}")


# Speech-to-text API endpoints
@app.post("/api/speech-to-text/start", tags=["speech-to-text"])
async def start_speech_to_text():
    """Start speech-to-text transcription."""
    global speech_to_text_service
    
    if SpeechToTextService is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Speech-to-text service is not available. Please install required dependencies: python-dotenv, deepgram-sdk, pyaudio"
        )
    
    if speech_to_text_service and speech_to_text_service.is_active:
        return {"success": True, "message": "Speech-to-text is already active"}
    
    try:
        print("Creating SpeechToTextService...")
        speech_to_text_service = SpeechToTextService(
            on_speech_started=on_speech_started,
            on_transcription=on_transcription,
            on_error=on_speech_error
        )
        print("Starting speech-to-text service...")
        speech_to_text_service.start(language="fr", model="nova-2")
        print(f"Speech-to-text started. Active: {speech_to_text_service.is_active}")
        return {"success": True, "message": "Speech-to-text started"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start speech-to-text: {str(e)}"
        )


@app.post("/api/speech-to-text/stop", tags=["speech-to-text"])
async def stop_speech_to_text():
    """Stop speech-to-text transcription."""
    global speech_to_text_service
    
    if not speech_to_text_service or not speech_to_text_service.is_active:
        return {"success": True, "message": "Speech-to-text is not active"}
    
    try:
        speech_to_text_service.stop()
        return {"success": True, "message": "Speech-to-text stopped"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop speech-to-text: {str(e)}"
        )


@app.get("/api/speech-to-text/status", tags=["speech-to-text"])
async def get_speech_to_text_status():
    """Get speech-to-text status."""
    global speech_to_text_service
    
    is_active = speech_to_text_service is not None and speech_to_text_service.is_active
    return {
        "is_active": is_active,
        "websocket_connections": len(speech_websocket_connections)
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

