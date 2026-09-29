import random
from typing import List
from datetime import datetime

# Примеры потенциальных клиентов в Ташкенте
TASHKENT_PROSPECTS = [
    {"name": "Фарход", "type": "restaurant", "field": "общепит"},
    {"name": "Дильфуза", "type": "shop", "field": "розница"},
    {"name": "Азиз", "type": "service", "field": "услуги"},
    {"name": "Мария", "type": "salon", "field": "красота"},
    {"name": "Самир", "type": "delivery", "field": "доставка"},
    {"name": "Лола", "type": "tutor", "field": "образование"},
    {"name": "Жавохир", "type": "repair", "field": "ремонт"},
    {"name": "Насрин", "type": "design", "field": "дизайн"},
    {"name": "Камол", "type": "construction", "field": "строительство"},
    {"name": "Тахир", "type": "trading", "field": "торговля"},
]

class LeadGenerator:
    def __init__(self):
        self.generated_leads = []

    def generate_leads(self, count: int = 10, business_type: str = None) -> List[dict]:
        """
        Генерирует список потенциальных лидов для обращения
        """
        leads = []
        available = [p for p in TASHKENT_PROSPECTS
                    if business_type is None or p["type"] == business_type]

        # Выбираем случайных лидов
        selected = random.sample(available, min(count, len(available)))

        for prospect in selected:
            lead = {
                "name": prospect["name"],
                "business_type": prospect["type"],
                "contact": f"+998{random.randint(10, 99)}{random.randint(1000000, 9999999)}",
                "field": prospect["field"],
                "priority": random.choice(["high", "medium", "low"]),
                "generated_at": datetime.utcnow().isoformat()
            }
            leads.append(lead)

        self.generated_leads.extend(leads)
        return leads

    def get_trending_businesses(self) -> List[dict]:
        """
        Возвращает тренды по типам бизнеса в Ташкенте
        """
        return [
            {"type": "restaurant", "growth": 45, "competition": "high"},
            {"type": "delivery", "growth": 60, "competition": "very_high"},
            {"type": "salon", "growth": 35, "competition": "medium"},
            {"type": "service", "growth": 50, "competition": "medium"},
            {"type": "shop", "growth": 20, "competition": "very_high"},
            {"type": "tutor", "growth": 55, "competition": "low"},
            {"type": "design", "growth": 40, "competition": "low"},
        ]

    def filter_leads_by_criteria(self, leads: List[dict],
                                priority: str = None,
                                business_type: str = None) -> List[dict]:
        """
        Фильтрует лидов по критериям
        """
        filtered = leads

        if priority:
            filtered = [l for l in filtered if l.get("priority") == priority]

        if business_type:
            filtered = [l for l in filtered if l.get("business_type") == business_type]

        return filtered

    def get_lead_stats(self) -> dict:
        """
        Возвращает статистику по сгенерированным лидам
        """
        if not self.generated_leads:
            return {"total": 0}

        business_types = {}
        for lead in self.generated_leads:
            bt = lead.get("business_type", "unknown")
            business_types[bt] = business_types.get(bt, 0) + 1

        return {
            "total": len(self.generated_leads),
            "by_type": business_types,
            "avg_priority": sum(1 for l in self.generated_leads if l.get("priority") == "high") / len(self.generated_leads) * 100
        }
