from abc import ABC, abstractmethod
from typing import List, Dict, Any

class PoseResult:
    def __init__(self, landmarks: List[Dict[str, float]], confidence: float):
        self.landmarks = landmarks
        self.confidence = confidence

class BoundingBox:
    def __init__(self, x1, y1, x2, y2, confidence):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.confidence = confidence

class MetricResult:
    def __init__(self, name: str, value: float, confidence: float, is_experimental: bool, description: str):
        self.name = name
        self.value = value
        self.confidence = confidence
        self.is_experimental = is_experimental
        self.description = description

class PoseEstimator(ABC):
    @abstractmethod
    def estimate(self, frame) -> PoseResult:
        pass

class PlayerDetector(ABC):
    @abstractmethod
    def detect(self, frame) -> List[BoundingBox]:
        pass

class FeatureExtractor(ABC):
    @abstractmethod
    def extract(self, landmarks) -> Dict[str, float]:
        pass

class MetricCalculator(ABC):
    @abstractmethod
    def calculate(self, features, analysis_type: str) -> List[MetricResult]:
        pass
