"""Tests for the deterministic scoring engine."""

from app.analytics.scoring_engine import ScoringEngine


def test_scoring_determinism():
    """Same inputs must always produce same outputs."""
    engine = ScoringEngine()
    metrics = {"preparation_quality": 80.0, "follow_through": 90.0, "body_rotation": 70.0}
    score1 = engine.calculate_technique_score(metrics)
    score2 = engine.calculate_technique_score(metrics)
    assert score1 == score2
    assert score1 is not None


def test_scoring_all_metrics():
    """Test scoring with all technique metrics present."""
    engine = ScoringEngine()
    metrics = {
        "preparation_quality": 80.0,
        "follow_through": 85.0,
        "body_rotation": 70.0,
        "balance_score": 75.0,
        "knee_bend_quality": 65.0,
        "head_stability": 90.0,
        "shoulder_rotation": 72.0,
    }
    score = engine.calculate_technique_score(metrics)
    assert score is not None
    assert 0 <= score <= 100


def test_scoring_empty_metrics():
    """No metrics should return None."""
    engine = ScoringEngine()
    assert engine.calculate_technique_score({}) is None
    assert engine.calculate_movement_score({}) is None
    assert engine.calculate_serve_score({}) is None


def test_scoring_partial_metrics():
    """Partial metrics should still produce a valid score."""
    engine = ScoringEngine()
    metrics = {"preparation_quality": 80.0}
    score = engine.calculate_technique_score(metrics)
    assert score is not None
    assert score == 80.0


def test_scoring_clamping():
    """Values outside 0-100 should be clamped."""
    engine = ScoringEngine()
    metrics = {"preparation_quality": 150.0, "follow_through": -20.0}
    score = engine.calculate_technique_score(metrics)
    assert score is not None
    assert 0 <= score <= 100


def test_movement_scoring():
    """Test movement score calculation."""
    engine = ScoringEngine()
    metrics = {
        "court_coverage": 80.0,
        "recovery_speed": 70.0,
        "lateral_agility": 75.0,
        "movement_efficiency": 65.0,
    }
    score = engine.calculate_movement_score(metrics)
    assert score is not None
    assert 0 <= score <= 100


def test_serve_scoring():
    """Test serve score calculation."""
    engine = ScoringEngine()
    metrics = {
        "toss_consistency": 72.0,
        "knee_bend_depth": 68.0,
        "contact_point_height": 74.0,
        "follow_through_quality": 73.0,
    }
    score = engine.calculate_serve_score(metrics)
    assert score is not None
    assert 0 <= score <= 100


def test_overall_scoring():
    """Test overall score with all category scores."""
    engine = ScoringEngine()
    overall = engine.calculate_overall_score(
        technique=75.0,
        movement=80.0,
        serve=70.0,
        consistency=72.0,
    )
    assert overall is not None
    assert 0 <= overall <= 100


def test_overall_with_none_categories():
    """Overall score should handle None category scores."""
    engine = ScoringEngine()
    overall = engine.calculate_overall_score(
        technique=75.0,
        movement=None,
        serve=70.0,
        consistency=None,
    )
    assert overall is not None
    assert 0 <= overall <= 100


def test_overall_all_none():
    """All None should return None."""
    engine = ScoringEngine()
    assert engine.calculate_overall_score(None, None, None, None) is None


def test_consistency_scoring():
    """Test consistency score calculation."""
    engine = ScoringEngine()
    metrics = {
        "preparation_quality": 78.0,
        "follow_through": 82.0,
        "balance_score": 76.0,
        "head_stability": 80.0,
    }
    score = engine.calculate_consistency_score(metrics)
    assert score is not None
    assert 0 <= score <= 100


def test_scoring_rounding():
    """Scores should be rounded to 1 decimal place."""
    engine = ScoringEngine()
    metrics = {"preparation_quality": 77.777}
    score = engine.calculate_technique_score(metrics)
    assert score is not None
    # Check it's rounded to 1 decimal
    assert score == round(score, 1)
