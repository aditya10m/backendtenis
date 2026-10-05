from app.ai.base import AICoachService
from app.schemas.coaching import CoachingReport
from app.schemas.analysis import DrillResponse

# Built-in drill library — no external API needed
DRILL_LIBRARY = {
    "preparation_quality": [
        DrillResponse(
            name="Shadow Swing Preparation",
            description="Stand at mid-court base. Have a partner call clear/smash/drop. "
            "Turn your shoulders and raise your racquet before the shuttlecock arrives.",
            duration_minutes=15, sets=3, repetitions=20, difficulty="intermediate",
            purpose="Improve preparation speed and reaction timing",
        ),
        DrillResponse(
            name="Split-Step Reaction",
            description="Start at the center base. Split-step as your partner strikes, "
            "then explode to the shuttlecock with early racquet preparation.",
            duration_minutes=10, sets=4, repetitions=15, difficulty="beginner",
            purpose="Build the habit of instant split-step anticipation",
        ),
    ],
    "follow_through": [
        DrillResponse(
            name="Full Follow-Through Freeze",
            description="Hit overhead smashes and freeze at the end of your follow-through. "
            "Your racquet should finish across the non-dominant hip with full pronation.",
            duration_minutes=10, sets=3, repetitions=15, difficulty="beginner",
            purpose="Develop complete follow-through and forearm pronation habit",
        ),
    ],
    "body_rotation": [
        DrillResponse(
            name="Scissor Kick Rotation Drill",
            description="Hit jump smashes from the rear court, focusing on full "
            "hip and shoulder rotation through the shot and scissor kick leg exchange.",
            duration_minutes=15, sets=3, repetitions=20, difficulty="intermediate",
            purpose="Increase power through explosive airborne body rotation",
        ),
    ],
    "balance_score": [
        DrillResponse(
            name="One-Leg Balance Rally",
            description="Rally with high clears while focusing on balanced lunge footwork. "
            "After each shot, hold your finish lunge position for 1 second.",
            duration_minutes=10, sets=2, repetitions=30, difficulty="advanced",
            purpose="Improve dynamic balance and lunge stability during play",
        ),
    ],
    "knee_bend_quality": [
        DrillResponse(
            name="Net Lunge Practice",
            description="Have a partner feed tight tumbling net shots. Bend your knees deeply "
            "into a lunging stance to get under the shuttlecock with an upright torso.",
            duration_minutes=10, sets=3, repetitions=15, difficulty="beginner",
            purpose="Develop proper front-court knee flexion and lunge mechanics",
        ),
    ],
    "court_coverage": [
        DrillResponse(
            name="Corner-to-Corner Sprint Drill",
            description="Sprint from rear court to front net corners, touching each line. "
            "Simulate recovery to center base after each touch.",
            duration_minutes=10, sets=5, repetitions=10, difficulty="intermediate",
            purpose="Improve explosive court coverage and recovery speed",
        ),
    ],
    "recovery_speed": [
        DrillResponse(
            name="Hit and Recover",
            description="Hit a smash or clear, then rapidly recover back to the center T base "
            "before the next shuttle is fed. Focus on explosive first push-off step.",
            duration_minutes=15, sets=4, repetitions=12, difficulty="intermediate",
            purpose="Build recovery speed and court positioning",
        ),
    ],
    "lateral_agility": [
        DrillResponse(
            name="Lateral Shuffle & Drive Drill",
            description="Shuffle laterally across the mid-court in defensive stance. "
            "Partner feeds alternating fast drives.",
            duration_minutes=10, sets=4, repetitions=10, difficulty="beginner",
            purpose="Improve mid-court drive reaction and lateral agility",
        ),
    ],
    "toss_consistency": [
        DrillResponse(
            name="Low Serve Precision Practice",
            description="Place a target on the front service line. "
            "Practice low short serves to skim the net tape and land on the target 10 times in a row.",
            duration_minutes=10, sets=3, repetitions=10, difficulty="beginner",
            purpose="Develop a consistent, tight low serve trajectory",
        ),
    ],
    "knee_bend_depth": [
        DrillResponse(
            name="Jump Smash Scissor Kick Load",
            description="Practice the rear leg loading with deep knee bend. Hold for "
            "2 seconds, then explode upward in a scissor kick. No shuttle needed initially.",
            duration_minutes=10, sets=3, repetitions=12, difficulty="intermediate",
            purpose="Build vertical leg drive and kinetic loading for smashes",
        ),
    ],
    "contact_point_height": [
        DrillResponse(
            name="High Contact Smash Practice",
            description="Hit smashes and clears at 75% power focusing only on contacting the "
            "shuttlecock at full arm extension at maximum apex.",
            duration_minutes=15, sets=3, repetitions=15, difficulty="intermediate",
            purpose="Maximize contact point height for steep smash angle",
        ),
    ],
    "head_stability": [
        DrillResponse(
            name="Watch the Shuttle Contact Drill",
            description="Rally at medium pace and keep your eyes on the shuttle contact point "
            "for a beat after hitting. Head should remain still through the shot.",
            duration_minutes=10, sets=3, repetitions=20, difficulty="beginner",
            purpose="Reduce head sway for cleaner sweet-spot striking",
        ),
    ],
    "shoulder_rotation": [
        DrillResponse(
            name="Medicine Ball Smash Rotation",
            description="Stand sideways in ready posture. Rotate and throw a medicine ball "
            "mimicking an explosive overhead smash torso coil.",
            duration_minutes=10, sets=3, repetitions=15, difficulty="intermediate",
            purpose="Build rotational core power for overhead smashes",
        ),
    ],
    "movement_efficiency": [
        DrillResponse(
            name="Six-Corner Ghosting Drill",
            description="Move to all six corners of the court in sequence without a shuttlecock, "
            "simulating strokes at each corner. Focus on efficient split-step footwork patterns.",
            duration_minutes=15, sets=3, repetitions=8, difficulty="intermediate",
            purpose="Optimize court footwork patterns and eliminate wasted steps",
        ),
    ],
}

# Templates for explanations based on score ranges
EXPLANATION_TEMPLATES = {
    "low": "Your {area} is currently an area that needs significant attention. "
    "The analysis shows inconsistency in this aspect across the reviewed footage. "
    "Focused practice on the recommended drills should yield noticeable improvement.",
    "medium": "Your {area} is developing but has room for improvement. "
    "There are moments of good execution mixed with inconsistency. "
    "Regular practice targeting this area will help build more reliable technique.",
    "high": "Your {area} is a strong part of your game. "
    "Continue to maintain this level while focusing improvement efforts elsewhere.",
}

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class DemoAICoachService(AICoachService):
    """Rule-based coaching service that works without any external API.

    Analyzes actual metric data to identify strengths, weaknesses,
    and prescribes appropriate drills from the built-in library.
    """

    def generate_report(self, analysis_data: dict) -> CoachingReport:
        scores = analysis_data.get("scores", {})

        # Collect all individual metrics with their values
        all_metrics: dict[str, float] = {}
        for metric in analysis_data.get("metrics", []):
            if metric.get("value") is not None:
                all_metrics[metric["name"]] = metric["value"]

        # Also include top-level scores
        score_mapping = {
            "technique": scores.get("technique"),
            "movement": scores.get("movement"),
            "serve": scores.get("serve"),
            "consistency": scores.get("consistency"),
        }
        for name, val in score_mapping.items():
            if val is not None:
                all_metrics[name] = val

        # Sort metrics by value to identify strengths and weaknesses
        sorted_metrics = sorted(all_metrics.items(), key=lambda x: x[1])

        # Weaknesses: lowest-scoring metrics (below 70 or bottom 3)
        weaknesses = []
        for name, value in sorted_metrics[:4]:
            if value < 80:
                label = name.replace("_", " ").title()
                weaknesses.append(f"{label} ({value:.0f}/100)")
        if not weaknesses:
            weaknesses = ["No significant weaknesses detected"]

        # Strengths: highest-scoring metrics
        strengths = []
        for name, value in sorted_metrics[-3:]:
            if value >= 60:
                label = name.replace("_", " ").title()
                strengths.append(f"{label} ({value:.0f}/100)")
        if not strengths:
            strengths = ["Continue developing fundamentals"]

        # Priority: lowest-scoring metric
        if sorted_metrics:
            priority_name, priority_value = sorted_metrics[0]
            priority_label = priority_name.replace("_", " ").title()

            if priority_value < 50:
                template = EXPLANATION_TEMPLATES["low"]
            elif priority_value < 70:
                template = EXPLANATION_TEMPLATES["medium"]
            else:
                template = EXPLANATION_TEMPLATES["high"]
            explanation = template.format(area=priority_label.lower())
        else:
            priority_label = "General technique"
            explanation = "Upload more footage for a detailed analysis."

        # Select drills for weaknesses
        drills = []
        seen_drills: set[str] = set()
        for name, _value in sorted_metrics[:5]:
            if name in DRILL_LIBRARY:
                for drill in DRILL_LIBRARY[name]:
                    if drill.name not in seen_drills:
                        drills.append(drill)
                        seen_drills.add(drill.name)
                        if len(drills) >= 5:
                            break
            if len(drills) >= 5:
                break

        # If not enough drills matched, add general ones
        if len(drills) < 3:
            for drill_list in DRILL_LIBRARY.values():
                for drill in drill_list:
                    if drill.name not in seen_drills:
                        drills.append(drill)
                        seen_drills.add(drill.name)
                        if len(drills) >= 3:
                            break
                if len(drills) >= 3:
                    break

        # Generate weekly plan
        plan_parts = []
        training_days = ["Monday", "Wednesday", "Friday"]
        focus_areas = [d.purpose for d in drills[:3]]
        for i, day in enumerate(training_days):
            focus = focus_areas[i] if i < len(focus_areas) else "General practice"
            relevant_drills = [d.name for d in drills[i:i+2]] if i < len(drills) else [drills[0].name] if drills else ["Practice"]
            plan_parts.append(f"{day}: {focus} — {', '.join(relevant_drills)}")

        weekly_plan = "\n".join(plan_parts)

        return CoachingReport(
            strengths=strengths,
            weaknesses=weaknesses,
            priority_improvement=priority_label,
            explanation=explanation,
            drills=drills,
            weekly_plan=weekly_plan,
        )
