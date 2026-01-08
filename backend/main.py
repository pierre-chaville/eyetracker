from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(title="Eye Tracker API", version="1.0.0")

# CORS middleware for Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "file://"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/")
async def root():
    return {"message": "Eye Tracker API", "status": "running"}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/eye-tracking/start")
async def start_eye_tracking():
    """Start eye tracking session"""
    return {"success": True, "message": "Eye tracking started"}


@app.post("/api/eye-tracking/stop")
async def stop_eye_tracking():
    """Stop eye tracking session"""
    return {"success": True, "message": "Eye tracking stopped"}


@app.get("/api/eye-tracking/status")
async def get_eye_tracking_status():
    """Get current eye tracking status"""
    return {
        "is_active": False,
        "calibration_status": "not_calibrated"
    }


@app.post("/api/communication/interpret")
async def interpret_gaze(request: CommunicationRequest):
    """Interpret gaze points and generate communication suggestions using AI"""
    # TODO: Implement AI/LLM integration for interpreting gaze patterns
    return {
        "interpreted_text": "Hello",
        "confidence": 0.85,
        "suggestions": ["Hello", "Hi there", "Good morning"]
    }


@app.post("/api/calibration/start")
async def start_calibration():
    """Start calibration process"""
    return {"success": True, "message": "Calibration started"}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

