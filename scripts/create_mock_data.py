#!/usr/bin/env python3
"""Создание мок-данных для тестирования системы."""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
import random

# Добавить корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger
from src.database.supabase_client import SupabaseClient
from src.config.settings import get_settings


async def create_mock_data():
    """Создать мок-данные в БД."""
    logger.info("=" * 70)
    logger.info("СОЗДАНИЕ МОК-ДАННЫХ В БД")
    logger.info("=" * 70)
    
    settings = get_settings()
    client = SupabaseClient()
    
    # Тестовые чаты
    test_chats = [
        {
            "chat_id": "-1001234567890",
            "chat_name": "Тестовый чат IT-заказов",
            "chat_type": "supergroup",
        },
        {
            "chat_id": "-1001234567891",
            "chat_name": "Фриланс разработка",
            "chat_type": "group",
        },
        {
            "chat_id": "-1001234567892",
            "chat_name": "AI и автоматизация",
            "chat_type": "supergroup",
        },
    ]
    
    # Тестовые сообщения и заказы
    test_orders = [
        {
            "message_id": "1001",
            "chat_id": "-1001234567890",
            "author_id": "123456789",
            "author_name": "test_user_1",
            "text": "Ищу Python разработчика для проекта. Нужен опыт работы с FastAPI и PostgreSQL. Бюджет обсуждается.",
            "category": "Backend",
            "relevance_score": 0.95,
            "detected_by": "regex",
            "telegram_link": "https://t.me/test_chat/1001",
        },
        {
            "message_id": "1002",
            "chat_id": "-1001234567890",
            "author_id": "123456790",
            "author_name": "test_user_2",
            "text": "Требуется AI инженер для создания чат-бота с ИИ. Нужна интеграция с OpenAI и автоматизация бизнес-процессов.",
            "category": "AI/ML",
            "relevance_score": 0.93,
            "detected_by": "regex",
            "telegram_link": "https://t.me/test_chat/1002",
        },
        {
            "message_id": "1003",
            "chat_id": "-1001234567891",
            "author_id": "123456791",
            "author_name": "test_user_3",
            "text": "Нужен Webflow разработчик для создания сайта. Проект на Webflow, нужен специалист с опытом.",
            "category": "Frontend",
            "relevance_score": 0.92,
            "detected_by": "regex",
            "telegram_link": "https://t.me/test_chat/1003",
        },
        {
            "message_id": "1004",
            "chat_id": "-1001234567891",
            "author_id": "123456792",
            "author_name": "test_user_4",
            "text": "Ищем Flutter разработчика для мобильного приложения. Нужен опыт работы с Flutter и Firebase.",
            "category": "Mobile",
            "relevance_score": 0.94,
            "detected_by": "regex",
            "telegram_link": "https://t.me/test_chat/1004",
        },
        {
            "message_id": "1005",
            "chat_id": "-1001234567892",
            "author_id": "123456793",
            "author_name": "test_user_5",
            "text": "Требуется Prompt Engineer для оптимизации промптов. Нужен специалист по промпт-инжинирингу для ChatGPT.",
            "category": "AI/ML",
            "relevance_score": 0.92,
            "detected_by": "regex",
            "telegram_link": "https://t.me/test_chat/1005",
        },
        {
            "message_id": "1006",
            "chat_id": "-1001234567892",
            "author_id": "123456794",
            "author_name": "test_user_6",
            "text": "Нужна автоматизация бизнес-процессов. Требуется специалист по автоматизации продаж и обработки заявок.",
            "category": "AI/ML",
            "relevance_score": 0.90,
            "detected_by": "regex",
            "telegram_link": "https://t.me/test_chat/1006",
        },
        {
            "message_id": "1007",
            "chat_id": "-1001234567890",
            "author_id": "123456795",
            "author_name": "test_user_7",
            "text": "Ищем разработчика на Bubble для создания MVP. Проект на Bubble, нужен специалист с опытом работы.",
            "category": "Low-Code",
            "relevance_score": 0.94,
            "detected_by": "regex",
            "telegram_link": "https://t.me/test_chat/1007",
        },
        {
            "message_id": "1008",
            "chat_id": "-1001234567891",
            "author_id": "123456796",
            "author_name": "test_user_8",
            "text": "Требуется Shopify разработчик для настройки магазина. Нужен специалист по Shopify с опытом работы.",
            "category": "Other",
            "relevance_score": 0.93,
            "detected_by": "regex",
            "telegram_link": "https://t.me/test_chat/1008",
        },
        {
            "message_id": "1009",
            "chat_id": "-1001234567892",
            "author_id": "123456797",
            "author_name": "test_user_9",
            "text": "Нужен специалист для создания AI-ассистента. Требуется разработка чат-бота с ИИ для автоматизации поддержки клиентов.",
            "category": "AI/ML",
            "relevance_score": 0.91,
            "detected_by": "llm",
            "telegram_link": "https://t.me/test_chat/1009",
        },
        {
            "message_id": "1010",
            "chat_id": "-1001234567890",
            "author_id": "123456798",
            "author_name": "test_user_10",
            "text": "Ищем Full-stack разработчика для проекта. Нужен опыт работы с Python, React и PostgreSQL.",
            "category": "Backend",
            "relevance_score": 0.88,
            "detected_by": "llm",
            "telegram_link": "https://t.me/test_chat/1010",
        },
    ]
    
    # Создать чаты
    logger.info("\n📝 Создание тестовых чатов...")
    created_chats = 0
    for chat_data in test_chats:
        try:
            # Проверить, существует ли чат
            response = await client.client.get(
                f"/chats?chat_id=eq.{chat_data['chat_id']}&select=chat_id"
            )
            existing_chats = response.json() if response.status_code == 200 else []
            
            if existing_chats:
                logger.debug(f"  ⚠️  Чат {chat_data['chat_name']} уже существует, пропускаем")
                continue
            
            # Создать чат
            response = await client.client.post(
                "/chats",
                json={
                    "chat_id": chat_data["chat_id"],
                    "chat_name": chat_data["chat_name"],
                    "chat_type": chat_data["chat_type"],
                    "is_active": True,
                }
            )
            
            if response.status_code in [200, 201]:
                created_chats += 1
                logger.info(f"  ✅ Создан чат: {chat_data['chat_name']}")
            else:
                logger.error(f"  ❌ Ошибка при создании чата {chat_data['chat_name']}: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"  ❌ Ошибка при создании чата {chat_data['chat_name']}: {e}")
    
    logger.info(f"\n✅ Создано чатов: {created_chats}/{len(test_chats)}")
    
    # Создать сообщения и заказы
    logger.info("\n📝 Создание тестовых сообщений и заказов...")
    created_messages = 0
    created_orders = 0
    
    # Генерировать разные даты для разнообразия
    base_date = datetime.now()
    
    for i, order_data in enumerate(test_orders):
        try:
            # Создать сообщение
            message_date = base_date - timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
            
            response = await client.client.post(
                "/messages",
                json={
                    "message_id": order_data["message_id"],
                    "chat_id": order_data["chat_id"],
                    "author_id": order_data["author_id"],
                    "author_name": order_data["author_name"],
                    "text": order_data["text"],
                    "timestamp": message_date.isoformat(),
                }
            )
            
            if response.status_code in [200, 201]:
                created_messages += 1
                logger.debug(f"  ✅ Создано сообщение: {order_data['message_id']}")
            elif response.status_code == 409:
                logger.debug(f"  ⚠️  Сообщение {order_data['message_id']} уже существует, пропускаем")
            else:
                logger.error(f"  ❌ Ошибка при создании сообщения {order_data['message_id']}: {response.status_code} - {response.text}")
            
            # Создать заказ через прямой вызов REST API
            order_date = message_date + timedelta(seconds=random.randint(1, 60))
            
            order_payload = {
                "message_id": order_data["message_id"],
                "chat_id": order_data["chat_id"],
                "author_id": order_data["author_id"],
                "author_name": order_data["author_name"],
                "text": order_data["text"],
                "category": order_data["category"],
                "relevance_score": order_data["relevance_score"],
                "detected_by": order_data["detected_by"],
                "telegram_link": order_data["telegram_link"],
                "created_at": order_date.isoformat(),
            }
            
            response = await client.client.post(
                "/userbot_orders",
                json=order_payload
            )
            
            result = response.status_code in [200, 201]
            
            if result:
                created_orders += 1
                logger.info(f"  ✅ Создан заказ: {order_data['category']} (message_id: {order_data['message_id']})")
            else:
                logger.debug(f"  ⚠️  Заказ {order_data['message_id']} уже существует или ошибка создания")
                
        except Exception as e:
            logger.error(f"  ❌ Ошибка при создании заказа {order_data.get('message_id', 'unknown')}: {e}", exc_info=True)
    
    logger.info(f"\n✅ Создано сообщений: {created_messages}/{len(test_orders)}")
    logger.info(f"✅ Создано заказов: {created_orders}/{len(test_orders)}")
    
    # Обновить статистику
    logger.info("\n📊 Обновление статистики...")
    try:
        response = await client.client.post(
            "/stats",
            json={
                "detected_orders": created_orders,
                "regex_detections": sum(1 for o in test_orders if o["detected_by"] == "regex"),
                "llm_detections": sum(1 for o in test_orders if o["detected_by"] == "llm"),
                "total_messages": created_messages,
            }
        )
        
        if response.status_code in [200, 201]:
            logger.info("  ✅ Статистика обновлена")
        else:
            logger.debug(f"  ⚠️  Статистика не обновлена: {response.status_code}")
    except Exception as e:
        logger.debug(f"  ⚠️  Ошибка при обновлении статистики: {e}")
    
    # Проверить результаты
    logger.info("\n" + "=" * 70)
    logger.info("ПРОВЕРКА СОЗДАННЫХ ДАННЫХ")
    logger.info("=" * 70)
    
    try:
        # Проверить чаты
        response = await client.client.get("/chats?select=chat_id,chat_name&limit=10")
        if response.status_code == 200:
            chats = response.json()
            logger.info(f"\n💬 Чатов в БД: {len(chats)}")
            for chat in chats[:5]:
                logger.info(f"  - {chat.get('chat_name', 'N/A')} ({chat.get('chat_id', 'N/A')})")
        
        # Проверить сообщения
        response = await client.client.get("/messages?select=message_id,chat_id&limit=10")
        if response.status_code == 200:
            messages = response.json()
            logger.info(f"\n📨 Сообщений в БД: {len(messages)}")
        
        # Проверить заказы
        orders = await client.get_orders()
        logger.info(f"\n📊 Заказов в БД: {len(orders)}")
        for order in orders[:5]:
            logger.info(f"  - {order.get('category', 'N/A')} | {order.get('text', '')[:50]}...")
            
    except Exception as e:
        logger.error(f"Ошибка при проверке данных: {e}", exc_info=True)
    
    await client.client.aclose()
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ СОЗДАНИЕ МОК-ДАННЫХ ЗАВЕРШЕНО")
    logger.info("=" * 70)
    logger.info("\n💡 Теперь вы можете проверить данные:")
    logger.info("   - python3 -m src.main stats dashboard --period today")
    logger.info("   - python3 -m src.main export csv --period week")
    logger.info("   - python3 -m src.main export html --period week")


if __name__ == "__main__":
    asyncio.run(create_mock_data())

