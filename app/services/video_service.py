import uuid
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.video import Video, VideoStatus
from app.services.storage_service import LocalStorageService
from app.core.config import settings
from math import ceil

class VideoService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage = LocalStorageService()
        
    async def upload_video(self, file: UploadFile, user_id):
        ext = file.filename.split('.')[-1].lower()
        if ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Invalid extension")
            
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
        
        if size > settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")
            
        new_filename = f"{uuid.uuid4()}.{ext}"
        file_path = await self.storage.save_file(file, new_filename)
        mime_type = file.content_type or "video/mp4"

        # If file is a zip archive of frames (e.g. ezgif extract), compile into streaming MP4
        if ext == "zip":
            import zipfile, re, cv2, numpy as np, os
            try:
                mp4_filename = f"{uuid.uuid4()}.mp4"
                mp4_path = os.path.join(self.storage.storage_path, mp4_filename)
                with zipfile.ZipFile(file_path, "r") as zf:
                    names = [n for n in zf.namelist() if n.lower().endswith((".jpg", ".jpeg", ".png"))]
                    names.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r"(\d+)", x)])
                    if names:
                        first_img = cv2.imdecode(np.frombuffer(zf.read(names[0]), np.uint8), cv2.IMREAD_COLOR)
                        if first_img is not None:
                            h, w = first_img.shape[:2]
                            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
                            vw = cv2.VideoWriter(mp4_path, fourcc, 15.0, (w, h))
                            for n in names:
                                img = cv2.imdecode(np.frombuffer(zf.read(n), np.uint8), cv2.IMREAD_COLOR)
                                if img is not None:
                                    vw.write(img)
                            vw.release()
                            file_path = mp4_path
                            new_filename = mp4_filename
                            mime_type = "video/mp4"
            except Exception as e:
                print(f"Error converting zip frames to mp4: {e}")

        video = Video(
            user_id=user_id,
            filename=new_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=size,
            mime_type=mime_type,
            status=VideoStatus.uploaded
        )
        self.db.add(video)
        await self.db.commit()
        await self.db.refresh(video)
        return {"message": "Upload successful", "video": video}
        
    async def list_videos(self, user_id, skip: int, limit: int):
        result = await self.db.execute(select(Video).where(Video.user_id == user_id).offset(skip).limit(limit))
        items = result.scalars().all()
        return {"items": items, "total": len(items)}
        
    async def get_video(self, video_id, user_id):
        result = await self.db.execute(select(Video).where(Video.id == video_id, Video.user_id == user_id))
        video = result.scalar_one_or_none()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        return video
