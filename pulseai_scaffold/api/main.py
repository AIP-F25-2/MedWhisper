# main.py

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import os, httpx, logging
from dotenv import load_dotenv
from typing import Optional

# Load environment variables BEFORE importing database
load_dotenv()

# Import database after loading .env
from database import db

# Optional OpenAI import (only needed if using OpenAI backend)
try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
except ImportError:
    pass  # OpenAI not required if using Gemini backend
logger = logging.getLogger("medwhisper")
logging.basicConfig(level=logging.INFO)

# Backend selection: 'rasa' or 'gemini'. Default to 'gemini'.
QA_BACKEND = os.getenv("QA_BACKEND", "gemini").lower()
GEMINI_QA_URL = os.getenv("GEMINI_QA_URL", "https://b946f3a056f1.ngrok-free.app/ml/qa")

app = FastAPI(title="Med-Whisper Gateway")

# Allow the React dev server to call the API
# (add more origins if you use a different port or host)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    sender: str
    message: str

# Authentication models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileRequest(BaseModel):
    user_id: int
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None



from fastapi.responses import StreamingResponse, JSONResponse
import asyncio

# Authentication endpoints
@app.post("/auth/signup")
async def signup(request: SignupRequest):
    """Register a new user."""
    try:
        logger.info(f"Signup attempt for email: {request.email}")
        
        # Validate password length
        if len(request.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Create user
        user_id = db.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        
        if user_id is None:
            raise HTTPException(status_code=409, detail="Email already registered")
        
        # Get user data
        user_data = db.authenticate_user(request.email, request.password)
        
        return JSONResponse(content={
            "success": True,
            "message": "User created successfully",
            "user": user_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in signup: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/auth/login")
async def login(request: LoginRequest):
    """Authenticate user and return user data."""
    try:
        logger.info(f"Login attempt for email: {request.email}")
        
        user_data = db.authenticate_user(request.email, request.password)
        
        if user_data is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return JSONResponse(content={
            "success": True,
            "message": "Login successful",
            "user": user_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/auth/profile")
async def update_profile(request: ProfileRequest):
    """Update user profile information."""
    try:
        logger.info(f"Profile update attempt for user_id: {request.user_id}")
        
        profile_data = {
            'phone': request.phone,
            'date_of_birth': request.date_of_birth,
            'gender': request.gender,
            'address': request.address,
            'emergency_contact': request.emergency_contact,
            'medical_history': request.medical_history,
            'allergies': request.allergies,
            'current_medications': request.current_medications,
            'insurance_provider': request.insurance_provider,
            'insurance_number': request.insurance_number
        }
        
        success = db.update_user_profile(request.user_id, profile_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update profile")
        
        return JSONResponse(content={
            "success": True,
            "message": "Profile updated successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_profile: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat")
async def chat(req: ChatRequest):
    """Forward message to OpenAI with streaming if API key is set, else Rasa. Returns AI reply."""
    logger.info(f"/chat from sender={req.sender!r}: {req.message!r} -> backend={QA_BACKEND}")
    try:
        reply = ""
        if QA_BACKEND == "rasa":
            rasa_url = "http://localhost:5005/webhooks/rest/webhook"
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    rasa_url,
                    json={"sender": req.sender, "message": req.message},
                    headers={"Content-Type": "application/json"},
                )
                r.raise_for_status()
                logger.info(f"Raw Rasa response: {r.text}")
                data = r.json()
            replies = [m.get("text") for m in data if isinstance(m, dict) and "text" in m]
            reply = replies[0] if replies else "Sorry, I couldn't answer that."
            # Recursively unwrap reply if it is a JSON string with 'replies' or 'text'
            def extract_plain_text(val):
                import json
                if isinstance(val, str) and val.strip().startswith("{"):
                    try:
                        parsed = json.loads(val)
                        if isinstance(parsed, dict):
                            if parsed.get("text") and isinstance(parsed["text"], str):
                                return extract_plain_text(parsed["text"])
                            if parsed.get("replies") and isinstance(parsed["replies"], list) and parsed["replies"]:
                                return extract_plain_text(parsed["replies"][0])
                    except Exception as inner_json_err:
                        logger.error(f"Inner JSON decode error: {inner_json_err}. Raw reply: {val}")
                        pass
                return val
            reply = extract_plain_text(reply)
        else:
            # Use Gemini QA
            async with httpx.AsyncClient(timeout=10) as client:
                payload = {"q": req.message, "role": "doctor"}
                r = await client.post(
                    GEMINI_QA_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                r.raise_for_status()
                logger.info(f"Raw Gemini QA response: {r.text}")
                data = r.json()
            # For doctor role, include confidence and citations if available
            reply = data.get("answer_text") or data.get("answer") or data.get("text") or "Sorry, I couldn't answer that."
            
            # Add confidence and citations for doctor responses
            if "confidence" in data:
                reply += f"\n\nConfidence: {data['confidence']}"
            if "citations" in data and data["citations"]:
                citations_str = ", ".join(data["citations"])
                reply += f"\nCitations: {citations_str}"
        return JSONResponse(content={"text": reply})
    except Exception as e:
        logger.error(f"Error in /chat: {e}")
        return JSONResponse(content={"text": f"[ERROR]: {str(e)}"}, status_code=500)

# ========== DASHBOARD & PATIENT ENDPOINTS ==========

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics (active patients, appointments, alerts, queue)."""
    try:
        stats = db.get_dashboard_stats()
        return JSONResponse(content={
            "success": True,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/patients")
async def get_patients(limit: int = 100, offset: int = 0):
    """Get list of all patients with pagination."""
    try:
        patients = db.get_all_patients(limit=limit, offset=offset)
        # Convert datetime objects to strings for JSON serialization
        for patient in patients:
            if patient.get('created_at'):
                patient['created_at'] = patient['created_at'].isoformat() if hasattr(patient['created_at'], 'isoformat') else str(patient['created_at'])
            if patient.get('updated_at'):
                patient['updated_at'] = patient['updated_at'].isoformat() if hasattr(patient['updated_at'], 'isoformat') else str(patient['updated_at'])
            if patient.get('date_of_birth'):
                patient['date_of_birth'] = patient['date_of_birth'].isoformat() if hasattr(patient['date_of_birth'], 'isoformat') else str(patient['date_of_birth'])
        
        return JSONResponse(content={
            "success": True,
            "patients": patients,
            "total": db.get_patient_count()
        })
    except Exception as e:
        logger.error(f"Error getting patients: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: int):
    """Get a specific patient by ID."""
    try:
        patient = db.get_patient_by_id(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Convert datetime objects to strings
        if patient.get('created_at'):
            patient['created_at'] = patient['created_at'].isoformat() if hasattr(patient['created_at'], 'isoformat') else str(patient['created_at'])
        if patient.get('updated_at'):
            patient['updated_at'] = patient['updated_at'].isoformat() if hasattr(patient['updated_at'], 'isoformat') else str(patient['updated_at'])
        if patient.get('date_of_birth'):
            patient['date_of_birth'] = patient['date_of_birth'].isoformat() if hasattr(patient['date_of_birth'], 'isoformat') else str(patient['date_of_birth'])
        
        return JSONResponse(content={
            "success": True,
            "patient": patient
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting patient: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/appointments")
async def get_appointments(patient_id: Optional[int] = None, limit: int = 50):
    """Get appointments, optionally filtered by patient."""
    try:
        appointments = db.get_appointments(limit=limit, patient_id=patient_id)
        # Convert datetime objects to strings
        for apt in appointments:
            if apt.get('appointment_date'):
                apt['appointment_date'] = apt['appointment_date'].isoformat() if hasattr(apt['appointment_date'], 'isoformat') else str(apt['appointment_date'])
            if apt.get('created_at'):
                apt['created_at'] = apt['created_at'].isoformat() if hasattr(apt['created_at'], 'isoformat') else str(apt['created_at'])
        
        return JSONResponse(content={
            "success": True,
            "appointments": appointments
        })
    except Exception as e:
        logger.error(f"Error getting appointments: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/tasks")
async def get_tasks(user_id: Optional[int] = None, status: Optional[str] = None):
    """Get tasks, optionally filtered by user and status."""
    try:
        tasks = db.get_tasks(user_id=user_id, status=status)
        # Convert datetime objects to strings
        for task in tasks:
            if task.get('created_at'):
                task['created_at'] = task['created_at'].isoformat() if hasattr(task['created_at'], 'isoformat') else str(task['created_at'])
            if task.get('due_date'):
                task['due_date'] = task['due_date'].isoformat() if hasattr(task['due_date'], 'isoformat') else str(task['due_date'])
            if task.get('completed_at'):
                task['completed_at'] = task['completed_at'].isoformat() if hasattr(task['completed_at'], 'isoformat') else str(task['completed_at'])
        
        return JSONResponse(content={
            "success": True,
            "tasks": tasks
        })
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/patients/{patient_id}/vitals")
async def get_patient_vitals(patient_id: int, limit: int = 10):
    """Get recent vital signs for a patient."""
    try:
        vitals = db.get_patient_vitals(patient_id, limit=limit)
        # Convert datetime objects to strings
        for vital in vitals:
            if vital.get('recorded_at'):
                vital['recorded_at'] = vital['recorded_at'].isoformat() if hasattr(vital['recorded_at'], 'isoformat') else str(vital['recorded_at'])
        
        return JSONResponse(content={
            "success": True,
            "vitals": vitals
        })
    except Exception as e:
        logger.error(f"Error getting vitals: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
