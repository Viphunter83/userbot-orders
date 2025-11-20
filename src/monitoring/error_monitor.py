"""Мониторинг ошибок и метрик."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import defaultdict
from loguru import logger


class ErrorMonitor:
    """Мониторинг ошибок и метрик."""
    
    def __init__(self, error_threshold: int = 10, time_window_minutes: int = 60):
        """
        Инициализировать мониторинг ошибок.
        
        Args:
            error_threshold: Порог ошибок для алерта
            time_window_minutes: Временное окно для подсчета ошибок
        """
        self.error_threshold = error_threshold
        self.time_window = timedelta(minutes=time_window_minutes)
        
        self.error_count = 0
        self.errors_by_type: Dict[str, int] = defaultdict(int)
        self.errors_by_component: Dict[str, int] = defaultdict(int)
        self.last_error_time: Optional[datetime] = None
        self.error_history: list = []  # Список последних ошибок
    
    def record_error(
        self, 
        error_type: str, 
        component: str = "unknown",
        details: Optional[Dict[str, Any]] = None,
        exc: Optional[Exception] = None
    ):
        """
        Записать ошибку.
        
        Args:
            error_type: Тип ошибки (например, "database_error", "validation_error")
            component: Компонент системы (например, "database", "telegram", "llm")
            details: Дополнительные детали ошибки
            exc: Исключение (если есть)
        """
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        self.errors_by_type[error_type] += 1
        self.errors_by_component[component] += 1
        
        error_record = {
            "timestamp": self.last_error_time.isoformat(),
            "type": error_type,
            "component": component,
            "details": details or {},
            "exception": str(exc) if exc else None,
        }
        
        self.error_history.append(error_record)
        
        # Ограничить историю последними 100 ошибками
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
        
        # Логирование
        logger.error(
            f"Error #{self.error_count} [{component}] {error_type}",
            extra={"error_details": details, "exception": str(exc) if exc else None}
        )
        
        # Проверка порога для алерта
        if self.error_count >= self.error_threshold:
            self._send_alert(error_type, component, details)
    
    def _send_alert(self, error_type: str, component: str, details: Optional[Dict[str, Any]]):
        """Отправить алерт при превышении порога."""
        logger.warning(
            f"🚨 ALERT: Error threshold exceeded! "
            f"Total errors: {self.error_count}, "
            f"Last error: {error_type} in {component}"
        )
        
        # Здесь можно добавить отправку уведомлений:
        # - Email
        # - Telegram бот
        # - Webhook
        # - и т.д.
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику ошибок."""
        # Очистить старые ошибки из истории
        cutoff_time = datetime.now() - self.time_window
        self.error_history = [
            e for e in self.error_history 
            if datetime.fromisoformat(e["timestamp"]) > cutoff_time
        ]
        
        return {
            "total_errors": self.error_count,
            "errors_in_window": len(self.error_history),
            "last_error_time": self.last_error_time.isoformat() if self.last_error_time else None,
            "errors_by_type": dict(self.errors_by_type),
            "errors_by_component": dict(self.errors_by_component),
            "recent_errors": self.error_history[-10:] if self.error_history else [],
        }
    
    def reset(self):
        """Сбросить счетчики ошибок."""
        self.error_count = 0
        self.errors_by_type.clear()
        self.errors_by_component.clear()
        self.error_history.clear()
        self.last_error_time = None
        logger.info("Error monitor reset")


# Global instance
error_monitor = ErrorMonitor()

