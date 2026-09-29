from anthropic import Anthropic
from config.settings import CLAUDE_API_KEY
import json
from typing import Optional

class SalesAIAgent:
    def __init__(self, business_context: str, target_audience: str):
        """
        Инициализирует AI агента для автоматизации продаж

        Args:
            business_context: Описание бизнеса клиента
            target_audience: Целевая аудитория для генерации лидов
        """
        self.client = Anthropic(api_key=CLAUDE_API_KEY)
        self.business_context = business_context
        self.target_audience = target_audience
        self.model = "claude-3-5-sonnet-20241022"

    def generate_lead_message(self, lead_name: str, lead_business: str = None) -> dict:
        """
        Генерирует персонализированное сообщение для лида
        """
        prompt = f"""
        Контекст: {self.business_context}
        Целевая аудитория: {self.target_audience}
        Имя потенциального клиента: {lead_name}
        {f'Его бизнес: {lead_business}' if lead_business else ''}

        Создай краткое, убедительное сообщение в Telegram для продажи наших услуг.
        Сообщение должно:
        1. Быть на русском языке
        2. Быть коротким (максимум 200 символов)
        3. Адресоваться конкретно этому человеку
        4. Содержать четкий call-to-action
        5. Не выглядеть как спам

        Ответь ТОЛЬКО текстом сообщения, без объяснений.
        """

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                "message": message.content[0].text,
                "status": "generated"
            }
        except Exception as e:
            # Fallback сообщение если API не работает
            return {
                "message": f"Привет, {lead_name}! У нас есть отличное предложение. Интересуешься? Пиши мне! 👋",
                "status": "fallback",
                "error": str(e)
            }

    def qualify_lead(self, lead_response: str) -> dict:
        """
        Квалифицирует ответ лида - определяет интерес
        """
        prompt = f"""
        Ответ потенциального клиента: "{lead_response}"

        На основе этого ответа определи:
        1. Уровень интереса (high, medium, low)
        2. Рекомендация действия (follow_up, demo, wait, rejected)
        3. Кратко объясни почему

        Ответь в формате JSON:
        {
            "interest_level": "high|medium|low",
            "action": "follow_up|demo|wait|rejected",
            "reason": "объяснение"
        }
        """

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

            try:
                response_text = message.content[0].text
                # Найди JSON в ответе
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end > start:
                    return json.loads(response_text[start:end])
            except:
                pass
        except:
            pass

        return {
            "interest_level": "medium",
            "action": "follow_up",
            "reason": "Default qualification"
        }

    def generate_follow_up(self, lead_name: str, previous_message: str, lead_response: str) -> str:
        """
        Генерирует follow-up сообщение для лида
        """
        prompt = f"""
        Первоначальное сообщение: "{previous_message}"
        Ответ клиента: "{lead_response}"
        Имя клиента: {lead_name}

        Создай умный follow-up ответ на их вопрос/возражение.
        Рекомендации:
        1. Коротко (макс 200 символов)
        2. На русском
        3. Ответить на их возражение прямо
        4. Предложить следующий шаг

        Ответь ТОЛЬКО текстом, без объяснений.
        """

        message = self.client.messages.create(
            model=self.model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text

    def analyze_business_metrics(self, total_leads: int, responses: int, conversions: int) -> dict:
        """
        Анализирует метрики работы агента
        """
        response_rate = (responses / total_leads * 100) if total_leads > 0 else 0
        conversion_rate = (conversions / responses * 100) if responses > 0 else 0

        prompt = f"""
        Метрики AI агента за период:
        - Всего лидов: {total_leads}
        - Ответов: {responses} ({response_rate:.1f}%)
        - Конверсии: {conversions} ({conversion_rate:.1f}%)

        Дай рекомендацию: как улучшить результаты?
        Ответь кратко (2-3 предложения) на русском.
        """

        message = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            "response_rate": response_rate,
            "conversion_rate": conversion_rate,
            "recommendation": message.content[0].text
        }
