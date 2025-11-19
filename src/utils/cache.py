"""Simple in-memory cache for LLM responses."""

import time
from typing import Optional, Dict, Any


class SimpleCache:
    """Простое кеширование в памяти с TTL."""
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Инициализировать кеш.
        
        Args:
            ttl_seconds: Время жизни записи в секундах
        """
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple[Any, float]] = {}
    
    def set(self, key: str, value: Any) -> None:
        """Сохранить значение с TTL."""
        self.cache[key] = (value, time.time())
    
    def get(self, key: str) -> Optional[Any]:
        """Получить значение если оно не истекло."""
        if key not in self.cache:
            return None
        
        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            return None
        
        return value
    
    def clear(self) -> None:
        """Очистить весь кеш."""
        self.cache.clear()
    
    def cleanup_expired(self) -> None:
        """Удалить истёкшие записи."""
        now = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp > self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]

