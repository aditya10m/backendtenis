import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy import Uuid as UUID, JSON
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class EventSeverity(str, enum.Enum):
    info = "info"
    positive = "positive"
    warning = "warning"
    negative = "negative"

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID, ForeignKey("analyses.id"))
    event_type = Column(String, nullable=False)
    timestamp_ms = Column(Float, nullable=False)
    end_timestamp_ms = Column(Float, nullable=True)
    description = Column(String, nullable=True)
    severity = Column(Enum(EventSeverity), default=EventSeverity.info)
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="events")
