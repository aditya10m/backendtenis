"""Full computer vision analysis pipeline — orchestrates frame extraction, pose estimation,
feature extraction, and metric calculation."""

import os
import logging
from typing import Callable, Optional

import cv2
import numpy as np

from app.cv.pose_estimator import MediaPipePoseEstimator
from app.cv.feature_extractor import TennisFeatureExtractor
from app.cv.metric_calculator import TennisMetricCalculator
from app.cv.match_play_skeleton import MatchPlaySkeletonTracker
from app.cv.base import PoseEstimator, MetricResult

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Orchestrates the full video analysis pipeline.

    1. Extract frames from video
    2. Detect player + estimate pose per frame
    3. Extract biomechanical features from landmark sequence
    4. Calculate badminton-specific metrics
    """

    def __init__(
        self,
        pose_estimator: Optional[PoseEstimator] = None,
        callback: Optional[Callable[[str, int], None]] = None,
        target_fps: float = 2.0,
    ):
        self.pose_estimator = pose_estimator
        self.feature_extractor = TennisFeatureExtractor()
        self.metric_calculator = TennisMetricCalculator()
        self.callback = callback
        self.target_fps = target_fps

    def _update(self, status: str, progress: int) -> None:
        if self.callback:
            self.callback(status, progress)

    def _extract_frames(self, video_path: str) -> list[np.ndarray]:
        """Extract frames from video at target FPS using OpenCV."""
        self._update("extracting_frames", 10)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = max(1, int(video_fps / self.target_fps))

        frames: list[np.ndarray] = []
        frame_idx = 0
        max_frames = 300  # Limit to prevent memory issues

        while cap.isOpened() and len(frames) < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % frame_interval == 0:
                frames.append(frame)
            frame_idx += 1

        cap.release()
        logger.info("Extracted %d frames from %d total (interval=%d)", len(frames), total_frames, frame_interval)
        return frames

    def _estimate_poses(self, frames: list[np.ndarray]) -> list[list[dict]]:
        """Run pose estimation on each frame."""
        self._update("estimating_pose", 30)

        if self.pose_estimator is None:
            try:
                self.pose_estimator = MediaPipePoseEstimator()
            except Exception as e:
                logger.warning("Could not initialize MediaPipe: %s", e)
                return []

        all_landmarks: list[list[dict]] = []
        for i, frame in enumerate(frames):
            try:
                result = self.pose_estimator.estimate(frame)
                if result.landmarks and result.confidence > 0.3:
                    all_landmarks.append(result.landmarks)
            except Exception as e:
                logger.warning("Pose estimation failed for frame %d: %s", i, e)

            if i % 10 == 0:
                progress = 30 + int((i / max(len(frames), 1)) * 25)
                self._update("estimating_pose", min(progress, 55))

        logger.info("Got poses for %d / %d frames", len(all_landmarks), len(frames))
        return all_landmarks

    def _generate_synthetic_poses(self, num_frames: int) -> list[list[dict]]:
        """Generate synthetic pose data when MediaPipe is unavailable.
        Used for testing and demo mode."""
        rng = np.random.RandomState(42)
        poses = []
        for i in range(num_frames):
            t = i / max(num_frames - 1, 1)
            landmarks = []
            # Generate 33 landmarks with realistic positions
            base_positions = [
                (0.5, 0.15),   # 0: nose
                (0.48, 0.16),  # 1: left eye inner
                (0.47, 0.15),  # 2: left eye
                (0.46, 0.16),  # 3: left eye outer
                (0.52, 0.16),  # 4: right eye inner
                (0.53, 0.15),  # 5: right eye
                (0.54, 0.16),  # 6: right eye outer
                (0.44, 0.18),  # 7: left ear
                (0.56, 0.18),  # 8: right ear
                (0.48, 0.22),  # 9: mouth left
                (0.52, 0.22),  # 10: mouth right
                (0.40, 0.30),  # 11: left shoulder
                (0.60, 0.30),  # 12: right shoulder
                (0.35, 0.42),  # 13: left elbow
                (0.65, 0.42),  # 14: right elbow
                (0.30, 0.50),  # 15: left wrist
                (0.70 + 0.05 * np.sin(t * 3.14), 0.35 - 0.1 * t),  # 16: right wrist (moving)
                (0.28, 0.52),  # 17: left pinky
                (0.72, 0.37),  # 18: right pinky
                (0.29, 0.51),  # 19: left index
                (0.71, 0.36),  # 20: right index
                (0.30, 0.50),  # 21: left thumb
                (0.70, 0.35),  # 22: right thumb
                (0.43, 0.55),  # 23: left hip
                (0.57, 0.55),  # 24: right hip
                (0.42, 0.72 + 0.03 * np.sin(t * 2)),  # 25: left knee
                (0.58, 0.72 + 0.03 * np.sin(t * 2)),  # 26: right knee
                (0.41, 0.90),  # 27: left ankle
                (0.59, 0.90),  # 28: right ankle
                (0.40, 0.92),  # 29: left heel
                (0.60, 0.92),  # 30: right heel
                (0.39, 0.93),  # 31: left foot index
                (0.61, 0.93),  # 32: right foot index
            ]
            for bx, by in base_positions:
                noise_x = rng.normal(0, 0.005)
                noise_y = rng.normal(0, 0.005)
                landmarks.append({
                    "x": bx + noise_x,
                    "y": by + noise_y,
                    "z": rng.normal(0, 0.01),
                    "visibility": 0.85 + rng.uniform(-0.1, 0.1),
                })
            poses.append(landmarks)
        return poses

    def run(self, video_path: str, analysis_type: str) -> dict:
        """Run the full analysis pipeline on a video.

        Returns:
            dict with 'metrics' (list of MetricResult-like dicts) and
            'events' (list of detected events).
        """
        self._update("processing", 5)

        # Match Play is intentionally measured by the same frame-by-frame path
        # that powers the skeleton replay.  Do not substitute synthetic poses: a
        # video with no detectable player is reported as insufficient data.
        if analysis_type.lower() == "match":
            self._update("extracting_frames", 10)
            self._update("estimating_pose", 30)
            tracker = MatchPlaySkeletonTracker(target_fps=max(self.target_fps, 8.0))
            skeleton = tracker.analyze_match_video(video_path)
            self._update("analyzing_movement", 70)
            self._update("calculating_metrics", 85)

            metrics = [
                {
                    "name": item["name"],
                    "value": item.get("value"),
                    "confidence": item.get("confidence", 0.0),
                    "is_experimental": item.get("status") != "valid",
                    "description": item.get("description", ""),
                    "category": item.get("category", "general"),
                    "unit": item.get("unit", ""),
                }
                for item in skeleton.get("metrics", [])
            ]
            events = [
                {
                    "event_type": event.get("name", "pose_event").lower(),
                    "timestamp_ms": int(float(event.get("timestamp", 0)) * 1000),
                    "description": event.get("note", "Pose event detected"),
                    "severity": event.get("status", "info"),
                }
                for event in skeleton.get("events", [])
            ]
            self._update("generating_report", 95)
            self._update("completed", 100)
            return {
                "metrics": metrics,
                "events": events,
                "features": {},
                "skeleton": skeleton,
                "scores": skeleton.get("scores", {}),
            }
        events: list[dict] = []

        # Step 1: Extract frames
        try:
            frames = self._extract_frames(video_path)
        except Exception as e:
            logger.error("Frame extraction failed: %s", e)
            # Fallback: generate synthetic data
            frames = []

        if not frames:
            raise ValueError("No readable frames were found in the uploaded video")
        else:
            # Step 2: Pose estimation
            self._update("detecting_player", 25)
            landmark_sequence = self._estimate_poses(frames)

        if not landmark_sequence:
            raise ValueError("No pose was detected in the uploaded video")

        # Step 3: Feature extraction
        self._update("analyzing_movement", 60)
        features = self.feature_extractor.extract(landmark_sequence)
        logger.info("Extracted %d features", len(features))

        # Step 4: Metric calculation
        self._update("calculating_metrics", 75)
        metric_results = self.metric_calculator.calculate(features, analysis_type)

        # Convert MetricResult objects to dicts
        metrics = []
        for mr in metric_results:
            metrics.append({
                "name": mr.name,
                "value": mr.value,
                "confidence": mr.confidence,
                "is_experimental": mr.is_experimental,
                "description": mr.description,
                "category": self._categorize_metric(mr.name),
            })

        # Generate events from analysis
        events = self._generate_events(metric_results, len(landmark_sequence))

        self._update("generating_report", 90)
        self._update("completed", 100)

        return {"metrics": metrics, "events": events, "features": features}

    def _categorize_metric(self, name: str) -> str:
        movement_metrics = {"court_coverage", "recovery_speed", "lateral_agility", "movement_efficiency"}
        serve_metrics = {"toss_consistency", "knee_bend_depth", "contact_point_height", "follow_through_quality"}
        technique_metrics = {"preparation_quality", "follow_through", "body_rotation",
                             "balance_score", "knee_bend_quality", "head_stability", "shoulder_rotation"}

        if name in movement_metrics:
            return "movement"
        if name in serve_metrics:
            return "serve"
        if name in technique_metrics:
            return "technique"
        return "general"

    def _generate_events(self, metrics: list[MetricResult], num_frames: int) -> list[dict]:
        """Generate timeline events from metric analysis."""
        events: list[dict] = []
        frame_duration_ms = 500  # Assume 2 FPS

        for mr in metrics:
            if mr.value is None:
                continue
            if mr.value >= 85:
                events.append({
                    "event_type": "positive",
                    "timestamp_ms": int(num_frames * frame_duration_ms * 0.3),
                    "description": f"Excellent {mr.name.replace('_', ' ')}",
                    "severity": "positive",
                })
            elif mr.value < 50:
                events.append({
                    "event_type": "issue",
                    "timestamp_ms": int(num_frames * frame_duration_ms * 0.5),
                    "description": f"Needs improvement: {mr.name.replace('_', ' ')}",
                    "severity": "warning",
                })

        # Sort by timestamp
        events.sort(key=lambda e: e["timestamp_ms"])
        return events
