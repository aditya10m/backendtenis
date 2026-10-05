from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, get_optional_current_user
from app.schemas.analysis import AnalysisCreate, AnalysisStatusResponse, AnalysisReportResponse, MetricResponse, AnalysisListResponse
from app.schemas.coaching import CoachingReport
from app.services.analysis_service import AnalysisService
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

router = APIRouter()

class SampleAnalysisRequest(BaseModel):
    analysis_type: str = "match"

@router.get("", response_model=List[AnalysisListResponse])
async def list_analyses(skip: int = 0, limit: int = 20, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    analysis_service = AnalysisService(db)
    return await analysis_service.list_user_analyses(current_user.id, skip, limit)

@router.post("/sample", response_model=AnalysisReportResponse)
async def create_sample(data: Optional[SampleAnalysisRequest] = None, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    raise HTTPException(
        status_code=410,
        detail="Sample reports were removed. Upload a video to receive measured pose analysis.",
    )

@router.post("", response_model=AnalysisStatusResponse)
async def create_analysis(data: AnalysisCreate, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    analysis_service = AnalysisService(db)
    return await analysis_service.create_analysis(data, current_user.id)

@router.get("/{id}", response_model=AnalysisReportResponse)
async def get_analysis(id: UUID, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    analysis_service = AnalysisService(db)
    return await analysis_service.get_analysis(id, current_user.id)

@router.get("/{id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(id: UUID, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    analysis_service = AnalysisService(db)
    return await analysis_service.get_status(id, current_user.id)

@router.get("/{id}/report", response_model=AnalysisReportResponse)
async def get_analysis_report(id: UUID, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    analysis_service = AnalysisService(db)
    return await analysis_service.get_report(id, current_user.id)

@router.get("/{id}/metrics", response_model=List[MetricResponse])
async def get_analysis_metrics(id: UUID, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    analysis_service = AnalysisService(db)
    return await analysis_service.get_metrics(id, current_user.id)

@router.get("/{id}/coaching", response_model=CoachingReport)
async def get_analysis_coaching(id: UUID, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    analysis_service = AnalysisService(db)
    return await analysis_service.get_coaching(id, current_user.id)

@router.get("/{id}/skeleton")
async def get_analysis_skeleton(id: str, current_user = Depends(get_optional_current_user), db: AsyncSession = Depends(get_db)):
    analysis_service = AnalysisService(db)
    user_id = current_user.id if current_user else None
    return await analysis_service.get_skeleton_analysis(id, user_id)
