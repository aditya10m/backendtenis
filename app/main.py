from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import settings
import os

app = FastAPI(title="BadmintonAI Coach API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)

@app.get("/")
async def root():
    return {"status": "ok", "service": "BadmintonAI Coach API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

app.include_router(api_router, prefix="/api")
