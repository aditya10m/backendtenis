from app.ai.base import AICoachService
from app.schemas.coaching import CoachingReport
from app.ai.demo_service import DemoAICoachService

class LLMCoachService(AICoachService):
    def generate_report(self, analysis_data: dict) -> CoachingReport:
        # Stub: normally calls OpenAI. Fallback to demo for now.
        demo = DemoAICoachService()
        return demo.generate_report(analysis_data)
