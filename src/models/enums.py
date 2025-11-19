"""Enum для категорий заказов и методов детекции."""

from enum import Enum


class OrderCategory(str, Enum):
    """Все возможные категории заказов."""
    
    BACKEND = "Backend"
    FRONTEND = "Frontend"
    MOBILE = "Mobile"
    AI_ML = "AI/ML"
    LOW_CODE = "Low-Code"
    OTHER = "Other"
    
    @classmethod
    def list_all(cls) -> list[str]:
        """Вернуть все категории как список строк."""
        return [c.value for c in cls]


class DetectionMethod(str, Enum):
    """Метод детекции заказа."""
    
    REGEX = "regex"
    LLM = "llm"
    MANUAL = "manual"

