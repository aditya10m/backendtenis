import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy import Uuid as UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID, ForeignKey("analyses.id"))
    category = Column(String, nullable=False)
    priority = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    explanation = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="recommendations")
