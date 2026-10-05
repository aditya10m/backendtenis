from pydantic import BaseModel
from typing import Optional


class ProgressSnapshotResponse(BaseModel):
    date: str = ""
    overall_score: Optional[float] = None
    technique_score: Optional[float] = None
    movement_score: Optional[float] = None
    serve_score: Optional[float] = None
    consistency_score: Optional[float] = None


class ProgressResponse(BaseModel):
    period: str
    snapshots: list[ProgressSnapshotResponse] = []
