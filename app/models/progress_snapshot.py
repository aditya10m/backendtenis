import uuid
from datetime import datetime
from sqlalchemy import Column, Float, DateTime, ForeignKey
from sqlalchemy import Uuid as UUID, JSON
from app.core.database import Base

class ProgressSnapshot(Base):
    __tablename__ = "progress_snapshots"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    analysis_id = Column(UUID, ForeignKey("analyses.id"), nullable=True)
    snapshot_date = Column(DateTime, nullable=False)
    overall_score = Column(Float, nullable=True)
    technique_score = Column(Float, nullable=True)
    movement_score = Column(Float, nullable=True)
    serve_score = Column(Float, nullable=True)
    consistency_score = Column(Float, nullable=True)
    match_intelligence_score = Column(Float, nullable=True)
    metrics_summary = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
