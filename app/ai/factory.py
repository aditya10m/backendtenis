from app.core.config import settings
from app.ai.base import AICoachService
from app.ai.demo_service import DemoAICoachService
from app.ai.llm_service import LLMCoachService

def get_ai_service() -> AICoachService:
    if settings.AI_API_KEY:
        return LLMCoachService()
    return DemoAICoachService()
