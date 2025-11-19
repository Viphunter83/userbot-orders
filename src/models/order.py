"""Order data models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID

from src.models.enums import OrderCategory, DetectionMethod


@dataclass
class OrderDetectionResult:
    """Результат детекции заказа."""
    category: OrderCategory
    confidence: float  # 0.0-1.0
    detected_by: DetectionMethod
    matched_pattern: str
    matched_text: str


class OrderAnalysis(BaseModel):
    """Order analysis result from LLM."""
    is_order: bool
    order_title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    deadline: Optional[str] = None
    requirements: List[str] = Field(default_factory=list)
    contact: Optional[str] = None
    category: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    error: Optional[str] = None
    raw_content: Optional[str] = None


class TelegramMessage(BaseModel):
    """Telegram message model."""
    id: int
    chat_id: int
    message_text: str
    date: datetime
    author_id: Optional[int] = None
    author_username: Optional[str] = None
    is_forwarded: bool = False
    forwarded_from_chat_id: Optional[int] = None
    has_media: bool = False
    media_type: Optional[str] = None
    raw_data: Optional[dict] = None


class Order(BaseModel):
    """Order model."""
    id: Optional[UUID] = None
    message_id: int
    chat_id: int
    channel_name: Optional[str] = None
    order_title: str
    description: Optional[str] = None
    price: Optional[str] = None
    deadline: Optional[str] = None
    requirements: List[str] = Field(default_factory=list)
    contact: Optional[str] = None
    category: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    status: str = Field(default="new")  # new, processed, archived
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    analysis_metadata: Optional[dict] = None

