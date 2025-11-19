#!/usr/bin/env python3
"""Проверка состояния базы данных и системы."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from src.database.base import db_manager
from src.database.repository import ChatRepository, MessageRepository, OrderRepository
from src.config.chat_config import chat_config_manager
from sqlalchemy import select, func
from src.database.schemas import Chat, Message, Order

async def check_system():
    print("=" * 70)
    print("ПРОВЕРКА СОСТОЯНИЯ СИСТЕМЫ")
    print("=" * 70)
    
    # Инициализация БД
    await db_manager.initialize()
    
    chats_count = 0
    messages_count = 0
    orders_count = 0
    
    try:
        async for session in db_manager.get_session():
            try:
                # Проверка чатов в БД
                chats_count = await session.scalar(select(func.count()).select_from(Chat))
                messages_count = await session.scalar(select(func.count()).select_from(Message))
                orders_count = await session.scalar(select(func.count()).select_from(Order))
                
                print(f"\n📊 Данные в БД:")
                print(f"   Чаты: {chats_count}")
                print(f"   Сообщения: {messages_count}")
                print(f"   Заказы: {orders_count}")
                
            finally:
                break
    finally:
        await db_manager.close()
    
    # Проверка конфигурации чатов
    chat_config_manager.initialize()
    active_chats = chat_config_manager.get_active_chats()
    
    print(f"\n💬 Конфигурация чатов:")
    print(f"   Активных чатов в конфиге: {len(active_chats)}")
    
    if active_chats:
        print(f"\n   Список активных чатов:")
        for chat in active_chats[:5]:  # Показать первые 5
            print(f"   - {chat.chat_name} ({chat.chat_id}) [Priority: {chat.priority}]")
        if len(active_chats) > 5:
            print(f"   ... и еще {len(active_chats) - 5} чатов")
    else:
        print(f"   ⚠️  НЕТ АКТИВНЫХ ЧАТОВ В КОНФИГУРАЦИИ!")
    
    print("\n" + "=" * 70)
    print("РЕКОМЕНДАЦИИ:")
    print("=" * 70)
    
    if chats_count == 0:
        print("\n1. ❌ В БД нет чатов")
        print("   → Userbot создаст чаты автоматически при получении первого сообщения")
        print("   → Убедитесь, что userbot запущен: python3 -m src.main start")
    
    if messages_count == 0:
        print("\n2. ❌ В БД нет сообщений")
        print("   → Userbot должен обрабатывать сообщения из активных чатов")
        print("   → Проверьте логи userbot на наличие обработанных сообщений")
        print("   → Убедитесь, что userbot запущен и работает")
    
    if orders_count == 0:
        print("\n3. ❌ В БД нет заказов")
        print("   → Это нормально, если:")
        print("     - Userbot еще не обработал релевантные сообщения")
        print("     - В чатах нет сообщений с ключевыми словами")
        print("     - Сообщения не соответствуют паттернам детекции")
        print("   → Проверьте логи userbot: должны быть записи '📥 Received message'")
    
    if len(active_chats) == 0:
        print("\n4. ⚠️  КРИТИЧНО: Нет активных чатов для мониторинга!")
        print("   → Добавьте чаты: python3 -m src.main chat auto-detect")
        print("   → Или вручную: python3 -m src.main chat add <chat_id> --name \"Название\"")
    elif chats_count == 0 and len(active_chats) > 0:
        print("\n5. ⚠️  Есть активные чаты в конфиге, но их нет в БД")
        print("   → Это нормально - чаты создаются автоматически при первом сообщении")
        print("   → Убедитесь, что userbot запущен: python3 -m src.main start")
        print("   → Userbot должен получать сообщения из этих чатов")
    
    print("\n" + "=" * 70)
    print("СЛЕДУЮЩИЕ ШАГИ:")
    print("=" * 70)
    print("\n1. Проверьте, запущен ли userbot:")
    print("   → ps aux | grep 'src.main start'")
    print("   → Или запустите: python3 -m src.main start")
    
    print("\n2. Проверьте логи userbot:")
    print("   → Должны быть записи '📥 Received message from chat'")
    print("   → Должны быть записи '✓ Chat ... IS monitored, processing message'")
    
    print("\n3. Если userbot не получает сообщения:")
    print("   → Проверьте, что userbot добавлен в чаты")
    print("   → Проверьте, что чаты активны: python3 -m src.main chat list")
    
    print("\n4. Если сообщения получаются, но не сохраняются:")
    print("   → Проверьте подключение к БД: python3 -m src.main admin test-connection")
    print("   → Проверьте логи на наличие ошибок")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(check_system())

