from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List

class VideoResponse(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    file_size: int
    duration_seconds: Optional[float] = None
    status: str

class VideoUploadResponse(BaseModel):
    message: str
    video: VideoResponse

class VideoListResponse(BaseModel):
    items: List[VideoResponse]
    total: int
