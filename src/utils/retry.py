"""Retry mechanism with exponential backoff."""

import asyncio
from typing import TypeVar, Callable, Awaitable, Optional, List
from loguru import logger

T = TypeVar('T')


class RetryConfig:
    """Конфигурация для retry механизма."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: Optional[List[type]] = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions or [
            ConnectionError,
            TimeoutError,
            OSError,
            asyncio.TimeoutError,
        ]


async def retry_with_backoff(
    func: Callable[[], Awaitable[T]],
    config: Optional[RetryConfig] = None,
    operation_name: str = "operation",
) -> T:
    """
    Выполнить функцию с повторными попытками и экспоненциальной задержкой.
    
    Args:
        func: Асинхронная функция для выполнения
        config: Конфигурация retry (опционально)
        operation_name: Название операции для логирования
    
    Returns:
        Результат выполнения функции
    
    Raises:
        Последнее исключение если все попытки не удались
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_retries):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            
            # Проверить, является ли исключение retryable
            is_retryable = any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions)
            
            if not is_retryable:
                # Не retry для других ошибок
                logger.error(f"{operation_name} failed with non-retryable error: {e}")
                raise
            
            if attempt < config.max_retries - 1:
                # Вычислить задержку с экспоненциальным backoff
                delay = min(
                    config.base_delay * (config.exponential_base ** attempt),
                    config.max_delay
                )
                
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{config.max_retries}): {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"{operation_name} failed after {config.max_retries} attempts: {e}"
                )
                raise
    
    # Должно быть недостижимо, но на всякий случай
    if last_exception:
        raise last_exception
    raise RuntimeError(f"{operation_name} failed unexpectedly")

