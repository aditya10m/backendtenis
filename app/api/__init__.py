from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.players import router as players_router
from app.api.videos import router as videos_router
from app.api.analyses import router as analyses_router
from app.api.progress import router as progress_router
from app.api.coach import router as coach_router
from app.api.health import router as health_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(players_router, prefix="/players", tags=["players"])
api_router.include_router(videos_router, prefix="/videos", tags=["videos"])
api_router.include_router(analyses_router, prefix="/analyses", tags=["analyses"])
api_router.include_router(progress_router, prefix="/players/me/progress", tags=["progress"])
api_router.include_router(coach_router, prefix="/coach", tags=["coach"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
