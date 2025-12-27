from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User
from schemas import (
    UserCreate, UserLogin, UserResponse,
    OnboardingCreate, OnboardingResponse, OnboardingUpdate
)
from crud import (
    get_user_by_email, create_user, get_user_by_id,
    create_onboarding_data, get_onboarding_data_by_user_id,
    update_onboarding_data, update_user_onboarding_status,
    get_syllabuses_by_user_id, get_syllabus_by_id,
    parse_syllabus_file, create_user_syllabus, delete_syllabus_by_id
)
from auth import verify_password, create_access_token, get_current_user_from_token

from typing import Dict, List, Optional
from pydantic import BaseModel
import os
import sys

# Since uvicorn runs from 'src', Python can find MockTestAutomation directly
from services.Generation import run_generation_task
from services.PromptsDict import prompt_templates


Base.metadata.create_all(bind=engine)

app = FastAPI(title="AceTrack API", version="1.0.0")

# --- Pydantic Models for Mock Test Generator ---
class QuestionGenerationRequest(BaseModel):
    question_plan: Dict[str, int]
    testing_mode: bool = False
    exam_name: str
    output_format: str = 'pdf'
    questions_per_chunk: int
    syllabus_id: int  # Added syllabus_id

class QuestionGenerationResponse(BaseModel):
    success: bool
    message: str
    files: Optional[Dict[str, str]] = None

class QuestionType(BaseModel):
    name: str
    description: str

class SyllabusResponse(BaseModel):
    id: int
    name: str
    created_at: str
    topic_count: int


# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Database Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===============================================================
# === MOCK TEST GENERATOR API ENDPOINTS ===
# ===============================================================

@app.get("/api/question-types", response_model=List[QuestionType])
async def get_question_types():
    descriptions = {
        "MTF": "Match the Following questions.", "2S": "Two-statement reasoning questions.",
        "3S": "Three-statement analysis questions.", "4S": "Four-statement analysis questions.",
        "5S": "Five-statement, highly analytical questions.", "SL": "Single-liner scenario-based questions.",
        "AR": "Assertion and Reasoning questions.", "CS": "Case study comprehension questions.",
        "CH": "Chronological ordering questions.", "FU": "Fill in the Blanks questions.",
        "MCQ": "Multiple choice questions.", "NU": "Numerical answer type questions."
    }
    try:
        if not prompt_templates:
            raise HTTPException(status_code=500, detail="Prompt templates are not loaded.")
        return [
            QuestionType(name=qtype, description=descriptions.get(qtype, f"Generate {qtype} questions."))
            for qtype in prompt_templates.keys()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading question types: {str(e)}")


@app.post("/api/generate-questions", response_model=QuestionGenerationResponse)
async def generate_questions(
    request: QuestionGenerationRequest,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(User.id == current_user["user_id"]).first()
        if not user or not user.is_authorized:
            raise HTTPException(
                status_code=403, 
                detail="Your account does not have generation permissions yet. Please contact support."
            )
        # Fetch the syllabus to get the topics
        syllabus = get_syllabus_by_id(db, request.syllabus_id, current_user["user_id"])
        if not syllabus:
            raise HTTPException(status_code=404, detail="Syllabus not found or you don't have access to it")
        
        # Pass the topics to the generation task
        result = run_generation_task(
            plan=request.question_plan,
            testing_mode=request.testing_mode,
            exam_name=request.exam_name,
            output_format=request.output_format,
            questions_per_chunk=request.questions_per_chunk,
            topics=syllabus.topics  # Pass the topics from the syllabus
        )
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred in the API: {str(e)}")

@app.get("/api/wakeup")
async def wakeup():
    return {"mssg":"I am ready"}

@app.get("/api/download-questions/{filename}")
async def download_questions_file(
    filename: str,
    current_user: dict = Depends(get_current_user_from_token)
):
    """Download generated question files securely."""
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    file_dir = os.path.join(current_script_dir, "data", "generated_files")
    file_path = os.path.join(file_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found. Searched at: {file_path}")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf'
    )

# ===============================================================
# === SYLLABUS API ENDPOINTS ===
# ===============================================================

@app.get("/api/syllabus", response_model=List[SyllabusResponse])
async def get_user_syllabuses(
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get all syllabuses for the current user"""
    syllabuses = get_syllabuses_by_user_id(db, current_user["user_id"])
    return [
        SyllabusResponse(
            id=s.id,
            name=s.name,
            created_at=s.created_at.isoformat(),
            topic_count=len(s.topics)
        )
        for s in syllabuses
    ]

@app.post("/api/syllabus/upload")
async def upload_syllabus(
    name: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Upload a new syllabus file"""
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only .xlsx and .xls files are allowed."
            )
        
        # Parse the file
        topics = parse_syllabus_file(file.file)
        
        # Create syllabus in database
        syllabus = create_user_syllabus(db, current_user["user_id"], name, topics)
        
        return SyllabusResponse(
            id=syllabus.id,
            name=syllabus.name,
            created_at=syllabus.created_at.isoformat(),
            topic_count=len(syllabus.topics)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload syllabus: {str(e)}")

@app.delete("/api/syllabus/{syllabus_id}")
async def delete_syllabus(
    syllabus_id: int,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a syllabus"""
    success = delete_syllabus_by_id(db, syllabus_id, current_user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail="Syllabus not found")
    return {"message": "Syllabus deleted successfully"}

# ===============================================================
# === USER AUTH & ONBOARDING ENDPOINTS ===
# ===============================================================

@app.get("/")
def read_root(): 
    return {"message": "AceTrack API is running!"}

@app.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user: 
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = create_user(db, user)
    return UserResponse(id=new_user.id, email=new_user.email, has_completed_onboarding=new_user.has_completed_onboarding)

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    access_token = create_access_token(data={"sub": db_user.email, "user_id": db_user.id})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": {
            "id": db_user.id, 
            "email": db_user.email, 
            "has_completed_onboarding": db_user.has_completed_onboarding
        }
    }

@app.get("/me", response_model=UserResponse)
def get_current_user(current_user: dict = Depends(get_current_user_from_token), db: Session = Depends(get_db)):
    user = get_user_by_id(db, current_user["user_id"])
    if not user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(id=user.id, email=user.email, has_completed_onboarding=user.has_completed_onboarding)

@app.post("/onboarding", response_model=OnboardingResponse)
def create_user_onboarding(onboarding_data: OnboardingCreate, current_user: dict = Depends(get_current_user_from_token), db: Session = Depends(get_db)):
    user_id = current_user["user_id"]
    if get_onboarding_data_by_user_id(db, user_id): 
        raise HTTPException(status_code=400, detail="User has already completed onboarding. Use PUT to update.")
    db_onboarding = create_onboarding_data(db, user_id, onboarding_data)
    update_user_onboarding_status(db, user_id, True)
    return db_onboarding

@app.get("/onboarding", response_model=OnboardingResponse)
def get_user_onboarding(current_user: dict = Depends(get_current_user_from_token), db: Session = Depends(get_db)):
    user_id = current_user["user_id"]
    onboarding_data = get_onboarding_data_by_user_id(db, user_id)
    if not onboarding_data: 
        raise HTTPException(status_code=404, detail="Onboarding data not found")
    return onboarding_data

@app.put("/onboarding", response_model=OnboardingResponse)
def update_user_onboarding(onboarding_update: OnboardingUpdate, current_user: dict = Depends(get_current_user_from_token), db: Session = Depends(get_db)):
    user_id = current_user["user_id"]
    if not get_onboarding_data_by_user_id(db, user_id): 
        raise HTTPException(status_code=404, detail="Onboarding data not found. Create it first using POST.")
    try:
        updated_onboarding = update_onboarding_data(db, user_id, onboarding_update)
        return updated_onboarding
    except Exception as e:
        print(f"Error updating onboarding data: {e}")
        raise HTTPException(status_code=500, detail="Failed to update onboarding data")
    
@app.get("/onboarding/status")
def check_onboarding_status(current_user: dict = Depends(get_current_user_from_token), db: Session = Depends(get_db)):
    user = get_user_by_id(db, current_user["user_id"])
    if not user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"has_completed_onboarding": user.has_completed_onboarding, "user_id": user.id}