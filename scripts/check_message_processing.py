#!/usr/bin/env python3
"""Проверка обработки конкретного сообщения."""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from src.database.supabase_client import SupabaseClient
from src.config.settings import get_settings
from src.analysis.regex_analyzer import RegexAnalyzer

async def check_message_processing():
    """Проверить обработку сообщения."""
    logger.info("=" * 70)
    logger.info("ПРОВЕРКА ОБРАБОТКИ СООБЩЕНИЯ")
    logger.info("=" * 70)
    
    chat_id = "-1001748730883"
    message_text = "🔺Fplus / Junior backend-разработчик 💲Оплата от 80 тыс. рублей."
    
    # Проверка детекции
    logger.info("\n1️⃣ ПРОВЕРКА ДЕТЕКЦИИ")
    logger.info("-" * 70)
    
    analyzer = RegexAnalyzer()
    result = analyzer.analyze(message_text)
    
    if result:
        logger.info(f"✅ Regex обнаружил заказ:")
        logger.info(f"   Категория: {result.category.value}")
        logger.info(f"   Confidence: {result.confidence:.2f}")
        logger.info(f"   Pattern: {result.matched_pattern}")
        logger.info(f"   Matched text: '{result.matched_text}'")
        
        if result.confidence >= 0.80:
            logger.info(f"   → Confidence >= 0.80, заказ должен быть сохранен напрямую")
        else:
            logger.info(f"   → Confidence < 0.80, заказ должен быть отправлен в LLM")
    else:
        logger.info(f"❌ Regex не обнаружил заказ")
        logger.info(f"   → Сообщение должно быть отправлено в LLM (если длина > 20 символов)")
        logger.info(f"   Длина сообщения: {len(message_text)} символов")
    
    # Проверка БД
    logger.info("\n2️⃣ ПРОВЕРКА БД")
    logger.info("-" * 70)
    
    client = SupabaseClient()
    
    # Проверка чата
    try:
        response = await client.client.get(f"/chats?chat_id=eq.{chat_id}")
        if response.status_code == 200:
            chats = response.json()
            if chats:
                chat = chats[0]
                logger.info(f"✅ Чат найден в БД:")
                logger.info(f"   ID: {chat.get('id')}")
                logger.info(f"   Name: {chat.get('chat_name')}")
                logger.info(f"   Type: {chat.get('chat_type')}")
                logger.info(f"   Active: {chat.get('is_active')}")
                logger.info(f"   Created: {chat.get('created_at')}")
            else:
                logger.warning(f"⚠️  Чат НЕ найден в БД")
                logger.info(f"   → Чат должен быть создан автоматически при первом сообщении")
        else:
            logger.error(f"❌ Ошибка при получении чата: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    # Проверка сообщений
    try:
        response = await client.client.get(
            f"/messages?chat_id=eq.{chat_id}&order=created_at.desc&limit=5"
        )
        if response.status_code == 200:
            messages = response.json()
            logger.info(f"\n📨 Сообщений из этого чата в БД: {len(messages)}")
            
            if messages:
                logger.info(f"\n   Последние сообщения:")
                for msg in messages[:3]:
                    logger.info(f"   - ID: {msg.get('message_id')}")
                    logger.info(f"     Author: {msg.get('author_name', 'N/A')}")
                    logger.info(f"     Text: {msg.get('text', '')[:100]}...")
                    logger.info(f"     Created: {msg.get('created_at')}")
                    logger.info("")
            else:
                logger.warning(f"⚠️  Сообщений из этого чата НЕТ в БД")
        else:
            logger.error(f"❌ Ошибка при получении сообщений: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    # Проверка заказов
    try:
        orders = await client.get_orders()
        chat_orders = [o for o in orders if o.get('chat_id') == chat_id]
        
        logger.info(f"\n📊 Заказов из этого чата в БД: {len(chat_orders)}")
        
        if chat_orders:
            logger.info(f"\n   Последние заказы:")
            for order in chat_orders[:3]:
                logger.info(f"   - Order ID: {order.get('id')}")
                logger.info(f"     Message ID: {order.get('message_id')}")
                logger.info(f"     Category: {order.get('category')}")
                logger.info(f"     Detected by: {order.get('detected_by')}")
                logger.info(f"     Relevance: {order.get('relevance_score', 0):.2f}")
                logger.info(f"     Text: {order.get('text', '')[:100]}...")
                logger.info(f"     Created: {order.get('created_at')}")
                logger.info("")
        else:
            logger.warning(f"⚠️  Заказов из этого чата НЕТ в БД")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    # Итоговый вывод
    logger.info("\n" + "=" * 70)
    logger.info("ИТОГОВЫЙ ВЫВОД")
    logger.info("=" * 70)
    
    if result and result.confidence >= 0.80:
        logger.info("\n✅ Паттерн детекции работает корректно")
        logger.info("   Сообщение должно быть обнаружено и сохранено")
        
        if not chats or not messages:
            logger.warning("\n⚠️  ПРОБЛЕМА: Сообщение не сохранилось в БД")
            logger.info("\nВозможные причины:")
            logger.info("1. Userbot не был запущен в момент получения сообщения")
            logger.info("2. Ошибка при сохранении в БД (проверьте логи userbot)")
            logger.info("3. Сообщение было пропущено фильтрами")
            logger.info("\nРекомендации:")
            logger.info("- Проверьте логи userbot на наличие ошибок")
            logger.info("- Убедитесь, что userbot запущен и работает")
            logger.info("- Проверьте подключение к БД")
        else:
            logger.info("\n✅ Данные в БД найдены")
    else:
        logger.warning("\n⚠️  Паттерн детекции не работает для этого сообщения")
        logger.info("   Сообщение должно быть обработано LLM")
    
    await client.client.aclose()

if __name__ == "__main__":
    asyncio.run(check_message_processing())

