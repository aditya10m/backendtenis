from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class AnalysisCreate(BaseModel):
    video_id: UUID
    analysis_type: str = "match"


class AnalysisStatusResponse(BaseModel):
    id: UUID
    status: str
    progress: int


class MetricResponse(BaseModel):
    name: str
    value: Optional[float] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    confidence: Optional[float] = None
    is_experimental: bool = False
    description: Optional[str] = None


class EventResponse(BaseModel):
    event_type: str
    timestamp_ms: int = 0
    end_timestamp_ms: Optional[int] = None
    description: Optional[str] = None
    severity: str = "info"


class DrillResponse(BaseModel):
    name: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    sets: Optional[int] = None
    repetitions: Optional[int] = None
    difficulty: Optional[str] = None
    purpose: Optional[str] = None
    equipment_needed: Optional[str] = None


class RecommendationResponse(BaseModel):
    category: str = ""
    priority: int = 0
    title: str
    description: Optional[str] = None
    explanation: Optional[str] = None
    drills: list[DrillResponse] = []


class ScoresResponse(BaseModel):
    overall: Optional[float] = None
    technique: Optional[float] = None
    movement: Optional[float] = None
    serve: Optional[float] = None
    consistency: Optional[float] = None


class AnalysisReportResponse(BaseModel):
    id: UUID
    status: str
    analysis_type: str
    video_url: Optional[str] = None
    scores: Optional[ScoresResponse] = None
    metrics: list[MetricResponse] = []
    events: list[EventResponse] = []
    recommendations: list[RecommendationResponse] = []


class AnalysisListResponse(BaseModel):
    id: UUID
    status: str
    analysis_type: str
    progress: int = 0
    created_at: Optional[str] = None
