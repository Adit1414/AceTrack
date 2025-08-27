from sqlalchemy.orm import Session
from models import User, OnboardingData
from schemas import UserCreate, OnboardingCreate, OnboardingUpdate
from auth import hash_password

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate):
    hashed_pw = hash_password(user.password)
    db_user = User(email=user.email, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_onboarding_status(db: Session, user_id: int, status: bool = True):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.has_completed_onboarding = status
        db.commit()
        db.refresh(db_user)
    return db_user

def create_onboarding_data(db: Session, user_id: int, onboarding: OnboardingCreate):
    db_onboarding = OnboardingData(
        user_id=user_id,
        exam_name=onboarding.exam_name,
        exam_date=onboarding.exam_date,
        current_preparation_level=onboarding.current_preparation_level,
        daily_study_hours=onboarding.daily_study_hours,
        preferred_study_time=onboarding.preferred_study_time,
        topics_covered=onboarding.topics_covered,
        weak_subjects=onboarding.weak_subjects,
        strong_subjects=onboarding.strong_subjects,
        additional_notes=onboarding.additional_notes
    )
    db.add(db_onboarding)
    db.commit()
    db.refresh(db_onboarding)
    return db_onboarding

def get_onboarding_data_by_user_id(db: Session, user_id: int):
    return db.query(OnboardingData).filter(OnboardingData.user_id == user_id).first()

def update_onboarding_data(db: Session, user_id: int, onboarding_update: OnboardingUpdate):
    db_onboarding = db.query(OnboardingData).filter(OnboardingData.user_id == user_id).first()
    if db_onboarding:
        update_data = onboarding_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_onboarding, field, value)
        db.commit()
        db.refresh(db_onboarding)
    return db_onboarding

def delete_onboarding_data(db: Session, user_id: int):
    db_onboarding = db.query(OnboardingData).filter(OnboardingData.user_id == user_id).first()
    if db_onboarding:
        db.delete(db_onboarding)
        db.commit()
        return True
    return False