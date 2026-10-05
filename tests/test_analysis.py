"""Tests for the AI coaching demo service."""

from app.ai.demo_service import DemoAICoachService


def test_demo_service_generates_report():
    """Demo service should generate a complete coaching report."""
    service = DemoAICoachService()
    analysis_data = {
        "scores": {
            "overall": 72.0,
            "technique": 68.0,
            "movement": 78.0,
            "serve": 65.0,
            "consistency": 70.0,
        },
        "metrics": [
            {"name": "preparation_quality", "value": 60.0},
            {"name": "follow_through", "value": 85.0},
            {"name": "balance_score", "value": 78.0},
            {"name": "court_coverage", "value": 82.0},
            {"name": "toss_consistency", "value": 55.0},
            {"name": "knee_bend_depth", "value": 50.0},
        ],
    }
    report = service.generate_report(analysis_data)

    assert len(report.strengths) > 0
    assert len(report.weaknesses) > 0
    assert report.priority_improvement != ""
    assert report.explanation != ""
    assert len(report.drills) > 0
    assert report.weekly_plan is not None


def test_demo_service_no_metrics():
    """Demo service should handle missing metrics gracefully."""
    service = DemoAICoachService()
    report = service.generate_report({"scores": {}, "metrics": []})
    assert report is not None
    assert report.priority_improvement != ""


def test_demo_service_drills_have_details():
    """Drills should have name, description, and purpose."""
    service = DemoAICoachService()
    report = service.generate_report({
        "scores": {"technique": 50.0},
        "metrics": [
            {"name": "preparation_quality", "value": 40.0},
            {"name": "follow_through", "value": 45.0},
        ],
    })
    for drill in report.drills:
        assert drill.name != ""
        assert drill.description is not None
        assert drill.purpose is not None


def test_demo_service_identifies_weaknesses():
    """Low-scoring metrics should appear as weaknesses."""
    service = DemoAICoachService()
    report = service.generate_report({
        "scores": {},
        "metrics": [
            {"name": "preparation_quality", "value": 30.0},
            {"name": "follow_through", "value": 90.0},
            {"name": "balance_score", "value": 85.0},
        ],
    })
    # The lowest metric should be the priority
    assert "Preparation Quality" in report.priority_improvement
