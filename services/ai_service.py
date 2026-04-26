"""
services/ai_service.py
Gemini 1.5 Flash integration for FAQ and recommendations.
"""

import google.generativeai as genai
from config import settings, get_logger

logger = get_logger(__name__)

# System prompt with catering business context
SYSTEM_PROMPT = """
Ты — умный ассистент кейтеринговой компании "Qazaq Catering" в Шымкенте.
Ты помогаешь клиентам с вопросами о меню, ценах, услугах и заказах.

Стиль общения: вежливый, профессиональный, на русском языке.
Если вопрос не по теме кейтеринга — мягко перенаправляй к основному меню.

Услуги:
- Организация мероприятий (той, свадьба, юбилей, корпоратив)
- Казахская кухня и современные блюда
- Доставка и выездной сервис по Шымкенту
- Минимальный заказ: уточняйте у менеджера
- Оформление заказа: через бота или WhatsApp
"""


class AIService:
    def __init__(self) -> None:
        genai.configure(api_key=settings.gemini_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=SYSTEM_PROMPT,
        )
        self._chat_sessions: dict[int, genai.ChatSession] = {}

    def _get_or_create_chat(self, user_id: int) -> genai.ChatSession:
        """Get or create a chat session per user (maintains context)."""
        if user_id not in self._chat_sessions:
            self._chat_sessions[user_id] = self.model.start_chat(history=[])
        return self._chat_sessions[user_id]

    async def ask(self, user_id: int, message: str) -> str:
        """Send message to Gemini and return response."""
        try:
            chat = self._get_or_create_chat(user_id)
            response = await chat.send_message_async(message)
            return response.text
        except Exception as e:
            logger.error(f"Gemini error for user {user_id}: {e}")
            return (
                "🤖 Извините, ИИ-ассистент временно недоступен.\n"
                "Пожалуйста, свяжитесь с нами напрямую."
            )

    def clear_history(self, user_id: int) -> None:
        """Clear chat history for user."""
        self._chat_sessions.pop(user_id, None)


# Singleton
ai_service = AIService()
