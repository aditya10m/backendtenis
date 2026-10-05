"""Seed script — creates demo data for development and testing."""

import asyncio
import datetime
import uuid

from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.player_profile import PlayerProfile, HandEnum, BackhandEnum, SkillLevelEnum
from app.models.coach_profile import CoachProfile
from app.models.video import Video, VideoStatus
from app.models.analysis import Analysis, AnalysisType, AnalysisStatus
from app.models.metric import Metric, MetricCategory
from app.models.event import Event, EventSeverity
from app.models.recommendation import Recommendation
from app.models.drill import Drill, DifficultyLevel
from app.models.progress_snapshot import ProgressSnapshot


DEMO_METRICS = [
    # Session 1: Baseline (weakest)
    {
        "technique": {"preparation_quality": 55, "follow_through": 62, "body_rotation": 48, "balance_score": 60,
                       "knee_bend_quality": 52, "head_stability": 58, "shoulder_rotation": 50},
        "movement": {"court_coverage": 65, "recovery_speed": 55, "lateral_agility": 58, "movement_efficiency": 60},
        "serve": {"toss_consistency": 50, "knee_bend_depth": 45, "contact_point_height": 55, "follow_through_quality": 52},
    },
    # Session 2: Slight improvement
    {
        "technique": {"preparation_quality": 60, "follow_through": 66, "body_rotation": 55, "balance_score": 64,
                       "knee_bend_quality": 56, "head_stability": 63, "shoulder_rotation": 55},
        "movement": {"court_coverage": 68, "recovery_speed": 60, "lateral_agility": 62, "movement_efficiency": 63},
        "serve": {"toss_consistency": 55, "knee_bend_depth": 50, "contact_point_height": 58, "follow_through_quality": 56},
    },
    # Session 3: Building momentum
    {
        "technique": {"preparation_quality": 68, "follow_through": 72, "body_rotation": 62, "balance_score": 70,
                       "knee_bend_quality": 63, "head_stability": 70, "shoulder_rotation": 61},
        "movement": {"court_coverage": 72, "recovery_speed": 66, "lateral_agility": 68, "movement_efficiency": 67},
        "serve": {"toss_consistency": 62, "knee_bend_depth": 58, "contact_point_height": 64, "follow_through_quality": 63},
    },
    # Session 4: Good progress
    {
        "technique": {"preparation_quality": 74, "follow_through": 78, "body_rotation": 70, "balance_score": 76,
                       "knee_bend_quality": 68, "head_stability": 75, "shoulder_rotation": 67},
        "movement": {"court_coverage": 78, "recovery_speed": 72, "lateral_agility": 74, "movement_efficiency": 73},
        "serve": {"toss_consistency": 68, "knee_bend_depth": 64, "contact_point_height": 70, "follow_through_quality": 69},
    },
    # Session 5: Latest / strongest
    {
        "technique": {"preparation_quality": 79, "follow_through": 82, "body_rotation": 75, "balance_score": 81,
                       "knee_bend_quality": 72, "head_stability": 80, "shoulder_rotation": 73},
        "movement": {"court_coverage": 82, "recovery_speed": 76, "lateral_agility": 78, "movement_efficiency": 77},
        "serve": {"toss_consistency": 72, "knee_bend_depth": 68, "contact_point_height": 74, "follow_through_quality": 73},
    },
]

DEMO_EVENTS = [
    {"event_type": "positive", "timestamp_ms": 2500, "description": "Strong forehand winner down the line", "severity": "positive"},
    {"event_type": "issue", "timestamp_ms": 5200, "description": "Late preparation on backhand return", "severity": "warning"},
    {"event_type": "positive", "timestamp_ms": 8100, "description": "Excellent split-step and recovery", "severity": "positive"},
    {"event_type": "issue", "timestamp_ms": 11000, "description": "Insufficient knee bend on serve", "severity": "warning"},
    {"event_type": "positive", "timestamp_ms": 14200, "description": "Clean follow-through on cross-court forehand", "severity": "positive"},
]


async def seed_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # ── Demo Player ──
        player_user = User(
            id=uuid.uuid4(),
            email="demo@tennisai.com",
            hashed_password=get_password_hash("demo123456"),
            full_name="Aditya",
            is_active=True,
            is_coach=False,
            role=UserRole.player,
        )
        db.add(player_user)

        # ── Demo Coach ──
        coach_user = User(
            id=uuid.uuid4(),
            email="coach@tennisai.com",
            hashed_password=get_password_hash("coach123456"),
            full_name="Coach Williams",
            is_active=True,
            is_coach=True,
            role=UserRole.coach,
        )
        db.add(coach_user)
        await db.commit()
        await db.refresh(player_user)
        await db.refresh(coach_user)

        # ── Player Profile ──
        player_profile = PlayerProfile(
            id=uuid.uuid4(),
            user_id=player_user.id,
            playing_hand=HandEnum.right,
            backhand_type=BackhandEnum.two_handed,
            skill_level=SkillLevelEnum.advanced,
            preferred_surface="Hard",
            height_cm=180,
            age=25,
            country="India",
            coach_name="Coach Williams",
            training_frequency="4x/week",
        )
        db.add(player_profile)

        # ── Coach Profile ──
        coach_profile = CoachProfile(
            id=uuid.uuid4(),
            user_id=coach_user.id,
            academy_name="Elite Tennis Academy",
            specialization="Performance Analysis",
            experience_years=15,
            certification="PTR Professional",
        )
        db.add(coach_profile)
        await db.commit()

        # ── Demo Video ──
        video = Video(
            id=uuid.uuid4(),
            user_id=player_user.id,
            filename="demo_match.mp4",
            original_filename="forehand_training_sept2024.mp4",
            file_path="./storage/demo_match.mp4",
            file_size=52_428_800,
            duration_seconds=120.5,
            width=1920,
            height=1080,
            fps=30.0,
            mime_type="video/mp4",
            status=VideoStatus.processed,
        )
        db.add(video)
        await db.commit()
        await db.refresh(video)

        # ── 5 Analysis Sessions (showing improvement over time) ──
        from app.analytics.scoring_engine import ScoringEngine
        scoring = ScoringEngine()

        analysis_types = [
            AnalysisType.match,
            AnalysisType.training,
            AnalysisType.forehand,
            AnalysisType.match,
            AnalysisType.training,
        ]

        for session_idx in range(5):
            base_date = datetime.datetime.utcnow() - datetime.timedelta(days=(4 - session_idx) * 7)
            analysis = Analysis(
                id=uuid.uuid4(),
                user_id=player_user.id,
                video_id=video.id,
                analysis_type=analysis_types[session_idx],
                status=AnalysisStatus.completed,
                progress=100,
                started_at=base_date,
                completed_at=base_date + datetime.timedelta(minutes=2),
            )
            db.add(analysis)
            await db.commit()
            await db.refresh(analysis)

            # Add metrics for this session
            session_metrics = DEMO_METRICS[session_idx]
            all_metric_values = {}

            for category, metrics in session_metrics.items():
                for name, value in metrics.items():
                    metric = Metric(
                        id=uuid.uuid4(),
                        analysis_id=analysis.id,
                        category=category,
                        name=name,
                        value=float(value),
                        unit="score",
                        confidence=0.85,
                        is_experimental=False,
                        description=f"{name.replace('_', ' ').title()} score",
                    )
                    db.add(metric)
                    all_metric_values[name] = float(value)

            # Add events for latest session
            if session_idx == 4:
                for evt in DEMO_EVENTS:
                    event = Event(
                        id=uuid.uuid4(),
                        analysis_id=analysis.id,
                        event_type=evt["event_type"],
                        timestamp_ms=evt["timestamp_ms"],
                        description=evt["description"],
                        severity=evt["severity"],
                    )
                    db.add(event)

            # Add recommendations
            rec = Recommendation(
                id=uuid.uuid4(),
                analysis_id=analysis.id,
                category="technique",
                priority=1,
                title="Improve preparation timing",
                description="Focus on earlier racket preparation to improve stroke quality",
                explanation="Analysis shows delayed preparation in several sequences",
            )
            db.add(rec)
            await db.commit()
            await db.refresh(rec)

            # Add drill
            drill = Drill(
                id=uuid.uuid4(),
                recommendation_id=rec.id,
                name="Shadow Swing Preparation",
                description="Practice early racket preparation without a ball",
                duration_minutes=15,
                sets=3,
                repetitions=20,
                difficulty=DifficultyLevel.intermediate,
                purpose="Build muscle memory for early preparation",
            )
            db.add(drill)

            # Calculate scores and create progress snapshot
            technique = scoring.calculate_technique_score(all_metric_values)
            movement = scoring.calculate_movement_score(all_metric_values)
            serve = scoring.calculate_serve_score(all_metric_values)
            consistency = scoring.calculate_consistency_score(all_metric_values)
            overall = scoring.calculate_overall_score(technique, movement, serve, consistency)

            snapshot = ProgressSnapshot(
                id=uuid.uuid4(),
                user_id=player_user.id,
                analysis_id=analysis.id,
                snapshot_date=base_date,
                overall_score=overall,
                technique_score=technique,
                movement_score=movement,
                serve_score=serve,
                consistency_score=consistency,
            )
            db.add(snapshot)
            await db.commit()

        print("Seed data created successfully!")
        print(f"  Demo player: demo@tennisai.com / demo123456")
        print(f"  Demo coach:  coach@tennisai.com / coach123456")
        print(f"  5 analysis sessions with metrics and progress history")


if __name__ == "__main__":
    asyncio.run(seed_data())
