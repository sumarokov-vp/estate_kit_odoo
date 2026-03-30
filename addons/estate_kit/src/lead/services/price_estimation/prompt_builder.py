SYSTEM_PROMPT = (
    "Ты — эксперт по рынку недвижимости Казахстана. "
    "Пользователь даёт критерии поиска объекта недвижимости. "
    "Ответь ТОЛЬКО числом — средней рыночной стоимостью в тенге (KZT), "
    "без пробелов, запятых, валюты и пояснений. Например: 45000000"
)


class PromptBuilder:
    def build(self, criteria: dict) -> str:
        parts = []

        labels = {
            "deal_type": "Тип сделки",
            "property_type": "Тип объекта",
            "city": "Город",
            "districts": "Районы",
            "rooms_min": "Комнат от",
            "rooms_max": "Комнат до",
            "area_min": "Площадь от (м²)",
            "area_max": "Площадь до (м²)",
        }

        for key, label in labels.items():
            if key in criteria:
                parts.append(f"{label}: {criteria[key]}")

        return "\n".join(parts)
