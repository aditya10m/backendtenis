import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class HandEnum(str, enum.Enum):
    left = "left"
    right = "right"

class BackhandEnum(str, enum.Enum):
    one_handed = "one_handed"
    two_handed = "two_handed"

class SkillLevelEnum(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    professional = "professional"

class PlayerProfile(Base):
    __tablename__ = "player_profiles"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    playing_hand = Column(Enum(HandEnum), nullable=True)
    backhand_type = Column(Enum(BackhandEnum), nullable=True)
    skill_level = Column(Enum(SkillLevelEnum), nullable=True)
    preferred_surface = Column(String, nullable=True)
    height_cm = Column(Integer, nullable=True)
    age = Column(Integer, nullable=True)
    country = Column(String, nullable=True)
    coach_name = Column(String, nullable=True)
    training_frequency = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="player_profile")
