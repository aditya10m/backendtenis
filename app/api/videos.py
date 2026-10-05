from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.video import VideoUploadResponse, VideoResponse, VideoListResponse
from app.services.video_service import VideoService
from app.models.video import Video
from uuid import UUID
import os

router = APIRouter()

@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...), current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    video_service = VideoService(db)
    return await video_service.upload_video(file, current_user.id)

@router.get("", response_model=VideoListResponse)
async def list_videos(skip: int = 0, limit: int = 10, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    video_service = VideoService(db)
    return await video_service.list_videos(current_user.id, skip, limit)

@router.get("/{id}/stream")
async def stream_video(id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.id == id))
    video = result.scalar_one_or_none()
    if video and video.file_path and os.path.exists(video.file_path):
        return FileResponse(video.file_path, media_type=video.mime_type or "video/mp4")
    
    # Fallback to demo video if stored file is missing or in demo mode
    demo_paths = ["../frontend/public/dashboard-bg.mp4", "./storage/demo_match.mp4", "./storage/sample_badminton_match.mp4"]
    for dp in demo_paths:
        if os.path.exists(dp):
            return FileResponse(dp, media_type="video/mp4")
            
    raise HTTPException(status_code=404, detail="Video file not found")

@router.get("/{id}", response_model=VideoResponse)
async def get_video(id: UUID, current_user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    video_service = VideoService(db)
    return await video_service.get_video(id, current_user.id)
