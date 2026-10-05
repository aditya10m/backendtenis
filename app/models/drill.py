import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy import Uuid as UUID
import enum
from app.core.database import Base

class DifficultyLevel(str, enum.Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class Drill(Base):
    __tablename__ = "drills"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    recommendation_id = Column(UUID, ForeignKey("recommendations.id"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    sets = Column(Integer, nullable=True)
    repetitions = Column(Integer, nullable=True)
    difficulty = Column(Enum(DifficultyLevel), nullable=True)
    purpose = Column(String, nullable=True)
    equipment_needed = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
