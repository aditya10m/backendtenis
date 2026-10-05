from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "demo_mode": settings.DEMO_MODE
    }
