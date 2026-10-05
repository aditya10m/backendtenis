import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    player = "player"
    coach = "coach"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_coach = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.player)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    player_profile = relationship("PlayerProfile", back_populates="user", uselist=False)
    coach_profile = relationship("CoachProfile", back_populates="user", uselist=False)
