from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import settings
import os
import logging
import traceback

logger = logging.getLogger(__name__)

app = FastAPI(title="BadmintonAI Coach API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://badminton-peach-eta.vercel.app",
        "https://badminton-ftlvs9l7s-vipraoil-s-projects.vercel.app",
        "http://localhost:3000",
        "http://localhost:8081",
        "http://localhost:19006",
        "http://localhost:8080",
    ],
    # Matches ALL *.vercel.app preview and production URLs + onrender.com + localhost
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.onrender\.com|http://localhost(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.method} {request.url.path}: {exc}\n{traceback.format_exc()}")
    origin = request.headers.get("origin", "*")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "path": request.url.path},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    from app.core.database import init_models
    try:
        await init_models()
    except Exception as e:
        logger.error(f"Warning initializing DB tables: {e}")

@app.get("/")
async def root():
    return {"status": "ok", "service": "BadmintonAI Coach API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

app.include_router(api_router, prefix="/api")
