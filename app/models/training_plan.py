import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy import Uuid as UUID, JSON
from app.core.database import Base

class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    frequency_per_week = Column(Integer, nullable=True)
    focus_areas = Column(JSON, nullable=True)
    drills = Column(JSON, nullable=True)  # JSON list of drill references

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
