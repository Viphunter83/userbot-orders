#!/usr/bin/env python3
"""Проверка соответствия структуры БД в Supabase проекту."""

import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from src.database.supabase_client import SupabaseClient

async def check_schema():
    """Проверить схему БД в Supabase."""
    logger.info("=" * 70)
    logger.info("ПРОВЕРКА СХЕМЫ БД В SUPABASE")
    logger.info("=" * 70)
    
    client = SupabaseClient()
    
    tables_to_check = [
        "chats",
        "messages", 
        "userbot_orders",
        "stats",
        "chat_stats",
        "feedback"
    ]
    
    for table_name in tables_to_check:
        logger.info(f"\n📊 Таблица: {table_name}")
        logger.info("-" * 70)
        
        try:
            # Попытка получить структуру через REST API
            # Supabase REST API не предоставляет прямой доступ к схеме,
            # но мы можем попробовать сделать запрос и посмотреть на ошибки
            
            # Попробуем получить одну запись для проверки структуры
            response = await client.client.get(f"/{table_name}?limit=1")
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    logger.info(f"✅ Таблица существует и доступна")
                    logger.info(f"   Пример структуры записи:")
                    for key, value in data[0].items():
                        value_preview = str(value)[:50] if value else "None"
                        logger.info(f"     - {key}: {type(value).__name__} = {value_preview}")
                else:
                    logger.info(f"✅ Таблица существует, но пуста")
            elif response.status_code == 404:
                logger.error(f"❌ Таблица {table_name} НЕ НАЙДЕНА в Supabase!")
            else:
                logger.warning(f"⚠️  Неожиданный статус: {response.status_code}")
                logger.info(f"   Ответ: {response.text[:200]}")
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке таблицы {table_name}: {e}")
    
    # Проверка конкретных полей в userbot_orders
    logger.info(f"\n🔍 ДЕТАЛЬНАЯ ПРОВЕРКА: userbot_orders")
    logger.info("-" * 70)
    
    try:
        # Попробуем вставить тестовую запись (которая будет удалена)
        # или получить существующую
        response = await client.client.get("/userbot_orders?limit=1")
        
        if response.status_code == 200:
            orders = response.json()
            if orders:
                order = orders[0]
                logger.info("✅ Структура записи из БД:")
                expected_fields = [
                    "id", "message_id", "chat_id", "author_id", "author_name",
                    "text", "category", "relevance_score", "detected_by",
                    "telegram_link", "created_at", "exported", "feedback", "notes"
                ]
                
                for field in expected_fields:
                    if field in order:
                        logger.info(f"   ✅ {field}: присутствует")
                    else:
                        logger.warning(f"   ❌ {field}: ОТСУТСТВУЕТ!")
                
                # Проверить лишние поля
                extra_fields = set(order.keys()) - set(expected_fields)
                if extra_fields:
                    logger.info(f"\n   Дополнительные поля в БД: {extra_fields}")
        else:
            logger.warning(f"⚠️  Не удалось получить данные: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    await client.client.aclose()
    
    logger.info("\n" + "=" * 70)
    logger.info("РЕКОМЕНДАЦИИ:")
    logger.info("=" * 70)
    logger.info("1. Убедитесь, что миграция migration_gioxfhlmzewgtqspokrt.sql выполнена")
    logger.info("2. Проверьте, что все таблицы созданы в Supabase Dashboard")
    logger.info("3. Сравните структуру таблиц в Supabase с моделями в src/database/schemas.py")

if __name__ == "__main__":
    asyncio.run(check_schema())

