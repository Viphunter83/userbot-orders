"""Валидация данных перед сохранением в БД."""

from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field, validator


class MessageData(BaseModel):
    """Валидация данных сообщения."""
    message_id: str = Field(..., min_length=1, max_length=50)
    chat_id: str = Field(..., min_length=1, max_length=50)
    author_id: str = Field(..., min_length=1, max_length=50)
    author_name: Optional[str] = Field(None, max_length=255)
    text: str = Field(..., min_length=1, max_length=10000)
    timestamp: datetime
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()


class OrderData(BaseModel):
    """Валидация данных заказа."""
    message_id: str = Field(..., min_length=1, max_length=50)
    chat_id: str = Field(..., min_length=1, max_length=50)
    author_id: str = Field(..., min_length=1, max_length=50)
    author_name: Optional[str] = Field(None, max_length=255)
    text: str = Field(..., min_length=1, max_length=10000)
    category: str = Field(..., min_length=1, max_length=50)
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    detected_by: str = Field(..., min_length=1, max_length=20)
    telegram_link: Optional[str] = Field(None, max_length=500)
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        return v.strip()
    
    @validator('category')
    def validate_category(cls, v):
        allowed_categories = [
            "Backend", "Frontend", "Mobile", "AI/ML", 
            "DevOps", "Design", "Low-Code", "Other"
        ]
        if v not in allowed_categories:
            logger.warning(f"Unknown category: {v}, allowing anyway")
        return v
    
    @validator('detected_by')
    def validate_detected_by(cls, v):
        allowed_methods = ["regex", "llm", "manual"]
        if v not in allowed_methods:
            raise ValueError(f"detected_by must be one of {allowed_methods}, got {v}")
        return v
    
    @validator('telegram_link')
    def validate_telegram_link(cls, v):
        if v and not v.startswith("https://t.me/"):
            logger.warning(f"Invalid telegram link format: {v}")
        return v


class ChatData(BaseModel):
    """Валидация данных чата."""
    chat_id: str = Field(..., min_length=1, max_length=50)
    chat_name: str = Field(..., min_length=1, max_length=255)
    chat_type: str = Field(..., min_length=1, max_length=20)
    is_active: bool = True
    
    @validator('chat_type')
    def validate_chat_type(cls, v):
        allowed_types = ["group", "supergroup", "channel", "private"]
        if v not in allowed_types:
            logger.warning(f"Unknown chat type: {v}, allowing anyway")
        return v


def validate_message_data(data: Dict[str, Any]) -> MessageData:
    """Валидировать данные сообщения."""
    try:
        return MessageData(**data)
    except Exception as e:
        logger.error(f"Message data validation failed: {e}")
        raise ValueError(f"Invalid message data: {e}")


def validate_order_data(data: Dict[str, Any]) -> OrderData:
    """Валидировать данные заказа."""
    try:
        return OrderData(**data)
    except Exception as e:
        logger.error(f"Order data validation failed: {e}")
        raise ValueError(f"Invalid order data: {e}")


def validate_chat_data(data: Dict[str, Any]) -> ChatData:
    """Валидировать данные чата."""
    try:
        return ChatData(**data)
    except Exception as e:
        logger.error(f"Chat data validation failed: {e}")
        raise ValueError(f"Invalid chat data: {e}")

