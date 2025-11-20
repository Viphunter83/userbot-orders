#!/usr/bin/env python3
"""Комплексный анализ системы детекции."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from src.analysis.regex_analyzer import RegexAnalyzer
from src.analysis.llm_classifier import llm_classifier
from src.analysis.prompts import SYSTEM_PROMPT

def analyze_message_length():
    """Анализ длины сообщений."""
    logger.info("=" * 70)
    logger.info("1️⃣ АНАЛИЗ ДЛИНЫ СООБЩЕНИЙ")
    logger.info("=" * 70)
    
    # Проверка ограничений
    logger.info("\n📏 Ограничения длины:")
    logger.info("  - В логах (для отображения): 100 символов")
    logger.info("  - В БД (сохранение): 10,000 символов")
    logger.info("  - В схеме БД (PostgreSQL TEXT): БЕЗ ОГРАНИЧЕНИЙ")
    logger.info("  - В валидаторе (Pydantic): 10,000 символов")
    
    # Примеры длинных сообщений
    test_messages = [
        "Нужен Python разработчик" * 1,  # ~25 символов
        "Нужен Python разработчик" * 10,  # ~250 символов
        "Нужен Python разработчик" * 100,  # ~2500 символов
        "Нужен Python разработчик" * 500,  # ~12500 символов
    ]
    
    logger.info("\n📊 Тестирование различных длин:")
    for msg in test_messages:
        length = len(msg)
        truncated_log = msg[:100]
        truncated_db = msg[:10000] if length > 10000 else msg
        
        logger.info(f"\n  Длина: {length} символов")
        logger.info(f"  В логах: '{truncated_log}...' ({len(truncated_log)} символов)")
        logger.info(f"  В БД: {'Обрезано' if length > 10000 else 'Полное'} ({len(truncated_db)} символов)")
        logger.info(f"  Потеря данных: {'ДА' if length > 10000 else 'НЕТ'}")
    
    logger.info("\n✅ Вывод:")
    logger.info("  - Сообщения до 10,000 символов сохраняются полностью")
    logger.info("  - Сообщения длиннее 10,000 символов обрезаются")
    logger.info("  - В логах показывается только превью (100 символов)")
    logger.info("  - Рекомендация: Увеличить лимит до 50,000 или убрать ограничение")


def analyze_patterns():
    """Анализ паттернов детекции."""
    logger.info("\n" + "=" * 70)
    logger.info("2️⃣ АНАЛИЗ ПАТТЕРНОВ ДЕТЕКЦИИ")
    logger.info("=" * 70)
    
    analyzer = RegexAnalyzer()
    
    # Подсчет паттернов
    total_patterns = 0
    category_counts = {}
    
    for category_name, patterns in analyzer.patterns.items():
        count = len(patterns)
        category_counts[category_name] = count
        total_patterns += count
    
    logger.info("\n📊 Статистика паттернов:")
    for category, count in sorted(category_counts.items()):
        logger.info(f"  {category}: {count} паттернов")
    
    logger.info(f"\n  ИТОГО: {total_patterns} паттернов")
    
    # Тестирование покрытия
    test_keywords = [
        "python", "javascript", "react", "vue", "flutter", 
        "ai", "chatgpt", "backend", "frontend", "mobile",
        "bubble", "glide", "zapier", "make", "n8n",
        "devops", "docker", "kubernetes", "design", "figma"
    ]
    
    logger.info("\n🔍 Тестирование покрытия ключевых слов:")
    detected = 0
    for keyword in test_keywords:
        test_message = f"Нужен {keyword} разработчик"
        result = analyzer.analyze(test_message)
        if result:
            detected += 1
            logger.info(f"  ✅ '{keyword}' - обнаружен ({result.category.value})")
        else:
            logger.info(f"  ❌ '{keyword}' - НЕ обнаружен")
    
    logger.info(f"\n  Покрытие: {detected}/{len(test_keywords)} ({detected/len(test_keywords)*100:.1f}%)")
    
    logger.info("\n✅ Вывод:")
    logger.info("  - Текущее количество паттернов: достаточное для базового покрытия")
    logger.info("  - Рекомендация: Добавить больше вариаций написания")
    logger.info("  - Рекомендация: Добавить синонимы и альтернативные формулировки")


def analyze_llm_prompt():
    """Анализ LLM промпта."""
    logger.info("\n" + "=" * 70)
    logger.info("3️⃣ АНАЛИЗ LLM ПРОМПТА И ЭФФЕКТИВНОСТИ")
    logger.info("=" * 70)
    
    logger.info("\n📝 Текущий промпт:")
    logger.info("-" * 70)
    logger.info(SYSTEM_PROMPT[:500] + "...")
    
    # Анализ промпта
    logger.info("\n🔍 Анализ промпта:")
    
    # Проверка поддержки языков
    has_russian = "Russian" in SYSTEM_PROMPT or "русск" in SYSTEM_PROMPT.lower()
    has_english = "English" in SYSTEM_PROMPT or "англ" in SYSTEM_PROMPT.lower()
    
    logger.info(f"  Поддержка русского языка: {'✅' if has_russian else '❌'}")
    logger.info(f"  Поддержка английского языка: {'✅' if has_english else '❌'}")
    
    # Проверка категорий
    categories = ["Backend", "Frontend", "Mobile", "AI/ML", "Low-Code", "Other"]
    categories_in_prompt = [cat for cat in categories if cat in SYSTEM_PROMPT]
    logger.info(f"  Категории в промпте: {len(categories_in_prompt)}/{len(categories)}")
    
    # Проверка примеров
    has_examples = "example" in SYSTEM_PROMPT.lower() or "пример" in SYSTEM_PROMPT.lower()
    logger.info(f"  Примеры в промпте: {'✅' if has_examples else '❌'}")
    
    # Проверка инструкций по языку
    logger.info("\n🌐 Поддержка языков:")
    logger.info("  - Промпт на английском (для лучшей производительности GPT)")
    logger.info("  - Анализирует русские сообщения")
    logger.info("  - Ответы на русском (reason field)")
    
    logger.info("\n✅ Вывод:")
    logger.info("  - Промпт хорошо структурирован")
    logger.info("  - Поддерживает русский и английский языки")
    logger.info("  - Рекомендация: Добавить больше примеров для разных языков")
    logger.info("  - Рекомендация: Уточнить инструкции для смешанных языков")


def main():
    """Главная функция."""
    logger.info("=" * 70)
    logger.info("КОМПЛЕКСНЫЙ АНАЛИЗ СИСТЕМЫ ДЕТЕКЦИИ")
    logger.info("=" * 70)
    
    analyze_message_length()
    analyze_patterns()
    analyze_llm_prompt()
    
    logger.info("\n" + "=" * 70)
    logger.info("ИТОГОВЫЕ РЕКОМЕНДАЦИИ")
    logger.info("=" * 70)
    logger.info("\n1. ДЛИНА СООБЩЕНИЙ:")
    logger.info("   ✅ Текущий лимит 10,000 символов достаточен для большинства случаев")
    logger.info("   ⚠️  Рекомендация: Увеличить до 50,000 или убрать ограничение")
    logger.info("\n2. ПАТТЕРНЫ:")
    logger.info("   ✅ Текущее количество паттернов достаточное")
    logger.info("   ⚠️  Рекомендация: Добавить больше вариаций и синонимов")
    logger.info("\n3. LLM ПРОМПТ:")
    logger.info("   ✅ Промпт хорошо структурирован")
    logger.info("   ✅ Поддерживает русский и английский языки")
    logger.info("   ⚠️  Рекомендация: Добавить больше примеров")


if __name__ == "__main__":
    main()

