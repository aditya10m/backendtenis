"""Badminton metric calculator — converts raw features into badminton-specific metrics."""

import numpy as np
from app.cv.base import MetricCalculator, MetricResult


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


class TennisMetricCalculator(MetricCalculator):
    """Converts raw biomechanical features into badminton-specific metrics scored 0-100."""

    def calculate(self, features: dict, analysis_type: str) -> list[MetricResult]:
        if not features:
            return [MetricResult("no_data", None, 0.0, False, "insufficient_data")]

        num_frames = features.get("num_valid_frames", 0)
        results: list[MetricResult] = []

        # ── Technique Metrics ──

        # Preparation quality: based on elbow angle consistency (lower std = more consistent prep)
        elbow_std = features.get("elbow_angle_std")
        if elbow_std is not None and num_frames >= 3:
            score = _clamp(100 - elbow_std * 3)
            conf = min(1.0, num_frames / 10)
            results.append(MetricResult(
                "preparation_quality", round(score, 1), round(conf, 2),
                conf < 0.5, "Measures racquet preparation consistency across frames",
            ))
        else:
            results.append(MetricResult(
                "preparation_quality", None, 0.0, False, "insufficient_data",
            ))

        # Follow-through: based on max arm extension
        arm_ext_max = features.get("arm_extension_max")
        if arm_ext_max is not None and num_frames >= 3:
            # Arm extension > 2.5x shoulder width is excellent
            score = _clamp(arm_ext_max * 40)
            conf = min(1.0, num_frames / 10)
            results.append(MetricResult(
                "follow_through", round(score, 1), round(conf, 2),
                conf < 0.5, "Measures arm extension through the shot",
            ))
        else:
            results.append(MetricResult(
                "follow_through", None, 0.0, False, "insufficient_data",
            ))

        # Body rotation: based on shoulder rotation range
        rot_range = features.get("shoulder_rotation_range")
        if rot_range is not None and num_frames >= 3:
            # 30-60 degrees of rotation is good for groundstrokes
            score = _clamp(rot_range * 2.5)
            conf = min(1.0, num_frames / 10)
            results.append(MetricResult(
                "body_rotation", round(score, 1), round(conf, 2),
                conf < 0.5, "Measures upper body rotation during strokes",
            ))
        else:
            results.append(MetricResult(
                "body_rotation", None, 0.0, False, "insufficient_data",
            ))

        # Balance: lower offset from center = better balance
        balance_offset = features.get("balance_offset_mean")
        if balance_offset is not None and num_frames >= 3:
            score = _clamp(100 - balance_offset * 500)
            conf = min(1.0, num_frames / 10)
            results.append(MetricResult(
                "balance_score", round(score, 1), round(conf, 2),
                conf < 0.5, "Measures body balance stability during play",
            ))
        else:
            results.append(MetricResult(
                "balance_score", None, 0.0, False, "insufficient_data",
            ))

        # Knee bend quality: deeper bend (lower angle) is generally better
        knee_min = features.get("knee_bend_min")
        if knee_min is not None and num_frames >= 3:
            # Ideal knee angle around 120-140 degrees; 180 = straight
            score = _clamp((180 - knee_min) * 1.5)
            conf = min(1.0, num_frames / 10)
            results.append(MetricResult(
                "knee_bend_quality", round(score, 1), round(conf, 2),
                conf < 0.5, "Measures depth of knee bend for power generation",
            ))
        else:
            results.append(MetricResult(
                "knee_bend_quality", None, 0.0, False, "insufficient_data",
            ))

        # Head stability: lower variance = better
        head_var = features.get("head_variance")
        if head_var is not None and num_frames >= 3:
            score = _clamp(100 - head_var * 5000)
            conf = min(1.0, num_frames / 10)
            results.append(MetricResult(
                "head_stability", round(score, 1), round(conf, 2),
                conf < 0.5, "Measures head steadiness during strokes",
            ))
        else:
            results.append(MetricResult(
                "head_stability", None, 0.0, False, "insufficient_data",
            ))

        # Shoulder rotation (absolute)
        rot_mean = features.get("shoulder_rotation_mean")
        if rot_mean is not None and num_frames >= 3:
            score = _clamp(rot_mean * 2)
            conf = min(1.0, num_frames / 10)
            results.append(MetricResult(
                "shoulder_rotation", round(score, 1), round(conf, 2),
                conf < 0.5, "Measures average shoulder rotation angle",
            ))
        else:
            results.append(MetricResult(
                "shoulder_rotation", None, 0.0, False, "insufficient_data",
            ))

        # ── Movement Metrics ──

        total_movement = features.get("total_movement")
        if total_movement is not None and num_frames >= 3:
            # Normalize: higher movement across court = better coverage
            score = _clamp(total_movement * 200)
            conf = min(1.0, num_frames / 10)
            results.append(MetricResult(
                "court_coverage", round(score, 1), round(conf, 2),
                conf < 0.5, "Measures total court area covered during play",
            ))
        else:
            results.append(MetricResult(
                "court_coverage", None, 0.0, False, "insufficient_data",
            ))

        # Recovery speed: based on balance offset std (lower = consistent recovery)
        balance_std = features.get("balance_offset_std")
        if balance_std is not None and num_frames >= 5:
            score = _clamp(100 - balance_std * 800)
            conf = min(1.0, num_frames / 15)
            results.append(MetricResult(
                "recovery_speed", round(score, 1), round(conf, 2),
                True, "Estimated recovery speed (experimental)",
            ))
        else:
            results.append(MetricResult(
                "recovery_speed", None, 0.0, False, "insufficient_data",
            ))

        # Lateral agility
        lat_move = features.get("lateral_movement")
        lat_max = features.get("lateral_movement_max")
        if lat_move is not None and lat_max is not None and num_frames >= 3:
            score = _clamp(lat_max * 500)
            conf = min(1.0, num_frames / 10)
            results.append(MetricResult(
                "lateral_agility", round(score, 1), round(conf, 2),
                conf < 0.5, "Measures lateral movement range and speed",
            ))
        else:
            results.append(MetricResult(
                "lateral_agility", None, 0.0, False, "insufficient_data",
            ))

        # Movement efficiency: ratio of useful movement to total movement
        if total_movement and total_movement > 0 and lat_move is not None:
            efficiency = min(1.0, (lat_move * num_frames) / (total_movement + 1e-8))
            score = _clamp(efficiency * 100)
            conf = min(1.0, num_frames / 15)
            results.append(MetricResult(
                "movement_efficiency", round(score, 1), round(conf, 2),
                True, "Measures path efficiency of movement (experimental)",
            ))
        else:
            results.append(MetricResult(
                "movement_efficiency", None, 0.0, False, "insufficient_data",
            ))

        # ── Serve Metrics (only for serve analysis type) ──

        if analysis_type in ("serve", "match", "training"):
            knee_angle_mean = features.get("knee_angle_mean")
            knee_angle_std = features.get("knee_angle_std")
            if knee_angle_mean is not None and num_frames >= 3:
                score = _clamp((180 - knee_angle_mean) * 2)
                conf = min(1.0, num_frames / 10) * (0.8 if analysis_type != "serve" else 1.0)
                results.append(MetricResult(
                    "knee_bend_depth", round(score, 1), round(conf, 2),
                    analysis_type != "serve", "Depth of knee bend during serve motion",
                ))

            if knee_angle_std is not None and num_frames >= 3:
                score = _clamp(100 - knee_angle_std * 3)
                conf = min(1.0, num_frames / 10) * (0.7 if analysis_type != "serve" else 1.0)
                results.append(MetricResult(
                    "toss_consistency", round(score, 1), round(conf, 2),
                    True, "Estimated toss consistency from body motion (experimental)",
                ))

            arm_ext = features.get("arm_extension_max")
            if arm_ext is not None:
                score = _clamp(arm_ext * 35)
                conf = min(1.0, num_frames / 10) * (0.6 if analysis_type != "serve" else 0.9)
                results.append(MetricResult(
                    "contact_point_height", round(score, 1), round(conf, 2),
                    True, "Estimated contact point height from arm extension (experimental)",
                ))

            follow_idx = next((i for i, r in enumerate(results) if r.name == "follow_through"), None)
            if follow_idx is not None and results[follow_idx].value is not None:
                results.append(MetricResult(
                    "follow_through_quality", results[follow_idx].value, results[follow_idx].confidence,
                    True, "Follow-through quality on serve (experimental)",
                ))

        return results
