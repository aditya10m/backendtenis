import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class AnalysisType(str, enum.Enum):
    match = "match"
    training = "training"
    serve = "serve"
    forehand = "forehand"
    backhand = "backhand"
    footwork = "footwork"

class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    extracting_frames = "extracting_frames"
    detecting_player = "detecting_player"
    estimating_pose = "estimating_pose"
    analyzing_movement = "analyzing_movement"
    calculating_metrics = "calculating_metrics"
    generating_report = "generating_report"
    completed = "completed"
    failed = "failed"

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    video_id = Column(UUID, ForeignKey("videos.id"))
    analysis_type = Column(Enum(AnalysisType), nullable=False)
    status = Column(Enum(AnalysisStatus), default=AnalysisStatus.pending)
    progress = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    metrics = relationship("Metric", back_populates="analysis")
    events = relationship("Event", back_populates="analysis")
    recommendations = relationship("Recommendation", back_populates="analysis")
