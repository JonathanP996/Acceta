"""
MongoDB Schema Models for Accenta
Pydantic models for data validation and MongoDB document structure
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class SkillLevel(str, Enum):
    """Skill rating levels"""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADEPT = "Adept"
    PRO = "Pro"
    MASTER = "Master"


class PhonemeDeviation(BaseModel):
    """Phoneme deviation data"""
    phoneme: str
    deviation_score: float = Field(..., ge=0.0, le=1.0)
    duration_diff: float
    pitch_diff: float
    stress_pattern: str


class AcousticFeatures(BaseModel):
    """Acoustic features extracted from audio"""
    mfcc_mean: List[float]
    pitch_contour: List[float]
    formant_ratios: List[float]
    intensity: Optional[float] = None


class SessionData(BaseModel):
    """Individual practice/test session data"""
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    language: str
    target_accent: str
    accent_score: float = Field(..., ge=0.0, le=100.0)
    phoneme_deviations: Dict[str, float]  # phoneme -> deviation_score
    acoustic_features: Optional[AcousticFeatures] = None
    exercises: List[str] = []
    feedback_summary: str = ""
    skill_ratings: Dict[str, str] = {}  # skill_name -> SkillLevel
    audio_recording_url: Optional[str] = None


class SkillRating(BaseModel):
    """Individual skill rating"""
    skill_name: str  # e.g., "Pronunciation", "Reduction", "Rhythm", "Articulation"
    level: SkillLevel
    progress_percentage: float = Field(..., ge=0.0, le=100.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(BaseModel):
    """User profile for a specific language/accent"""
    user_id: str
    language: str
    accent: str
    overall_skill_level: SkillLevel = SkillLevel.BEGINNER
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)
    skill_ratings: List[SkillRating] = []
    session_history: List[SessionData] = []
    total_practice_time_minutes: int = 0
    total_sessions: int = 0
    struggle_areas: List[str] = []  # List of phonemes or skills
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    """User authentication and basic info"""
    user_id: str = Field(..., unique=True)
    email: str = Field(..., unique=True)
    username: str
    password_hash: str
    profiles: List[UserProfile] = []  # One profile per language/accent
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None


class Exercise(BaseModel):
    """Practice exercise"""
    exercise_id: str
    title: str
    description: str
    difficulty: str  # "Beginner", "Intermediate", "Advanced"
    phoneme_focus: List[str] = []
    phrase: str
    audio_url: Optional[str] = None


class Feedback(BaseModel):
    """AI-generated feedback"""
    feedback_id: str
    session_id: str
    user_id: str
    accent_score: float
    strengths: List[str] = []
    weaknesses: List[str] = []
    personalized_exercises: List[str] = []
    feedback_summary: str
    tts_audio_url: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class TimelineRecording(BaseModel):
    """Recording saved at milestone for timeline feature"""
    recording_id: str
    user_id: str
    language: str
    accent: str
    phrase: str
    audio_url: str
    accent_score: float
    skill_level: SkillLevel
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    milestone_note: Optional[str] = None

