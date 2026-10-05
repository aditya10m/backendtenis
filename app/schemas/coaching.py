from pydantic import BaseModel
from typing import List, Optional
from app.schemas.analysis import DrillResponse

class CoachingReport(BaseModel):
    strengths: List[str]
    weaknesses: List[str]
    priority_improvement: str
    explanation: str
    drills: List[DrillResponse]
    weekly_plan: Optional[str] = None
