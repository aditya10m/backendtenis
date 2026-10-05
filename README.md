# BadmintonAI Coach - Backend API

FastAPI backend for BadmintonAI Coach, providing computer vision biomechanical analysis, deterministic scoring, video frame extraction, and training recommendations.

## Deployment on Render

This repository is ready to deploy directly on [Render](https://render.com).

### Option 1: Web Service (Python Native)
1. In the Render Dashboard, click **New +** -> **Web Service**.
2. Connect this repository (`aditya10m/backendtenis`).
3. Set the following settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set Environment Variables:
   - `PYTHON_VERSION`: `3.11.9`
   - `DEMO_MODE`: `true`
   - `JWT_SECRET`: *(auto-generated or random string)*
   - `STORAGE_PATH`: `./storage`
   - *(Optional)* `DATABASE_URL`: `postgresql+asyncpg://...` (or standard Render PostgreSQL URL)
5. Click **Create Web Service**.

### Option 2: Docker Web Service
1. Select **Docker** as runtime.
2. Render will automatically build using the provided `Dockerfile`.

### Option 3: Render Blueprint (render.yaml)
Click **New +** -> **Blueprint** and select this repo. Render will configure the service automatically from `render.yaml`.

## Health Check
- `GET /` -> `{"status": "ok", "service": "BadmintonAI Coach API"}`
- `GET /health` -> `{"status": "healthy"}`
- Swagger docs: `https://<your-render-url>/docs`
