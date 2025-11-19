"""LLM response models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMClassificationResult:
    """Результат классификации от LLM."""
    is_order: bool
    category: str  # Backend, Frontend, Mobile, AI/ML, Low-Code, Other
    relevance_score: float  # 0.0-1.0
    reason: str
    tokens_used: Optional[int] = None  # Сколько токенов использовано (если известно)
    cost_usd: Optional[float] = None  # Стоимость этого запроса (если известна)
    
    def __repr__(self):
        status = "✓ ORDER" if self.is_order else "✗ NOT ORDER"
        return f"<LLMResult {status} | {self.category} ({self.relevance_score:.2f}) | {self.reason[:50]}...>"

