"""Analysis worker — processes video analysis jobs asynchronously."""

import asyncio
import json
import logging
from pathlib import Path
import uuid
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.cv.pipeline import AnalysisPipeline
from app.analytics.scoring_engine import ScoringEngine
from app.ai.factory import get_ai_service
from app.models.analysis import Analysis, AnalysisStatus
from app.models.metric import Metric
from app.models.event import Event
from app.models.recommendation import Recommendation
from app.models.drill import Drill
from app.models.progress_snapshot import ProgressSnapshot

logger = logging.getLogger(__name__)


class AnalysisWorker:
    """Processes analysis jobs by running the CV pipeline, scoring engine, and AI coaching."""

    def __init__(self):
        self.scoring_engine = ScoringEngine()
        self.ai_service = get_ai_service()

    async def process_job(self, analysis_id: str, video_path: str, analysis_type: str) -> None:
        """Process a single analysis job end-to-end."""
        logger.info("Starting analysis job %s (type=%s)", analysis_id, analysis_type)

        async with AsyncSessionLocal() as db:
            try:
                # Update status callback
                async def update_status(status: str, progress: int):
                    await self._update_analysis_status(db, analysis_id, status, progress)

                # Create sync callback wrapper for the pipeline
                status_updates = []
                def sync_callback(status: str, progress: int):
                    status_updates.append((status, progress))

                # Run CV pipeline in background thread so event loop never blocks
                pipeline = AnalysisPipeline(callback=sync_callback)
                result = await asyncio.to_thread(pipeline.run, video_path, analysis_type)

                # Apply status updates
                for status, progress in status_updates:
                    await self._update_analysis_status(db, analysis_id, status, progress)

                # Save metrics to DB
                metrics_dict = {}
                for m in result.get("metrics", []):
                    metric = Metric(
                        id=uuid.uuid4(),
                        analysis_id=uuid.UUID(analysis_id),
                        category=m.get("category", "general"),
                        name=m["name"],
                        value=m.get("value"),
                        unit=m.get("unit", ""),
                        confidence=m.get("confidence", 0.0),
                        is_experimental=m.get("is_experimental", False),
                        description=m.get("description", ""),
                    )
                    db.add(metric)
                    if m.get("value") is not None:
                        metrics_dict[m["name"]] = m["value"]

                # The replay is a processing artifact, not a second analysis
                # pass.  Persist the measured landmarks/telemetry so the API
                # can return exactly what produced this report.
                skeleton = result.get("skeleton")
                if skeleton is not None:
                    from app.core.config import settings
                    artifact_dir = Path(settings.STORAGE_PATH) / "analyses"
                    artifact_dir.mkdir(parents=True, exist_ok=True)
                    artifact_path = artifact_dir / f"{analysis_id}.json"
                    artifact_path.write_text(json.dumps(skeleton), encoding="utf-8")

                # Save events to DB
                for e in result.get("events", []):
                    event = Event(
                        id=uuid.uuid4(),
                        analysis_id=uuid.UUID(analysis_id),
                        event_type=e.get("event_type", "info"),
                        timestamp_ms=e.get("timestamp_ms", 0),
                        description=e.get("description", ""),
                        severity=e.get("severity", "info"),
                    )
                    db.add(event)

                # Calculate scores
                measured_scores = result.get("scores") or {}
                technique = measured_scores.get("technique")
                movement = measured_scores.get("movement")
                serve = measured_scores.get("serve")
                consistency = measured_scores.get("consistency")
                overall = measured_scores.get("overall")
                if not measured_scores:
                    technique = self.scoring_engine.calculate_technique_score(metrics_dict)
                    movement = self.scoring_engine.calculate_movement_score(metrics_dict)
                    serve = self.scoring_engine.calculate_serve_score(metrics_dict)
                    consistency = self.scoring_engine.calculate_consistency_score(metrics_dict)
                    overall = self.scoring_engine.calculate_overall_score(technique, movement, serve, consistency)

                # Generate AI coaching report
                analysis_data = {
                    "scores": {
                        "overall": overall,
                        "technique": technique,
                        "movement": movement,
                        "serve": serve,
                        "consistency": consistency,
                    },
                    "metrics": result.get("metrics", []),
                    "analysis_type": analysis_type,
                }
                coaching_report = self.ai_service.generate_report(analysis_data)

                # Save recommendations
                for i, weakness in enumerate(coaching_report.weaknesses):
                    rec = Recommendation(
                        id=uuid.uuid4(),
                        analysis_id=uuid.UUID(analysis_id),
                        category="weakness",
                        priority=i + 1,
                        title=weakness,
                        description=coaching_report.explanation if i == 0 else "",
                    )
                    db.add(rec)

                # Save drills
                for drill_data in coaching_report.drills:
                    drill = Drill(
                        id=uuid.uuid4(),
                        name=drill_data.name,
                        description=drill_data.description or "",
                        duration_minutes=drill_data.duration_minutes or 15,
                        sets=drill_data.sets,
                        repetitions=drill_data.repetitions,
                        difficulty=drill_data.difficulty or "intermediate",
                        purpose=drill_data.purpose or "",
                    )
                    db.add(drill)

                # Get user_id from analysis
                from sqlalchemy.future import select
                analysis_result = await db.execute(
                    select(Analysis).where(Analysis.id == uuid.UUID(analysis_id))
                )
                analysis_obj = analysis_result.scalar_one_or_none()

                # Create progress snapshot
                if analysis_obj:
                    snapshot = ProgressSnapshot(
                        id=uuid.uuid4(),
                        user_id=analysis_obj.user_id,
                        analysis_id=uuid.UUID(analysis_id),
                        snapshot_date=datetime.utcnow(),
                        overall_score=overall,
                        technique_score=technique,
                        movement_score=movement,
                        serve_score=serve,
                        consistency_score=consistency,
                        metrics_summary=json.dumps(analysis_data["scores"]),
                    )
                    db.add(snapshot)

                # Mark analysis as completed
                await db.execute(
                    update(Analysis)
                    .where(Analysis.id == uuid.UUID(analysis_id))
                    .values(
                        status=AnalysisStatus.completed,
                        progress=100,
                        completed_at=datetime.utcnow(),
                    )
                )
                await db.commit()
                logger.info("Analysis job %s completed successfully", analysis_id)

            except Exception as e:
                logger.error("Analysis job %s failed: %s", analysis_id, e, exc_info=True)
                await db.execute(
                    update(Analysis)
                    .where(Analysis.id == uuid.UUID(analysis_id))
                    .values(
                        status=AnalysisStatus.failed,
                        error_message=str(e),
                    )
                )
                await db.commit()

    async def _update_analysis_status(self, db: AsyncSession, analysis_id: str, status: str, progress: int):
        """Update analysis status in the database."""
        try:
            status_enum = AnalysisStatus(status)
        except ValueError:
            status_enum = AnalysisStatus.processing
        await db.execute(
            update(Analysis)
            .where(Analysis.id == uuid.UUID(analysis_id))
            .values(status=status_enum, progress=progress)
        )
        await db.commit()
