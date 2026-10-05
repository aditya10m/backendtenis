"""Badminton feature extractor — computes biomechanical features from pose landmarks."""

import math
import numpy as np
from app.cv.base import FeatureExtractor


# MediaPipe landmark indices
NOSE = 0
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28


def _angle_between(a: dict, b: dict, c: dict) -> float:
    """Calculate angle at point b formed by points a-b-c in degrees."""
    ba = np.array([a["x"] - b["x"], a["y"] - b["y"]])
    bc = np.array([c["x"] - b["x"], c["y"] - b["y"]])
    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return math.degrees(math.acos(cos_angle))


def _distance(a: dict, b: dict) -> float:
    """Euclidean distance between two landmarks (normalized coords)."""
    return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2)


def _midpoint(a: dict, b: dict) -> dict:
    return {"x": (a["x"] + b["x"]) / 2, "y": (a["y"] + b["y"]) / 2}


class TennisFeatureExtractor(FeatureExtractor):
    """Extracts biomechanical features from a sequence of pose landmark frames."""

    def extract(self, landmarks_sequence: list) -> dict:
        """Extract features from a list of per-frame landmark lists.

        Args:
            landmarks_sequence: List of frames, each being a list of 33 landmark dicts
                with keys x, y, z, visibility.

        Returns:
            Dictionary of feature names to values.
        """
        if not landmarks_sequence:
            return {}

        features: dict[str, float] = {}
        valid_frames = [lm for lm in landmarks_sequence if len(lm) >= 29]
        if not valid_frames:
            return {}

        # Per-frame calculations
        elbow_angles = []
        knee_angles = []
        shoulder_rotations = []
        hip_positions = []
        nose_positions = []
        knee_bend_depths = []
        arm_extensions = []
        wrist_heights = []

        for lm in valid_frames:
            # Average visibility as confidence check
            avg_vis = sum(l.get("visibility", 0) for l in lm) / len(lm)
            if avg_vis < 0.3:
                continue

            # Elbow angle (dominant side — use whichever wrist is higher/more visible)
            left_elbow_angle = _angle_between(lm[LEFT_SHOULDER], lm[LEFT_ELBOW], lm[LEFT_WRIST])
            right_elbow_angle = _angle_between(lm[RIGHT_SHOULDER], lm[RIGHT_ELBOW], lm[RIGHT_WRIST])
            elbow_angles.append(min(left_elbow_angle, right_elbow_angle))

            # Knee angle (both knees)
            left_knee_angle = _angle_between(lm[LEFT_HIP], lm[LEFT_KNEE], lm[LEFT_ANKLE])
            right_knee_angle = _angle_between(lm[RIGHT_HIP], lm[RIGHT_KNEE], lm[RIGHT_ANKLE])
            knee_angles.append(min(left_knee_angle, right_knee_angle))

            # Knee bend depth (lower angle = deeper bend)
            knee_bend_depths.append(min(left_knee_angle, right_knee_angle))

            # Shoulder rotation (angle of shoulder line relative to horizontal)
            dx = lm[RIGHT_SHOULDER]["x"] - lm[LEFT_SHOULDER]["x"]
            dy = lm[RIGHT_SHOULDER]["y"] - lm[LEFT_SHOULDER]["y"]
            shoulder_angle = abs(math.degrees(math.atan2(dy, dx)))
            shoulder_rotations.append(shoulder_angle)

            # Hip center position for movement tracking
            hip_center = _midpoint(lm[LEFT_HIP], lm[RIGHT_HIP])
            hip_positions.append(hip_center)

            # Nose position for head stability
            nose_positions.append({"x": lm[NOSE]["x"], "y": lm[NOSE]["y"]})

            # Arm extension (wrist distance from shoulder, normalized by shoulder width)
            shoulder_width = _distance(lm[LEFT_SHOULDER], lm[RIGHT_SHOULDER])
            left_ext = _distance(lm[LEFT_SHOULDER], lm[LEFT_WRIST]) / (shoulder_width + 1e-8)
            right_ext = _distance(lm[RIGHT_SHOULDER], lm[RIGHT_WRIST]) / (shoulder_width + 1e-8)
            arm_extensions.append(max(left_ext, right_ext))

            # Wrist height relative to shoulder (for contact point analysis)
            wrist_heights.append(min(lm[LEFT_WRIST]["y"], lm[RIGHT_WRIST]["y"]))

        if not elbow_angles:
            return {}

        # Aggregate features
        features["elbow_angle_mean"] = float(np.mean(elbow_angles))
        features["elbow_angle_std"] = float(np.std(elbow_angles))
        features["knee_angle_mean"] = float(np.mean(knee_angles))
        features["knee_angle_std"] = float(np.std(knee_angles))
        features["knee_bend_min"] = float(np.min(knee_bend_depths))
        features["shoulder_rotation_range"] = float(np.max(shoulder_rotations) - np.min(shoulder_rotations))
        features["shoulder_rotation_mean"] = float(np.mean(shoulder_rotations))
        features["arm_extension_max"] = float(np.max(arm_extensions))
        features["arm_extension_mean"] = float(np.mean(arm_extensions))

        # Head stability: lower variance = more stable
        if len(nose_positions) >= 2:
            nose_x = [p["x"] for p in nose_positions]
            nose_y = [p["y"] for p in nose_positions]
            features["head_variance"] = float(np.var(nose_x) + np.var(nose_y))
        else:
            features["head_variance"] = 0.0

        # Movement: total displacement of hip center
        if len(hip_positions) >= 2:
            total_displacement = 0.0
            lateral_displacements = []
            for i in range(1, len(hip_positions)):
                dx = hip_positions[i]["x"] - hip_positions[i - 1]["x"]
                dy = hip_positions[i]["y"] - hip_positions[i - 1]["y"]
                total_displacement += math.sqrt(dx * dx + dy * dy)
                lateral_displacements.append(abs(dx))
            features["total_movement"] = total_displacement
            features["lateral_movement"] = float(np.mean(lateral_displacements))
            features["lateral_movement_max"] = float(np.max(lateral_displacements))
        else:
            features["total_movement"] = 0.0
            features["lateral_movement"] = 0.0
            features["lateral_movement_max"] = 0.0

        # Balance: center of gravity relative to feet midpoint
        # (simplified: hip center x relative to ankle midpoint x)
        balance_scores = []
        for lm in valid_frames:
            hip_cx = (lm[LEFT_HIP]["x"] + lm[RIGHT_HIP]["x"]) / 2
            ankle_cx = (lm[LEFT_ANKLE]["x"] + lm[RIGHT_ANKLE]["x"]) / 2
            balance_scores.append(abs(hip_cx - ankle_cx))

        if balance_scores:
            features["balance_offset_mean"] = float(np.mean(balance_scores))
            features["balance_offset_std"] = float(np.std(balance_scores))

        features["num_valid_frames"] = float(len(valid_frames))
        return features
