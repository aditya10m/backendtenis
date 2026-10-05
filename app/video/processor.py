import cv2
import os

class VideoInfo:
    def __init__(self, duration, width, height, fps):
        self.duration = duration
        self.width = width
        self.height = height
        self.fps = fps

class VideoProcessor:
    def get_video_info(self, video_path) -> VideoInfo:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return VideoInfo(0, 0, 0, 0)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frames / fps if fps > 0 else 0
        cap.release()
        return VideoInfo(duration, width, height, fps)

    def extract_frames(self, video_path, fps=2):
        cap = cv2.VideoCapture(video_path)
        frame_paths = []
        cap.release()
        return frame_paths
        
    def validate_video(self, video_path) -> bool:
        cap = cv2.VideoCapture(video_path)
        valid = cap.isOpened()
        cap.release()
        return valid

    def create_thumbnail(self, video_path) -> str:
        return "thumb.jpg"
