"""LLM-based order classification (ProxyAPI integration)."""

import asyncio
import json
import time
from typing import Optional, List
from loguru import logger
import httpx

from src.config.settings import get_settings
from src.analysis.prompts import (
    SYSTEM_PROMPT,
    format_batch_prompt,
    parse_json_response,
    parse_batch_json_response,
    validate_response_schema,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
)
from src.models.llm_response import LLMClassificationResult
from src.utils.cache import SimpleCache


class LLMClassifier:
    """
    Classifier на основе LLM через ProxyAPI.
    Второй уровень фильтрации для ambiguous сообщений.
    """
    
    def __init__(self):
        """Инициализировать classifier с ProxyAPI credentials."""
        settings = get_settings()
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model
        self.base_url = settings.llm_base_url
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout_seconds
        self.max_retries = settings.llm_max_retries
        self.batch_size = settings.llm_batch_size
        self.threshold = settings.llm_analysis_threshold
        
        # Кеширование для идентичных текстов
        self.cache = SimpleCache(ttl_seconds=settings.llm_cache_ttl_seconds) if settings.llm_enable_caching else None
        
        # Счётчики для метрик
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        self.total_requests = 0
        
        # Task для периодической очистки кеша (будет создана лениво)
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info(
            f"✓ LLMClassifier initialized",
            extra={
                "model": self.model,
                "provider": settings.llm_provider,
                "batch_size": self.batch_size,
            }
        )
    
    # ========================================================================
    # ОСНОВНЫЕ МЕТОДЫ
    # ========================================================================
    
    async def classify(self, text: str) -> Optional[LLMClassificationResult]:
        """
        Классифицировать одно сообщение.
        
        Args:
            text: Текст сообщения для анализа
        
        Returns:
            LLMClassificationResult или None если анализ не удался
        
        Example:
            result = await classifier.classify("Нужен Python разработчик")
            if result and result.is_order:
                print(f"Order detected: {result.category}")
        """
        if not text or len(text.strip()) < 3:
            return None
        
        # Нормализовать текст: убрать проблемные символы и исправить кодировку
        text = self._normalize_text(text)
        
        # Запустить очистку кеша если еще не запущена
        if self.cache and self._cleanup_task is None:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            except RuntimeError:
                pass
        
        # Проверить кеш
        if self.cache:
            cached = self.cache.get(text)
            if cached:
                logger.debug(f"Cache hit for text: {text[:50]}...")
                return cached
        
        # Проверить бюджет
        if not await self.check_budget():
            logger.warning("LLM budget exhausted, skipping classification")
            return None
        
        # Отправить в LLM
        result = await self._classify_single(text)
        
        # Сохранить в кеш
        if result and self.cache:
            self.cache.set(text, result)
        
        return result
    
    async def _cleanup_loop(self) -> None:
        """Периодически очищать истёкшие записи из кеша."""
        try:
            while True:
                try:
                    await asyncio.sleep(300)  # Каждые 5 минут
                    if self.cache:
                        self.cache.cleanup_expired()
                        cache_size = len(self.cache.cache)
                        if cache_size > 0:
                            logger.debug(f"Cache cleanup completed, cache size: {cache_size}")
                except asyncio.CancelledError:
                    logger.debug("Cache cleanup task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in cache cleanup: {e}")
        finally:
            self._cleanup_task = None
    
    def stop_cleanup_task(self) -> None:
        """Остановить задачу очистки кеша (для тестов и завершения работы)."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            logger.debug("Cache cleanup task cancellation requested")
    
    async def classify_batch(self, texts: list[str]) -> list[Optional[LLMClassificationResult]]:
        """
        Классифицировать батч сообщений (более эффективно).
        
        Args:
            texts: Список текстов для анализа (макс 10)
        
        Returns:
            Список LLMClassificationResult в том же порядке
        
        Example:
            texts = ["Нужен Python разработчик", "Ищем React специалиста"]
            results = await classifier.classify_batch(texts)
        """
        if not texts:
            return []
        
        # Нормализовать и фильтровать пустые тексты
        valid_texts = [self._normalize_text(t) for t in texts if t and len(t.strip()) >= 3]
        if not valid_texts:
            return [None] * len(texts)
        
        if len(valid_texts) > self.batch_size:
            logger.warning(f"Batch size {len(valid_texts)} exceeds max {self.batch_size}, splitting...")
            # Рекурсивно обработать по частям
            results = []
            for i in range(0, len(valid_texts), self.batch_size):
                chunk = valid_texts[i:i + self.batch_size]
                chunk_results = await self.classify_batch(chunk)
                results.extend(chunk_results)
            
            # Pad с None для пустых текстов
            final_results = []
            text_idx = 0
            for original_text in texts:
                if original_text and len(original_text.strip()) >= 3:
                    final_results.append(results[text_idx])
                    text_idx += 1
                else:
                    final_results.append(None)
            return final_results
        
        # Проверить кеш для каждого текста
        cached_results = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(valid_texts):
            if self.cache:
                cached = self.cache.get(text)
                if cached:
                    cached_results.append((i, cached))
                    logger.debug(f"Cache hit for batch item {i}")
                    continue
            uncached_texts.append(text)
            uncached_indices.append(i)
        
        # Если все в кеше
        if not uncached_texts:
            result_dict = {idx: result for idx, result in cached_results}
            return [result_dict.get(i) for i in range(len(valid_texts))]
        
        # Проверить бюджет
        if not await self.check_budget():
            logger.warning("LLM budget exhausted, skipping batch classification")
            return [None] * len(valid_texts)
        
        # Отправить только uncached в LLM
        llm_results = await self._classify_batch_llm(uncached_texts)
        
        # Собрать результаты в правильном порядке
        all_results = [None] * len(valid_texts)
        
        # Добавить кешированные
        for idx, result in cached_results:
            all_results[idx] = result
        
        # Добавить из LLM
        for original_idx, llm_result in zip(uncached_indices, llm_results):
            all_results[original_idx] = llm_result
            
            # Сохранить в кеш
            if llm_result and self.cache:
                self.cache.set(valid_texts[original_idx], llm_result)
        
        # Вернуть результаты для всех оригинальных текстов
        final_results = []
        valid_idx = 0
        for original_text in texts:
            if original_text and len(original_text.strip()) >= 3:
                final_results.append(all_results[valid_idx])
                valid_idx += 1
            else:
                final_results.append(None)
        
        return final_results
    
    # ========================================================================
    # ПРИВАТНЫЕ МЕТОДЫ
    # ========================================================================
    
    async def _classify_single(self, text: str) -> Optional[LLMClassificationResult]:
        """
        Классифицировать одно сообщение через LLM.
        С retry logic и обработкой ошибок.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response_text = await self._call_llm(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": text},
                    ]
                )
                
                # Парсить ответ
                parsed = parse_json_response(response_text)
                if not parsed:
                    logger.warning(f"Failed to parse LLM response: {response_text[:100]}")
                    if attempt < self.max_retries:
                        await asyncio.sleep(RETRY_DELAY * attempt)
                        continue
                    return None
                
                # Создать результат
                # Если is_order=False и category пустой, использовать "Other"
                category = parsed.get("category", "Other")
                if not category or category == "":
                    category = "Other"
                
                result = LLMClassificationResult(
                    is_order=parsed.get("is_order", False),
                    category=category,
                    relevance_score=float(parsed.get("relevance_score", 0.0)),
                    reason=parsed.get("reason", "No reason provided"),
                )
                
                logger.debug(
                    f"LLM classification: {result}",
                    extra={
                        "is_order": result.is_order,
                        "category": result.category,
                        "relevance": result.relevance_score,
                    }
                )
                
                return result
            
            except Exception as e:
                logger.warning(f"LLM classification attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(RETRY_DELAY * attempt)  # Exponential backoff
                    continue
                else:
                    logger.error(f"LLM classification failed after {self.max_retries} attempts")
                    return None
    
    async def _classify_batch_llm(self, texts: list[str]) -> list[Optional[LLMClassificationResult]]:
        """
        Отправить батч сообщений в LLM.
        Более эффективно чем отдельные вызовы.
        """
        if not texts:
            return []
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # Форматировать batch промпт
                batch_prompt = format_batch_prompt(texts)
                
                response_text = await self._call_llm(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": batch_prompt},
                    ]
                )
                
                # Парсить batch результаты
                parsed_list = parse_batch_json_response(response_text, len(texts))
                
                if len(parsed_list) != len(texts):
                    logger.warning(
                        f"Batch parsing mismatch: expected {len(texts)}, got {len(parsed_list)}"
                    )
                
                # Создать результаты
                results = []
                for i, parsed in enumerate(parsed_list):
                    if not parsed:
                        results.append(None)
                        continue
                    
                    # Если is_order=False и category пустой, использовать "Other"
                    category = parsed.get("category", "Other")
                    if not category or category == "":
                        category = "Other"
                    
                    result = LLMClassificationResult(
                        is_order=parsed.get("is_order", False),
                        category=category,
                        relevance_score=float(parsed.get("relevance_score", 0.0)),
                        reason=parsed.get("reason", ""),
                    )
                    results.append(result)
                
                # Pad с None если нужно
                while len(results) < len(texts):
                    results.append(None)
                
                logger.debug(f"Batch classification completed: {len(results)} items")
                return results
            
            except Exception as e:
                logger.warning(f"Batch LLM attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(RETRY_DELAY * attempt)
                    continue
                else:
                    logger.error(f"Batch LLM failed after {self.max_retries} attempts")
                    return [None] * len(texts)
    
    async def _call_llm(self, messages: list[dict]) -> str:
        """
        Отправить запрос в ProxyAPI.
        
        Args:
            messages: List of message dicts {role, content}
        
        Returns:
            Сырой текст ответа от LLM
        
        Raises:
            Exception если запрос неудачен
        """
        # Нормализовать содержимое сообщений перед отправкой
        normalized_messages = []
        for msg in messages:
            normalized_msg = msg.copy()
            if 'content' in normalized_msg and normalized_msg['content']:
                normalized_msg['content'] = self._normalize_text(normalized_msg['content'])
            normalized_messages.append(normalized_msg)
        
        payload = {
            "model": self.model,
            "messages": normalized_messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8",
        }
        
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                
                elapsed = time.time() - start_time
                
                data = response.json()
                
                # Извлечь текст из ответа
                if "choices" in data and len(data["choices"]) > 0:
                    response_text_raw = data["choices"][0].get("message", {}).get("content", "")
                    
                    # Нормализовать ответ от LLM
                    response_text = self._normalize_text(response_text_raw) if response_text_raw else ""
                    
                    # Обновить метрики
                    if "usage" in data:
                        tokens_used = data["usage"].get("total_tokens", 0)
                        self.total_tokens_used += tokens_used
                        
                        # Калькулировать стоимость: GPT-4o-mini $0.00015 per 1K input tokens, $0.0006 per 1K output tokens
                        input_tokens = data["usage"].get("prompt_tokens", 0)
                        output_tokens = data["usage"].get("completion_tokens", 0)
                        cost = (input_tokens / 1000) * 0.00015 + (output_tokens / 1000) * 0.0006
                        self.total_cost_usd += cost
                        self.total_requests += 1
                        
                        logger.debug(
                            f"LLM API call completed",
                            extra={
                                "elapsed_ms": int(elapsed * 1000),
                                "tokens": tokens_used,
                                "cost_usd": cost,
                            }
                        )
                    
                    return response_text
                else:
                    raise ValueError("Unexpected response format from LLM API")
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling ProxyAPI: {e}")
            raise
        except Exception as e:
            logger.error(f"Error calling ProxyAPI: {e}")
            raise
    
    # ========================================================================
    # УТИЛИТЫ
    # ========================================================================
    
    def _normalize_text(self, text: str) -> str:
        """
        Нормализовать текст перед отправкой в LLM.
        Убирает проблемные символы и исправляет кодировку.
        
        Args:
            text: Исходный текст
        
        Returns:
            Нормализованный текст
        """
        if not text:
            return ""
        
        try:
            # Убедиться что текст в UTF-8
            if isinstance(text, bytes):
                # Попробовать декодировать как UTF-8
                try:
                    text = text.decode('utf-8')
                except UnicodeDecodeError:
                    # Если не получается, попробовать другие кодировки
                    try:
                        text = text.decode('utf-16-le', errors='ignore')
                    except (UnicodeDecodeError, UnicodeError):
                        # В крайнем случае использовать errors='replace'
                        text = text.decode('utf-8', errors='replace')
            
            # Убрать нулевые байты и другие проблемные символы
            text = text.replace('\x00', '')
            text = text.replace('\ufffd', '')  # Replacement character
            
            # Нормализовать пробелы
            import re
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            return text
        
        except Exception as e:
            logger.warning(f"Error normalizing text: {e}, using original text")
            # В случае ошибки вернуть оригинальный текст, но попробовать исправить кодировку
            if isinstance(text, str):
                return text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
            return str(text) if text else ""
    
    def get_metrics(self) -> dict:
        """
        Получить текущие метрики использования LLM.
        
        Returns:
            Dict с tokens, cost, requests
        """
        settings = get_settings()
        return {
            "total_requests": self.total_requests,
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": self.total_cost_usd,
            "avg_tokens_per_request": (
                self.total_tokens_used / self.total_requests
                if self.total_requests > 0
                else 0
            ),
            "daily_budget_usd": settings.llm_daily_budget_usd,
            "budget_remaining_usd": max(0, settings.llm_daily_budget_usd - self.total_cost_usd),
            "budget_percentage_used": (
                (self.total_cost_usd / settings.llm_daily_budget_usd * 100)
                if settings.llm_daily_budget_usd > 0
                else 0
            ),
        }
    
    async def check_budget(self) -> bool:
        """
        Проверить остался ли бюджет на день.
        
        Returns:
            True если можно делать запросы, False если бюджет исчерпан
        """
        settings = get_settings()
        metrics = self.get_metrics()
        if metrics["budget_remaining_usd"] <= 0:
            logger.warning(f"Daily LLM budget exhausted! Cost: ${metrics['total_cost_usd']:.2f}")
            return False
        return True
    
    def reset_daily_metrics(self) -> None:
        """Сбросить суточные метрики (вызывать в 00:00)."""
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        self.total_requests = 0
        logger.info("Daily LLM metrics reset")


# Global instance
llm_classifier = LLMClassifier()

