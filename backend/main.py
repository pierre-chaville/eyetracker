from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from sqlmodel import Session, select
import uvicorn
import json
import os
from pathlib import Path
from datetime import datetime

from database import engine, create_db_and_tables, get_session
from models import (
    User, UserCreate, UserUpdate, UserResponse,
    EyeTrackingSetup, CommunicationSettings
)
from calibration import (
    CalibrationRequest,
    CalibrationResponse,
    process_calibration_data,
)

app = FastAPI(title="Eye Tracker API", version="1.0.0")

# CORS middleware for Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


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
        notes=user.notes
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
        notes=user_data.notes
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


# Configuration file path
CONFIG_FILE = Path(__file__).parent / "config.json"


# Configuration models
class ConfigModel(BaseModel):
    """Application configuration model"""
    provider: str = "openai"  # openai, anthropic, google, azure
    model: str = ""
    temperature: float = 0.7
    prompt: str = ""
    header_height_adjustment: int = 0  # in px
    menu_width_adjustment: int = 0  # in px


class ConfigResponse(BaseModel):
    """Configuration response model"""
    provider: str
    model: str
    temperature: float
    prompt: str
    header_height_adjustment: int
    menu_width_adjustment: int


def load_config() -> ConfigModel:
    """Load configuration from config.json file"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
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
    
    save_config(config)
    return ConfigResponse(**config.model_dump())


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

