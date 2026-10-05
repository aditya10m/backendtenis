"""High-accuracy Pose Estimator using MediaPipe Tasks PoseLandmarker.

Supports 33 full-body landmarks, 3D joint angle calculation, bounding box
derivation, and temporal smoothing for tennis biomechanics.
"""

from pathlib import Path
import math
import os
import urllib.request
from typing import List, Dict, Any, Optional, Tuple
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    RunningMode,
)

from app.cv.base import PoseEstimator, PoseResult

# Model path resolution
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "pose_landmarker_full.task"
MODEL_DOWNLOAD_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"
)

# Standard landmark indices
LANDMARKS = {
    "nose": 0,
    "left_eye_inner": 1,
    "left_eye": 2,
    "left_eye_outer": 3,
    "right_eye_inner": 4,
    "right_eye": 5,
    "right_eye_outer": 6,
    "left_ear": 7,
    "right_ear": 8,
    "mouth_left": 9,
    "mouth_right": 10,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
    "left_pinky": 17,
    "right_pinky": 18,
    "left_index": 19,
    "right_index": 20,
    "left_thumb": 21,
    "right_thumb": 22,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
    "left_heel": 29,
    "right_heel": 30,
    "left_foot_index": 31,
    "right_foot_index": 32,
}


def compute_angle_3d(a: Dict[str, float], b: Dict[str, float], c: Dict[str, float]) -> Optional[float]:
    """Compute 3D angle at vertex b formed by rays ba and bc in degrees."""
    if a.get("visibility", 1.0) < 0.3 or b.get("visibility", 1.0) < 0.3 or c.get("visibility", 1.0) < 0.3:
        return None
    ba = np.array([a.get("x", 0.0) - b.get("x", 0.0), a.get("y", 0.0) - b.get("y", 0.0), a.get("z", 0.0) - b.get("z", 0.0)])
    bc = np.array([c.get("x", 0.0) - b.get("x", 0.0), c.get("y", 0.0) - b.get("y", 0.0), c.get("z", 0.0) - b.get("z", 0.0)])
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return None
    cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return round(float(math.degrees(math.acos(cos_angle))), 1)


def compute_angle_2d(a: Dict[str, float], b: Dict[str, float], c: Dict[str, float]) -> Optional[float]:
    """Compute 2D image-plane angle at vertex b formed by rays ba and bc."""
    if a.get("visibility", 1.0) < 0.3 or b.get("visibility", 1.0) < 0.3 or c.get("visibility", 1.0) < 0.3:
        return None
    ba = np.array([a.get("x", 0.0) - b.get("x", 0.0), a.get("y", 0.0) - b.get("y", 0.0)])
    bc = np.array([c.get("x", 0.0) - b.get("x", 0.0), c.get("y", 0.0) - b.get("y", 0.0)])
    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)
    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return None
    cos_angle = np.dot(ba, bc) / (norm_ba * norm_bc)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return round(float(math.degrees(math.acos(cos_angle))), 1)


class MediaPipePoseEstimator(PoseEstimator):
    """MediaPipe Tasks PoseLandmarker engine."""

    _landmarker_instance: Optional[PoseLandmarker] = None

    def __init__(self, model_path: Optional[str] = None):
        target_model = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        if not target_model.exists():
            target_model.parent.mkdir(parents=True, exist_ok=True)
            print(f"Downloading MediaPipe Pose model to {target_model}...")
            urllib.request.urlretrieve(MODEL_DOWNLOAD_URL, str(target_model))

        if MediaPipePoseEstimator._landmarker_instance is None:
            options = PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(target_model)),
                running_mode=RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=0.45,
                min_pose_presence_confidence=0.45,
                min_tracking_confidence=0.45,
            )
            MediaPipePoseEstimator._landmarker_instance = PoseLandmarker.create_from_options(options)

        self.landmarker = MediaPipePoseEstimator._landmarker_instance

    def estimate(self, frame: np.ndarray, max_dim: int = 720) -> PoseResult:
        """Estimate 33 pose landmarks on frame.
        
        Downsamples frame to max_dim for fast inference while preserving
        normalized [0.0, 1.0] coordinate invariance.
        """
        if frame is None or frame.size == 0:
            return PoseResult([], 0.0)

        h, w = frame.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / float(max(h, w))
            resized = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)
        else:
            resized = frame

        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        detection = self.landmarker.detect(mp_image)

        if not detection.pose_landmarks or len(detection.pose_landmarks) == 0:
            return PoseResult([], 0.0)

        raw_landmarks = detection.pose_landmarks[0]
        landmarks: List[Dict[str, float]] = []
        conf_sum = 0.0

        for lm in raw_landmarks:
            landmarks.append({
                "x": round(float(lm.x), 4),
                "y": round(float(lm.y), 4),
                "z": round(float(lm.z), 4),
                "visibility": round(float(getattr(lm, "visibility", 1.0) or 1.0), 3),
            })
            conf_sum += float(getattr(lm, "visibility", 1.0) or 1.0)

        conf = round(conf_sum / len(landmarks), 3) if landmarks else 0.0
        return PoseResult(landmarks, conf)
