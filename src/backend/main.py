from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from backend.models import User
from backend.schemas import (
    UserCreate, UserLogin, UserResponse, 
    OnboardingCreate, OnboardingResponse, OnboardingUpdate
)
from backend.crud import (
    get_user_by_email, create_user, get_user_by_id,
    create_onboarding_data, get_onboarding_data_by_user_id,
    update_onboarding_data, update_user_onboarding_status
)
from backend.auth import verify_password, create_access_token, get_current_user_from_token

from typing import Dict, List, Optional
from pydantic import BaseModel
import os
import sys

# --- Mock Test Generator Integration ---
# Ensure the script path is correct relative to where you run uvicorn
# If you run `uvicorn main:app` from the project root, this path should be correct.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src/MockTestAutomation')))
from automation.MockTestAutomation.Generation import run_generation_task
from automation.MockTestAutomation.PromptsDict import prompt_templates


# --- Create Database Tables ---
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AceTrack API", version="1.0.0")

# --- Pydantic Models for Mock Test Generator ---
class QuestionGenerationRequest(BaseModel):
    question_plan: Dict[str, int]
    testing_mode: bool = False
    exam_name: str

class QuestionGenerationResponse(BaseModel):
    success: bool
    message: str
    files: Optional[Dict[str, str]] = None

class QuestionType(BaseModel):
    name: str
    description: str


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
    """Get available question types from PromptsDict.py"""
    descriptions = {
        "MTF": "Match the Following questions.",
        "2S": "Two-statement reasoning questions.",
        "3S": "Three-statement analysis questions.",
        "4S": "Four-statement analysis questions.",
        "5S": "Five-statement, highly analytical questions.",
        "SL": "Single-liner scenario-based questions.",
        "AR": "Assertion and Reasoning questions.",
        "CS": "Case study comprehension questions.",
        "CH": "Chronological ordering questions.",
        "FU": "Fill in the Blanks questions.",
        "MCQ": "Multiple choice questions.",
        "NU": "Numerical answer type questions."
    }
    try:
        return [
            QuestionType(name=qtype, description=descriptions.get(qtype, f"Generate {qtype} questions."))
            for qtype in prompt_templates.keys()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading question types: {str(e)}")


@app.post("/api/generate-questions", response_model=QuestionGenerationResponse)
async def generate_questions(
    request: QuestionGenerationRequest,
    current_user: dict = Depends(get_current_user_from_token)
):
    """
    Generate questions by directly calling the generation script.
    This runs synchronously. For long tasks, consider background tasks.
    """
    try:
        # The generation logic is now a direct function call
        result = run_generation_task(
            plan=request.question_plan,
            testing_mode=request.testing_mode,
            exam_name=request.exam_name
        )
        
        if result["success"]:
            return QuestionGenerationResponse(
                success=True,
                message=result["message"],
                files=result["files"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.get("/api/download-questions/{filename}")
async def download_questions_file(
    filename: str,
    current_user: dict = Depends(get_current_user_from_token)
):
    """Download generated question files securely."""
    # Prevent path traversal attacks
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    
    # Files are stored in the 'generated_files' directory by the script
    file_path = os.path.join("generated_files", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found. It may have expired or failed to generate.")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


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
    return UserResponse(
        id=new_user.id, 
        email=new_user.email, 
        has_completed_onboarding=new_user.has_completed_onboarding
    )

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": db_user.email, "user_id": db_user.id})
    return {
        "access_token": access_token, "token_type": "bearer",
        "user": {
            "id": db_user.id, "email": db_user.email,
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
def get_user_onboarding(
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get onboarding data for the current user"""
    user_id = current_user["user_id"]
    
    onboarding_data = get_onboarding_data_by_user_id(db, user_id)
    if not onboarding_data:
        raise HTTPException(
            status_code=404,
            detail="Onboarding data not found"
        )
    
    return onboarding_data

@app.put("/onboarding", response_model=OnboardingResponse)
def update_user_onboarding(
    onboarding_update: OnboardingUpdate,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update onboarding data for the current user"""
    user_id = current_user["user_id"]
    
    # Check if onboarding data exists
    existing_onboarding = get_onboarding_data_by_user_id(db, user_id)
    if not existing_onboarding:
        raise HTTPException(
            status_code=404,
            detail="Onboarding data not found. Create it first using POST."
        )
    
    try:
        updated_onboarding = update_onboarding_data(db, user_id, onboarding_update)
        return updated_onboarding
    except Exception as e:
        print(f"Error updating onboarding data: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update onboarding data"
        )

@app.get("/onboarding/status")
def check_onboarding_status(
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Check if user has completed onboarding"""
    user = get_user_by_id(db, current_user["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "has_completed_onboarding": user.has_completed_onboarding,
        "user_id": user.id
    }