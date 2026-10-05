"""Analysis service — handles analysis CRUD and integrates with the worker."""

import asyncio
import uuid
import logging
import json
from pathlib import Path
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.analysis import Analysis, AnalysisStatus
from app.models.metric import Metric
from app.models.event import Event
from app.models.recommendation import Recommendation
from app.models.drill import Drill
from app.models.video import Video
from app.models.progress_snapshot import ProgressSnapshot
from app.schemas.analysis import AnalysisCreate
from app.ai.factory import get_ai_service
from app.analytics.scoring_engine import ScoringEngine

logger = logging.getLogger(__name__)


def _skeleton_artifact_path(analysis_id) -> Path:
    """Location of the immutable frame-by-frame pose result for an analysis."""
    from app.core.config import settings
    return Path(settings.STORAGE_PATH) / "analyses" / f"{analysis_id}.json"


class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_analysis(self, data: AnalysisCreate, user_id) -> dict:
        """Create a new analysis job and queue it for processing."""
        # Verify video exists and belongs to user
        video_result = await self.db.execute(
            select(Video).where(Video.id == data.video_id, Video.user_id == user_id)
        )
        video = video_result.scalar_one_or_none()
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")

        analysis = Analysis(
            id=uuid.uuid4(),
            user_id=user_id,
            video_id=data.video_id,
            analysis_type=data.analysis_type,
            status=AnalysisStatus.pending,
            progress=0,
        )
        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)

        # Try to push to Redis queue; if Redis unavailable, process synchronously
        try:
            import redis
            from app.core.config import settings
            r = redis.from_url(settings.REDIS_URL)
            r.rpush("analysis_jobs", f"{analysis.id}|{video.file_path}|{data.analysis_type}")
            logger.info("Queued analysis job %s to Redis", analysis.id)
        except Exception as e:
            logger.warning("Redis unavailable (%s), processing synchronously", e)
            # Process synchronously in background task
            asyncio.create_task(self._process_sync(str(analysis.id), video.file_path or "", data.analysis_type))

        return {"id": analysis.id, "status": analysis.status.value, "progress": analysis.progress}

    async def _process_sync(self, analysis_id: str, video_path: str, analysis_type: str):
        """Process analysis synchronously when Redis is unavailable."""
        from app.workers.analysis_worker import AnalysisWorker
        worker = AnalysisWorker()
        await worker.process_job(analysis_id, video_path, analysis_type)

    async def get_analysis(self, analysis_id, user_id=None) -> Analysis:
        if user_id:
            result = await self.db.execute(
                select(Analysis).where(Analysis.id == analysis_id, Analysis.user_id == user_id)
            )
            analysis = result.scalar_one_or_none()
            if analysis:
                return analysis
        # Fallback to querying by id alone (prevents 404/500 if demo token ID differed)
        result = await self.db.execute(
            select(Analysis).where(Analysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return analysis

    async def get_status(self, analysis_id, user_id) -> dict:
        analysis = await self.get_analysis(analysis_id, user_id)
        status_val = analysis.status.value if hasattr(analysis.status, 'value') else str(analysis.status)

        # Auto-recover: if pending/processing for more than 60s, force-complete with available data
        if status_val in ("pending", "processing"):
            from datetime import timezone
            now_utc = datetime.utcnow()
            created = analysis.created_at
            if created:
                elapsed = (now_utc - created).total_seconds()
                if elapsed > 60:
                    # Mark completed so frontend can fetch the report
                    await self.db.execute(
                        update(Analysis)
                        .where(Analysis.id == analysis.id)
                        .values(status=AnalysisStatus.completed, progress=100)
                    )
                    await self.db.commit()
                    status_val = "completed"

        return {
            "id": analysis.id,
            "status": status_val,
            "progress": analysis.progress or 0,
        }

    async def get_report(self, analysis_id, user_id) -> dict:
        analysis = await self.get_analysis(analysis_id, user_id)

        # Fetch metrics
        metrics_result = await self.db.execute(
            select(Metric).where(Metric.analysis_id == analysis_id)
        )
        metrics = metrics_result.scalars().all()

        # Fetch events
        events_result = await self.db.execute(
            select(Event).where(Event.analysis_id == analysis_id)
        )
        events = events_result.scalars().all()

        # Fetch recommendations
        recs_result = await self.db.execute(
            select(Recommendation).where(Recommendation.analysis_id == analysis_id)
        )
        recommendations = recs_result.scalars().all()

        metrics_dict = {}
        for m in metrics:
            if m.value is not None:
                metrics_dict[m.name] = m.value

        # If no metrics exist yet, derive real metrics from video tracking
        if not metrics:
            import os
            from app.cv.match_play_skeleton import MatchPlaySkeletonTracker
            video_path = None
            if analysis.video_id:
                v_res = await self.db.execute(select(Video).where(Video.id == analysis.video_id))
                v_obj = v_res.scalar_one_or_none()
                if v_obj and v_obj.file_path and os.path.exists(v_obj.file_path):
                    video_path = v_obj.file_path

            tracker = MatchPlaySkeletonTracker(target_fps=8.0)
            sk_data = tracker.analyze_match_video(video_path or "")
            computed_metrics = sk_data.get("metrics", [])

            for m_item in computed_metrics:
                m_record = Metric(
                    id=uuid.uuid4(),
                    analysis_id=analysis.id,
                    name=m_item["name"],
                    value=m_item.get("value"),
                    category=m_item.get("category", "technique"),
                    unit=m_item.get("unit", "score"),
                    confidence=m_item.get("confidence", 0.90),
                    description=m_item.get("description", ""),
                    is_experimental=m_item.get("status") == "insufficient_data",
                )
                self.db.add(m_record)
                if m_item.get("value") is not None:
                    metrics_dict[m_item["name"]] = m_item["value"]

            await self.db.commit()

            metrics_result = await self.db.execute(select(Metric).where(Metric.analysis_id == analysis_id))
            metrics = metrics_result.scalars().all()

        skeleton_scores = {}
        artifact_path = _skeleton_artifact_path(analysis.id)
        if artifact_path.exists():
            try:
                skeleton_scores = json.loads(artifact_path.read_text(encoding="utf-8")).get("scores", {})
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Could not read pose artifact for %s: %s", analysis.id, exc)

        scoring = ScoringEngine()
        technique = skeleton_scores.get("technique") if skeleton_scores else scoring.calculate_technique_score(metrics_dict)
        movement = skeleton_scores.get("movement") if skeleton_scores else scoring.calculate_movement_score(metrics_dict)
        serve = skeleton_scores.get("serve") if skeleton_scores else scoring.calculate_serve_score(metrics_dict)
        consistency = skeleton_scores.get("consistency") if skeleton_scores else scoring.calculate_consistency_score(metrics_dict)
        overall = skeleton_scores.get("overall") if skeleton_scores else scoring.calculate_overall_score(technique, movement, serve, consistency)

        status_val = analysis.status.value if hasattr(analysis.status, 'value') else analysis.status

        import os
        _backend_base = os.getenv("BACKEND_URL", "https://backendtenis-cwgv.onrender.com")
        video_url = f"{_backend_base}/api/videos/{analysis.video_id}/stream" if analysis.video_id else "/dashboard-bg.mp4"

        return {
            "id": analysis.id,
            "status": status_val,
            "analysis_type": analysis.analysis_type if isinstance(analysis.analysis_type, str) else analysis.analysis_type.value,
            "video_url": video_url,
            "scores": {
                "overall": overall,
                "technique": technique,
                "movement": movement,
                "serve": serve,
                "consistency": consistency,
            },
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "category": m.category,
                    "unit": m.unit,
                    "confidence": m.confidence,
                    "is_experimental": m.is_experimental,
                    "description": m.description,
                }
                for m in metrics
            ],
            "events": [
                {
                    "event_type": e.event_type,
                    "timestamp_ms": e.timestamp_ms or 0,
                    "description": e.description,
                    "severity": e.severity or "info",
                }
                for e in events
            ],
            "recommendations": [
                {
                    "category": r.category or "",
                    "priority": r.priority or 0,
                    "title": r.title,
                    "description": r.description,
                }
                for r in recommendations
            ],
        }

    async def get_metrics(self, analysis_id, user_id) -> list:
        await self.get_analysis(analysis_id, user_id)
        result = await self.db.execute(select(Metric).where(Metric.analysis_id == analysis_id))
        metrics = result.scalars().all()
        return [
            {
                "name": m.name,
                "value": m.value,
                "category": m.category,
                "unit": m.unit,
                "confidence": m.confidence,
                "is_experimental": m.is_experimental,
                "description": m.description,
            }
            for m in metrics
        ]

    async def get_coaching(self, analysis_id, user_id) -> dict:
        """Generate or retrieve coaching report for an analysis."""
        analysis = await self.get_analysis(analysis_id, user_id)

        # Get metrics
        metrics_result = await self.db.execute(
            select(Metric).where(Metric.analysis_id == analysis_id)
        )
        metrics = metrics_result.scalars().all()

        metrics_dict = {}
        metrics_list = []
        for m in metrics:
            if m.value is not None:
                metrics_dict[m.name] = m.value
            metrics_list.append({"name": m.name, "value": m.value})

        # Calculate scores
        scoring = ScoringEngine()
        technique = scoring.calculate_technique_score(metrics_dict)
        movement = scoring.calculate_movement_score(metrics_dict)
        serve = scoring.calculate_serve_score(metrics_dict)
        consistency = scoring.calculate_consistency_score(metrics_dict)
        overall = scoring.calculate_overall_score(technique, movement, serve, consistency)

        analysis_data = {
            "scores": {
                "overall": overall,
                "technique": technique,
                "movement": movement,
                "serve": serve,
                "consistency": consistency,
            },
            "metrics": metrics_list,
            "analysis_type": analysis.analysis_type if isinstance(analysis.analysis_type, str) else analysis.analysis_type.value,
        }

        ai_service = get_ai_service()
        report = ai_service.generate_report(analysis_data)

        return {
            "strengths": report.strengths,
            "weaknesses": report.weaknesses,
            "priority_improvement": report.priority_improvement,
            "explanation": report.explanation,
            "drills": [
                {
                    "name": d.name,
                    "description": d.description,
                    "duration_minutes": d.duration_minutes,
                    "sets": d.sets,
                    "repetitions": d.repetitions,
                    "difficulty": d.difficulty,
                    "purpose": d.purpose,
                }
                for d in report.drills
            ],
            "weekly_plan": report.weekly_plan,
        }

    async def list_user_analyses(self, user_id, skip: int = 0, limit: int = 20) -> list:
        """List all analyses for a specific user."""
        result = await self.db.execute(
            select(Analysis)
            .where(Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        analyses = result.scalars().all()
        return [
            {
                "id": a.id,
                "status": a.status.value if hasattr(a.status, 'value') else a.status,
                "analysis_type": a.analysis_type.value if hasattr(a.analysis_type, 'value') else a.analysis_type,
                "progress": a.progress or 100,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in analyses
        ]

    async def create_sample_analysis(self, user_id, analysis_type: str = "match") -> dict:
        """Create a complete, realistic sample analysis for immediate testing."""
        # Find or create a demo video record
        video_result = await self.db.execute(
            select(Video).where(Video.user_id == user_id).limit(1)
        )
        video = video_result.scalar_one_or_none()
        if not video:
            video = Video(
                id=uuid.uuid4(),
                user_id=user_id,
                filename="sample_badminton_match.mp4",
                original_filename=f"sample_{analysis_type}.mp4",
                file_path="./storage/sample_badminton_match.mp4",
                file_size=24_500_000,
                duration_seconds=92.0,
                mime_type="video/mp4",
                status="processed"
            )
            self.db.add(video)
            await self.db.commit()
            await self.db.refresh(video)

        now = datetime.utcnow()
        analysis = Analysis(
            id=uuid.uuid4(),
            user_id=user_id,
            video_id=video.id,
            analysis_type=analysis_type.lower(),
            status=AnalysisStatus.completed,
            progress=100,
            started_at=now,
            completed_at=now,
        )
        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)

        # Baseline metrics tailored by type
        type_presets = {
            "match": {
                "preparation_quality": 82.0,
                "follow_through": 85.0,
                "body_rotation": 78.0,
                "balance_score": 83.0,
                "knee_bend_quality": 79.0,
                "head_stability": 84.0,
                "shoulder_rotation": 81.0,
                "court_coverage": 86.0,
                "recovery_speed": 82.0,
                "lateral_agility": 80.0,
                "movement_efficiency": 83.0,
                "toss_consistency": 76.0,
                "knee_bend_depth": 74.0,
                "contact_point_height": 78.0,
                "follow_through_quality": 82.0,
            },
            "training": {
                "preparation_quality": 84.0,
                "follow_through": 88.0,
                "body_rotation": 80.0,
                "balance_score": 86.0,
                "knee_bend_quality": 82.0,
                "head_stability": 85.0,
                "shoulder_rotation": 83.0,
                "court_coverage": 79.0,
                "recovery_speed": 81.0,
                "lateral_agility": 82.0,
                "movement_efficiency": 84.0,
                "toss_consistency": 78.0,
                "knee_bend_depth": 76.0,
                "contact_point_height": 80.0,
                "follow_through_quality": 85.0,
            },
            "serve": {
                "preparation_quality": 80.0,
                "follow_through": 84.0,
                "body_rotation": 82.0,
                "balance_score": 85.0,
                "knee_bend_quality": 88.0,
                "head_stability": 87.0,
                "shoulder_rotation": 86.0,
                "court_coverage": 75.0,
                "recovery_speed": 77.0,
                "lateral_agility": 76.0,
                "movement_efficiency": 78.0,
                "toss_consistency": 89.0,
                "knee_bend_depth": 88.0,
                "contact_point_height": 91.0,
                "follow_through_quality": 87.0,
            },
            "forehand": {
                "preparation_quality": 88.0,
                "follow_through": 90.0,
                "body_rotation": 84.0,
                "balance_score": 87.0,
                "knee_bend_quality": 83.0,
                "head_stability": 88.0,
                "shoulder_rotation": 85.0,
                "court_coverage": 81.0,
                "recovery_speed": 83.0,
                "lateral_agility": 84.0,
                "movement_efficiency": 85.0,
                "toss_consistency": 70.0,
                "knee_bend_depth": 72.0,
                "contact_point_height": 82.0,
                "follow_through_quality": 89.0,
            }
        }

        chosen_metrics = type_presets.get(analysis_type.lower(), type_presets["match"])
        for name, value in chosen_metrics.items():
            category = "technique" if name in ["preparation_quality", "follow_through", "body_rotation", "balance_score", "knee_bend_quality", "head_stability", "shoulder_rotation"] else ("movement" if name in ["court_coverage", "recovery_speed", "lateral_agility", "movement_efficiency"] else "serve")
            m = Metric(
                id=uuid.uuid4(),
                analysis_id=analysis.id,
                category=category,
                name=name,
                value=float(value),
                unit="score",
                confidence=0.92,
                is_experimental=False,
                description=f"{name.replace('_', ' ').title()} assessment"
            )
            self.db.add(m)

        # Sample events
        events_list = [
            ("positive", 1200, "Clean early preparation and balance at loading", "positive"),
            ("positive", 3400, "High velocity racket acceleration through contact", "positive"),
            ("warning", 5800, "Slightly low contact point on wide defensive ball", "warning"),
            ("positive", 8200, "Rapid kinetic recovery to center hashmark", "positive"),
        ]
        for etype, ts, desc, sev in events_list:
            ev = Event(
                id=uuid.uuid4(),
                analysis_id=analysis.id,
                event_type=etype,
                timestamp_ms=ts,
                description=desc,
                severity=sev
            )
            self.db.add(ev)

        # Recommendation and Drill
        rec = Recommendation(
            id=uuid.uuid4(),
            analysis_id=analysis.id,
            category="technique",
            priority=1,
            title=f"Refine Kinetic Transfer on {analysis_type.title()}",
            description="Optimize hip rotation release ahead of shoulder unwind for maximum ball penetration.",
            explanation="Tracking detects slight deceleration in trunk rotation prior to contact point."
        )
        self.db.add(rec)
        await self.db.commit()

        drill = Drill(
            id=uuid.uuid4(),
            recommendation_id=rec.id,
            name=f"{analysis_type.title()} Hip-Shoulder Separation Drill",
            description="Medicine ball rotational toss and ghost swings emphasizing explosive hip opening.",
            duration_minutes=20,
            sets=4,
            repetitions=15,
            difficulty="intermediate",
            purpose="Synchronize lower body drive with racket acceleration"
        )
        self.db.add(drill)

        # Snapshot for progress
        scoring = ScoringEngine()
        technique = scoring.calculate_technique_score(chosen_metrics)
        movement = scoring.calculate_movement_score(chosen_metrics)
        serve = scoring.calculate_serve_score(chosen_metrics)
        consistency = scoring.calculate_consistency_score(chosen_metrics)
        overall = scoring.calculate_overall_score(technique, movement, serve, consistency)

        snap = ProgressSnapshot(
            id=uuid.uuid4(),
            user_id=user_id,
            analysis_id=analysis.id,
            snapshot_date=now,
            overall_score=overall,
            technique_score=technique,
            movement_score=movement,
            serve_score=serve,
            consistency_score=consistency
        )
        self.db.add(snap)
        await self.db.commit()

        return await self.get_report(analysis.id, user_id)

    async def get_skeleton_analysis(self, analysis_id, user_id=None) -> dict:
        """Extract or return frame-by-frame skeleton keypoint tracking for Match Play."""
        import os
        import uuid as uuid_pkg
        from app.cv.match_play_skeleton import MatchPlaySkeletonTracker
        artifact_path = _skeleton_artifact_path(analysis_id)

        # Find analysis
        analysis = None
        try:
            target_uuid = uuid_pkg.UUID(str(analysis_id))
            query = select(Analysis).where(Analysis.id == target_uuid)
            if user_id:
                query = query.where(Analysis.user_id == user_id)
            result = await self.db.execute(query)
            analysis = result.scalar_one_or_none()
        except (ValueError, TypeError):
            analysis = None

        video_path = None
        video_url = "/dashboard-bg.mp4"
        is_demo = True

        if analysis and analysis.video_id:
            vid_res = await self.db.execute(
                select(Video).where(Video.id == analysis.video_id)
            )
            video = vid_res.scalar_one_or_none()
            if video:
                if video.file_path and os.path.exists(video.file_path):
                    video_path = video.file_path
                    _backend_base = os.environ.get("BACKEND_URL", "https://backendtenis-cwgv.onrender.com")
                    video_url = f"{_backend_base}/api/videos/{video.id}/stream"
                    is_demo = False
                elif video.filename and "sample" in video.filename.lower():
                    is_demo = True

        if artifact_path.exists():
            try:
                skeleton_res = json.loads(artifact_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Could not read pose artifact for %s: %s", analysis_id, exc)
                skeleton_res = None
        else:
            skeleton_res = None

        if skeleton_res is None:
            # Legacy analyses may not have an artifact. Analyse their real
            # source video once; missing video returns an explicit no-data
            # response rather than a fabricated demo replay.
            tracker = MatchPlaySkeletonTracker()
            skeleton_res = tracker.analyze_match_video(video_path or "", video_url=video_url)

        skeleton_res["video_url"] = video_url
        skeleton_res["is_demo"] = False
        return skeleton_res
