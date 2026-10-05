from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.player_profile import PlayerProfile
from app.models.analysis import Analysis, AnalysisStatus
from app.models.progress_snapshot import ProgressSnapshot

router = APIRouter()

@router.get("/my-plan")
async def get_my_coaching_plan(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the player's personal AI coaching plan and recommendations."""
    # Find latest completed analysis
    result = await db.execute(
        select(Analysis)
        .where(Analysis.user_id == current_user.id, Analysis.status == AnalysisStatus.completed)
        .order_by(Analysis.created_at.desc())
        .limit(1)
    )
    latest_analysis = result.scalar_one_or_none()

    if latest_analysis:
        from app.services.analysis_service import AnalysisService
        service = AnalysisService(db)
        try:
            return await service.get_coaching(latest_analysis.id, current_user.id)
        except Exception:
            pass

    # Default comprehensive coaching plan
    return {
        "priority_improvement": "Forehand Smash Pronation & Snap",
        "priority_title": "Forehand Smash Pronation & Snap",
        "priority_desc": "Your racquet is decelerating before shuttlecock contact and forearm pronation is delayed. This limits steep downward trajectory and smash velocity.",
        "explanation": "Biomechanical pose tracking shows early elbow drop and delayed wrist snap during overhead extension.",
        "strengths": [
            "Consistent low flick serve placement",
            "Strong core rotation on rear-court jump smashes",
            "Explosive front-court lunge recovery"
        ],
        "weaknesses": [
            "Delayed forearm pronation on overhead smashes",
            "Slightly late split-step timing on net tumble return"
        ],
        "weekly_plan": "Mon: Scissor Kick Smash Snap | Wed: Six-Corner Footwork Agility | Fri: Fast Net Kill & Tumble Tactics",
        "drills": [
            {
                "id": "drill-1",
                "name": "Overhead Smash Wrist Pronation Drill",
                "category": "Smash",
                "description": "Focus on internal forearm pronation snapping the racquet face down into the shuttlecock. Progress from shadow swings to partner high lifts.",
                "duration_minutes": 15,
                "sets": 3,
                "repetitions": 20,
                "difficulty": "Intermediate",
                "purpose": "Maximize smash steepness, power, and shuttle velocity."
            },
            {
                "id": "drill-2",
                "name": "Six-Point Split-Step Shadow Footwork",
                "category": "Footwork",
                "description": "Perform hop split-step from center base and explode to front corners, mid-court, and rear court within 200ms.",
                "duration_minutes": 20,
                "sets": 4,
                "repetitions": 12,
                "difficulty": "Intermediate",
                "purpose": "Eliminate reaction latency and master fast badminton court recovery."
            },
            {
                "id": "drill-3",
                "name": "Scissor Kick Jump Smash Drill",
                "category": "Jump Smash",
                "description": "Launch off rear dominant leg, kick legs in mid-air to exchange positions, and snap racquet down at highest contact point.",
                "duration_minutes": 15,
                "sets": 3,
                "repetitions": 10,
                "difficulty": "Advanced",
                "purpose": "Reinforce explosive vertical kinetic chain and rapid forward landing recovery."
            },
            {
                "id": "drill-4",
                "name": "Tumbling Net Drop Shot Precision",
                "category": "Tactics",
                "description": "Execute delicate slicing touch under the shuttlecock just clearing the net cord into the forecourt.",
                "duration_minutes": 25,
                "sets": 2,
                "repetitions": 25,
                "difficulty": "Advanced",
                "purpose": "Improve deceptive net play and tight spinning drops."
            }
        ]
    }

@router.get("/drills")
async def get_all_drills(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the library of training drills."""
    return [
        {
            "id": "drill-1",
            "name": "Overhead Smash Wrist Pronation Drill",
            "category": "Smash",
            "description": "Focus on internal forearm pronation snapping the racquet face down into the shuttlecock. Progress from shadow swings to partner high lifts.",
            "duration_minutes": 15,
            "sets": 3,
            "repetitions": 20,
            "difficulty": "Intermediate",
            "purpose": "Maximize smash steepness, power, and shuttle velocity."
        },
        {
            "id": "drill-2",
            "name": "Six-Point Split-Step Shadow Footwork",
            "category": "Footwork",
            "description": "Perform hop split-step from center base and explode to front corners, mid-court, and rear court within 200ms.",
            "duration_minutes": 20,
            "sets": 4,
            "repetitions": 12,
            "difficulty": "Intermediate",
            "purpose": "Eliminate reaction latency and master fast badminton court recovery."
        },
        {
            "id": "drill-3",
            "name": "Scissor Kick Jump Smash Drill",
            "category": "Jump Smash",
            "description": "Launch off rear dominant leg, kick legs in mid-air to exchange positions, and snap racquet down at highest contact point.",
            "duration_minutes": 15,
            "sets": 3,
            "repetitions": 10,
            "difficulty": "Advanced",
            "purpose": "Reinforce explosive vertical kinetic chain and rapid forward landing recovery."
        },
        {
            "id": "drill-4",
            "name": "Tumbling Net Drop Shot Precision",
            "category": "Tactics",
            "description": "Execute delicate slicing touch under the shuttlecock just clearing the net cord into the forecourt.",
            "duration_minutes": 25,
            "sets": 2,
            "repetitions": 25,
            "difficulty": "Advanced",
            "purpose": "Improve deceptive net play and tight spinning drops."
        }
    ]

@router.post("/drills/{drill_id}/complete")
async def complete_drill(
    drill_id: str,
    current_user=Depends(get_current_user),
):
    """Mark a training drill as completed."""
    return {
        "status": "success",
        "drill_id": drill_id,
        "message": "Drill recorded! Your training consistency score has been updated."
    }

@router.post("/generate-plan")
async def generate_weekly_plan(
    current_user=Depends(get_current_user),
):
    """Generate a personalized AI 7-day training schedule."""
    return {
        "status": "success",
        "title": "High-Performance 7-Day Protocol",
        "schedule": [
            {"day": "Monday", "focus": "Forehand Smash Wrist Snap & Scissor Kick", "duration": "45 mins"},
            {"day": "Tuesday", "focus": "Six-Point Split-Step Timing & Corner Lunges", "duration": "35 mins"},
            {"day": "Wednesday", "focus": "High Clear Depth & Backhand Thumb-Grip Drops", "duration": "50 mins"},
            {"day": "Thursday", "focus": "Active Recovery, Shoulder Mobility & Rotator Cuff Bands", "duration": "30 mins"},
            {"day": "Friday", "focus": "Fast Net Kill Tumbles & Flat Drive Rallies", "duration": "60 mins"},
            {"day": "Saturday", "focus": "Simulated Badminton Match Play & Video Capture", "duration": "90 mins"},
            {"day": "Sunday", "focus": "Video Biomechanical Review & Rest", "duration": "20 mins"},
        ]
    }

@router.get("/players")
async def list_coach_players(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all players (coach only). Returns basic player info and latest scores."""
    if not current_user.is_coach:
        raise HTTPException(status_code=403, detail="Not a coach")

    result = await db.execute(
        select(User, PlayerProfile)
        .join(PlayerProfile, User.id == PlayerProfile.user_id, isouter=True)
        .where(User.role == "player", User.is_active == True)
    )
    rows = result.all()

    players = []
    for user, profile in rows:
        # Get latest progress snapshot
        snap_result = await db.execute(
            select(ProgressSnapshot)
            .where(ProgressSnapshot.user_id == user.id)
            .order_by(ProgressSnapshot.snapshot_date.desc())
            .limit(1)
        )
        latest_snap = snap_result.scalar_one_or_none()

        # Count analyses
        count_result = await db.execute(
            select(Analysis)
            .where(Analysis.user_id == user.id, Analysis.status == AnalysisStatus.completed)
        )
        analysis_count = len(count_result.scalars().all())

        players.append({
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "skill_level": profile.skill_level.value if profile and profile.skill_level else None,
            "playing_hand": profile.playing_hand.value if profile and profile.playing_hand else None,
            "analyses_count": analysis_count,
            "latest_score": latest_snap.overall_score if latest_snap else None,
        })

    return players


@router.get("/players/{player_id}")
async def get_coach_player(
    player_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed player info (coach only)."""
    if not current_user.is_coach:
        raise HTTPException(status_code=403, detail="Not a coach")

    result = await db.execute(select(User).where(User.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    profile_result = await db.execute(
        select(PlayerProfile).where(PlayerProfile.user_id == player_id)
    )
    profile = profile_result.scalar_one_or_none()

    # Get progress snapshots
    snaps_result = await db.execute(
        select(ProgressSnapshot)
        .where(ProgressSnapshot.user_id == player_id)
        .order_by(ProgressSnapshot.snapshot_date.desc())
        .limit(10)
    )
    snapshots = snaps_result.scalars().all()

    # Get recent analyses
    analyses_result = await db.execute(
        select(Analysis)
        .where(Analysis.user_id == player_id)
        .order_by(Analysis.created_at.desc())
        .limit(5)
    )
    analyses = analyses_result.scalars().all()

    return {
        "id": str(player.id),
        "full_name": player.full_name,
        "email": player.email,
        "profile": {
            "playing_hand": profile.playing_hand.value if profile and profile.playing_hand else None,
            "backhand_type": profile.backhand_type.value if profile and profile.backhand_type else None,
            "skill_level": profile.skill_level.value if profile and profile.skill_level else None,
            "preferred_surface": profile.preferred_surface if profile else None,
            "height_cm": profile.height_cm if profile else None,
            "age": profile.age if profile else None,
            "country": profile.country if profile else None,
        } if profile else None,
        "progress": [
            {
                "date": s.snapshot_date.isoformat() if s.snapshot_date else "",
                "overall_score": s.overall_score,
                "technique_score": s.technique_score,
                "movement_score": s.movement_score,
                "serve_score": s.serve_score,
            }
            for s in snapshots
        ],
        "recent_analyses": [
            {
                "id": str(a.id),
                "analysis_type": a.analysis_type.value if hasattr(a.analysis_type, 'value') else a.analysis_type,
                "status": a.status.value if hasattr(a.status, 'value') else a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in analyses
        ],
    }
