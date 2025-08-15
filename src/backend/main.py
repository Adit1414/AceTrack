from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from schemas import UserCreate, UserLogin, UserResponse
from crud import get_user_by_email, create_user
from auth import verify_password, create_access_token

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="StudyPlanner API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "StudyPlanner API is running!"}

@app.post("/signup", response_model=UserResponse)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(
            status_code=400, 
            detail="Email already registered"
        )
    
    # Create new user
    try:
        new_user = create_user(db, user)
        return UserResponse(id=new_user.id, email=new_user.email)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    # Get user from database
    db_user = get_user_by_email(db, user.email)
    
    # Verify user exists and password is correct
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=401, 
            detail="Invalid email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": db_user.email, "user_id": db_user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "email": db_user.email
        }
    }