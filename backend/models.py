from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Date, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    has_completed_onboarding = Column(Boolean, default=False)
    
    # Relationship with onboarding data
    onboarding = relationship("OnboardingData", back_populates="user", uselist=False)

class OnboardingData(Base):
    __tablename__ = "onboarding_data"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)  # Added ForeignKey
    exam_name = Column(String, nullable=False)
    exam_date = Column(Date, nullable=False)
    current_preparation_level = Column(String, nullable=False)  # beginner, intermediate, advanced
    daily_study_hours = Column(Integer, nullable=False)
    preferred_study_time = Column(String, nullable=False)  # morning, afternoon, evening, night
    topics_covered = Column(JSON, nullable=True)  # List of topics already covered
    weak_subjects = Column(JSON, nullable=True)  # List of subjects they struggle with
    strong_subjects = Column(JSON, nullable=True)  # List of subjects they're good at
    additional_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship with user
    user = relationship("User", back_populates="onboarding")