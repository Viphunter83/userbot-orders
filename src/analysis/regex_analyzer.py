"""Regex-based order detection (fast, zero-cost first level)."""

import re
from typing import Optional
from loguru import logger

from src.analysis.triggers import ALL_PATTERNS, EXCLUDE_PATTERNS
from src.models.enums import OrderCategory, DetectionMethod
from src.models.order import OrderDetectionResult


class RegexAnalyzer:
    """
    Быстрый анализатор заказов на основе регулярных выражений.
    Первый уровень фильтрации (zero-cost).
    """
    
    def __init__(self):
        """Инициализировать анализатор: скомпилировать все паттерны."""
        self.compiled_patterns: dict[str, dict[str, re.Pattern]] = {}
        self.compiled_exclude_patterns: list[re.Pattern] = []
        
        # Скомпилировать основные паттерны по категориям
        for category, patterns in ALL_PATTERNS.items():
            self.compiled_patterns[category] = {}
            for pattern_name, pattern_data in patterns.items():
                try:
                    compiled = re.compile(
                        pattern_data["pattern"],
                        re.IGNORECASE | re.MULTILINE | re.UNICODE
                    )
                    self.compiled_patterns[category][pattern_name] = compiled
                except re.error as e:
                    logger.error(f"Failed to compile regex for {category}/{pattern_name}: {e}")
        
        # Скомпилировать исключающие паттерны
        for exclude_pattern in EXCLUDE_PATTERNS:
            try:
                compiled = re.compile(exclude_pattern, re.IGNORECASE)
                self.compiled_exclude_patterns.append(compiled)
            except re.error as e:
                logger.error(f"Failed to compile exclude pattern: {e}")
        
        logger.info(f"RegexAnalyzer initialized with {len(self.compiled_patterns)} categories")
    
    def analyze(self, text: str) -> Optional[OrderDetectionResult]:
        """
        Анализировать текст сообщения на предмет заказов.
        
        Args:
            text: Текст сообщения
        
        Returns:
            OrderDetectionResult если найден заказ, иначе None
        """
        if not text or len(text.strip()) < 3:
            return None
        
        # Шаг 1: Проверить исключающие паттерны
        for exclude_pattern in self.compiled_exclude_patterns:
            if exclude_pattern.search(text):
                logger.debug(f"Message excluded by pattern: {text[:50]}...")
                return None
        
        # Шаг 2: Найти подходящую категорию
        best_match: Optional[OrderDetectionResult] = None
        best_confidence: float = 0.0
        
        for category, patterns in self.compiled_patterns.items():
            for pattern_name, compiled_pattern in patterns.items():
                match = compiled_pattern.search(text)
                if match:
                    # Получить confidence из triggers.py
                    confidence = ALL_PATTERNS[category][pattern_name]["confidence"]
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = OrderDetectionResult(
                            category=OrderCategory(category),
                            confidence=confidence,
                            detected_by=DetectionMethod.REGEX,
                            matched_pattern=pattern_name,
                            matched_text=match.group(0),
                        )
        
        if best_match and best_confidence >= 0.80:  # Порог для высокой уверенности
            logger.info(
                f"Order detected by regex: {best_match.category.value} "
                f"(confidence: {best_match.confidence:.2f}, pattern: {best_match.matched_pattern})"
            )
            return best_match
        
        return None

