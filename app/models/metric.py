import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class MetricCategory(str, enum.Enum):
    movement = "movement"
    technique = "technique"
    serve = "serve"
    match_data = "match_data"

class Metric(Base):
    __tablename__ = "metrics"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID, ForeignKey("analyses.id"))
    category = Column(Enum(MetricCategory), nullable=False)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    is_experimental = Column(Boolean, default=False)
    description = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="metrics")
