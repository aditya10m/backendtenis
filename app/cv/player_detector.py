from app.cv.base import PlayerDetector, BoundingBox

class SimplePlayerDetector(PlayerDetector):
    def detect(self, frame):
        # Stub, just returns a full-frame box
        h, w = frame.shape[:2]
        return [BoundingBox(0, 0, w, h, 1.0)]

class YOLODetector(PlayerDetector):
    def detect(self, frame):
        raise NotImplementedError("YOLO not configured")
