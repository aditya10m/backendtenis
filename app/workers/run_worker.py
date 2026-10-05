"""Worker process — polls Redis for analysis jobs and processes them."""

import asyncio
import logging
import signal
import sys

from app.workers.analysis_worker import AnalysisWorker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("worker")


async def poll_redis():
    """Poll Redis for analysis jobs."""
    from app.core.config import settings
    worker = AnalysisWorker()
    running = True

    def shutdown(sig, frame):
        nonlocal running
        logger.info("Shutting down worker...")
        running = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.info("Worker started, polling Redis at %s", settings.REDIS_URL)

    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error("Cannot connect to Redis: %s", e)
        logger.info("Worker will exit. Use synchronous mode via the API instead.")
        return

    while running:
        try:
            job = r.blpop("analysis_jobs", timeout=5)
            if job:
                _, job_data = job
                parts = job_data.decode().split("|", 2)
                if len(parts) == 3:
                    analysis_id, video_path, analysis_type = parts
                    logger.info("Processing job: analysis_id=%s type=%s", analysis_id, analysis_type)
                    await worker.process_job(analysis_id, video_path, analysis_type)
                else:
                    logger.warning("Invalid job data: %s", job_data)
        except Exception as e:
            logger.error("Worker error: %s", e, exc_info=True)
            await asyncio.sleep(2)

    logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(poll_redis())
