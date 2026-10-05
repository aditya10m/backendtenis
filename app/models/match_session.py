import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class MatchType(str, enum.Enum):
    singles = "singles"
    doubles = "doubles"

class MatchSession(Base):
    __tablename__ = "match_sessions"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    analysis_id = Column(UUID, ForeignKey("analyses.id"), nullable=True)
    opponent_name = Column(String, nullable=True)
    surface = Column(String, nullable=True)
    tournament_name = Column(String, nullable=True)
    match_date = Column(DateTime, nullable=True)
    match_type = Column(Enum(MatchType), nullable=True)
    result = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
