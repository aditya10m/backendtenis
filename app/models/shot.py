import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy import Uuid as UUID
import enum
from app.core.database import Base

class ShotType(str, enum.Enum):
    forehand = "forehand"
    backhand = "backhand"
    serve = "serve"
    volley = "volley"
    overhead = "overhead"
    drop_shot = "drop_shot"
    lob = "lob"

class Shot(Base):
    __tablename__ = "shots"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID, ForeignKey("analyses.id"))
    shot_type = Column(Enum(ShotType), nullable=False)
    timestamp_ms = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=True)
    speed_estimate = Column(Float, nullable=True)
    spin_estimate = Column(Float, nullable=True)
    placement = Column(String, nullable=True)
    is_winner = Column(Boolean, default=False)
    is_error = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
