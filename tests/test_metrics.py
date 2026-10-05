"""Tests for metric calculation from CV features."""

from app.cv.metric_calculator import TennisMetricCalculator
from app.cv.feature_extractor import TennisFeatureExtractor


def test_metric_calculator_empty():
    """No features should return insufficient_data."""
    calc = TennisMetricCalculator()
    results = calc.calculate({}, "match")
    assert len(results) >= 1
    assert results[0].name == "no_data"
    assert results[0].value is None


def test_metric_calculator_with_features():
    """Valid features should produce metrics."""
    calc = TennisMetricCalculator()
    features = {
        "elbow_angle_mean": 120.0,
        "elbow_angle_std": 8.0,
        "knee_angle_mean": 150.0,
        "knee_angle_std": 5.0,
        "knee_bend_min": 130.0,
        "shoulder_rotation_range": 35.0,
        "shoulder_rotation_mean": 15.0,
        "arm_extension_max": 2.2,
        "arm_extension_mean": 1.8,
        "head_variance": 0.002,
        "total_movement": 0.5,
        "lateral_movement": 0.02,
        "lateral_movement_max": 0.05,
        "balance_offset_mean": 0.03,
        "balance_offset_std": 0.01,
        "num_valid_frames": 20.0,
    }
    results = calc.calculate(features, "match")
    assert len(results) > 5

    # Check all values are either None or in valid range
    for metric in results:
        if metric.value is not None:
            assert 0 <= metric.value <= 100, f"{metric.name} = {metric.value}"
            assert 0 <= metric.confidence <= 1, f"{metric.name} conf = {metric.confidence}"


def test_metric_calculator_serve_type():
    """Serve analysis type should produce serve-specific metrics."""
    calc = TennisMetricCalculator()
    features = {
        "elbow_angle_mean": 120.0,
        "elbow_angle_std": 8.0,
        "knee_angle_mean": 140.0,
        "knee_angle_std": 5.0,
        "knee_bend_min": 125.0,
        "shoulder_rotation_range": 40.0,
        "shoulder_rotation_mean": 20.0,
        "arm_extension_max": 2.5,
        "arm_extension_mean": 2.0,
        "head_variance": 0.001,
        "total_movement": 0.3,
        "lateral_movement": 0.01,
        "lateral_movement_max": 0.03,
        "balance_offset_mean": 0.02,
        "balance_offset_std": 0.008,
        "num_valid_frames": 15.0,
    }
    results = calc.calculate(features, "serve")
    metric_names = {m.name for m in results}
    assert "knee_bend_depth" in metric_names
    assert "toss_consistency" in metric_names
    assert "contact_point_height" in metric_names


def test_metric_insufficient_frames():
    """Too few frames should produce insufficient_data."""
    calc = TennisMetricCalculator()
    features = {
        "elbow_angle_mean": 120.0,
        "num_valid_frames": 1.0,
    }
    results = calc.calculate(features, "match")
    # Most metrics should be insufficient with only 1 frame
    null_count = sum(1 for m in results if m.value is None)
    assert null_count > 0


def test_feature_extractor_empty():
    """Empty landmarks should return empty features."""
    extractor = TennisFeatureExtractor()
    assert extractor.extract([]) == {}


def test_feature_extractor_valid():
    """Valid landmark sequences should produce features."""
    import numpy as np
    rng = np.random.RandomState(42)
    extractor = TennisFeatureExtractor()

    # Generate 10 frames of 33 landmarks
    landmarks_seq = []
    for _ in range(10):
        frame_landmarks = []
        for j in range(33):
            frame_landmarks.append({
                "x": 0.5 + rng.normal(0, 0.05),
                "y": 0.3 + j * 0.02 + rng.normal(0, 0.01),
                "z": rng.normal(0, 0.01),
                "visibility": 0.9,
            })
        landmarks_seq.append(frame_landmarks)

    features = extractor.extract(landmarks_seq)
    assert len(features) > 0
    assert "elbow_angle_mean" in features
    assert "knee_angle_mean" in features
    assert "total_movement" in features
    assert "head_variance" in features
    assert features["num_valid_frames"] == 10.0
