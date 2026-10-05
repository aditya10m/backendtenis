import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class CoachProfile(Base):
    __tablename__ = "coach_profiles"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    academy_name = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    experience_years = Column(Integer, nullable=True)
    certification = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="coach_profile")
