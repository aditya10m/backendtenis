from abc import ABC, abstractmethod
from app.schemas.coaching import CoachingReport

class AICoachService(ABC):
    @abstractmethod
    def generate_report(self, analysis_data: dict) -> CoachingReport:
        pass
