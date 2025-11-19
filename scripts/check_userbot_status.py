#!/usr/bin/env python3
"""Проверка статуса userbot и диагностика проблем."""

import sys
import os
import subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.supabase_client import SupabaseClient
from src.config.settings import get_settings
from src.config.chat_config import chat_config_manager

def check_userbot_process():
    """Проверка, запущен ли userbot."""
    print("=" * 70)
    print("ПРОВЕРКА ПРОЦЕССА USERBOT")
    print("=" * 70)
    
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        
        userbot_processes = [
            line for line in result.stdout.split('\n')
            if 'src.main start' in line and 'grep' not in line
        ]
        
        if userbot_processes:
            print(f"\n✅ Userbot запущен ({len(userbot_processes)} процесс(ов))")
            for proc in userbot_processes[:3]:
                parts = proc.split()
                pid = parts[1]
                time = parts[9] if len(parts) > 9 else "N/A"
                print(f"   PID: {pid}, CPU Time: {time}")
        else:
            print("\n❌ Userbot НЕ запущен")
            print("   → Запустите: python3 -m src.main start")
        
        return len(userbot_processes) > 0
    except Exception as e:
        print(f"\n⚠️  Ошибка при проверке процесса: {e}")
        return False

async def check_database_async():
    """Проверка данных в БД (async)."""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("=" * 70)
    
    client = SupabaseClient()
    
    # Проверка чатов
    chats_count = 0
    try:
        response = await client.client.get("/chats?limit=10")
        if response.status_code == 200:
            chats = response.json() if hasattr(response, 'json') else []
            chats_count = len(chats) if isinstance(chats, list) else 0
            print(f"\n💬 Чатов в БД: {chats_count}")
        else:
            print(f"\n⚠️  Ошибка при получении чатов: HTTP {response.status_code}")
    except Exception as e:
        print(f"\n⚠️  Ошибка при получении чатов: {e}")
    
    # Проверка сообщений
    messages_count = 0
    try:
        response = await client.client.get("/messages?limit=10")
        if response.status_code == 200:
            messages = response.json() if hasattr(response, 'json') else []
            messages_count = len(messages) if isinstance(messages, list) else 0
            print(f"📨 Сообщений в БД: {messages_count}")
        else:
            print(f"⚠️  Ошибка при получении сообщений: HTTP {response.status_code}")
    except Exception as e:
        print(f"⚠️  Ошибка при получении сообщений: {e}")
    
    # Проверка заказов
    orders_count = 0
    try:
        orders = await client.get_orders()
        orders_count = len(orders) if orders else 0
        print(f"📊 Заказов в БД: {orders_count}")
    except Exception as e:
        print(f"⚠️  Ошибка при получении заказов: {e}")
    
    await client.client.aclose()
    return chats_count, messages_count, orders_count

def check_database():
    """Проверка данных в БД (синхронная обертка)."""
    import asyncio
    return asyncio.run(check_database_async())

def check_chat_config():
    """Проверка конфигурации чатов."""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА КОНФИГУРАЦИИ ЧАТОВ")
    print("=" * 70)
    
    chat_config_manager.initialize()
    active_chats = chat_config_manager.get_active_chats()
    
    print(f"\n💬 Активных чатов в конфиге: {len(active_chats)}")
    
    if active_chats:
        print("\nСписок активных чатов:")
        for chat in active_chats[:5]:
            print(f"  - {chat.chat_name} ({chat.chat_id}) [Priority: {chat.priority}]")
        if len(active_chats) > 5:
            print(f"  ... и еще {len(active_chats) - 5} чатов")
    else:
        print("\n⚠️  НЕТ АКТИВНЫХ ЧАТОВ!")
    
    return len(active_chats)

def main():
    """Основная функция диагностики."""
    print("\n" + "=" * 70)
    print("ДИАГНОСТИКА USERBOT")
    print("=" * 70)
    
    # Проверка процесса
    is_running = check_userbot_process()
    
    # Проверка БД
    chats_count, messages_count, orders_count = check_database()
    
    # Проверка конфигурации
    active_chats_count = check_chat_config()
    
    # Итоговый анализ
    print("\n" + "=" * 70)
    print("ИТОГОВЫЙ АНАЛИЗ")
    print("=" * 70)
    
    if not is_running:
        print("\n❌ КРИТИЧНО: Userbot не запущен")
        print("   → Запустите: python3 -m src.main start")
        return
    
    if active_chats_count == 0:
        print("\n❌ КРИТИЧНО: Нет активных чатов в конфигурации")
        print("   → Добавьте чаты: python3 -m src.main chat auto-detect")
        return
    
    if chats_count == 0 and messages_count == 0:
        print("\n⚠️  ПРОБЛЕМА: Userbot запущен, но не получает сообщения")
        print("\nВозможные причины:")
        print("1. Userbot не добавлен в чаты как участник")
        print("2. В чатах нет новых сообщений после запуска userbot")
        print("3. Userbot не может подключиться к Telegram API")
        print("\nРекомендации:")
        print("- Проверьте логи userbot (должны быть записи '📥 Received message')")
        print("- Убедитесь, что userbot добавлен в чаты")
        print("- Проверьте подключение к интернету")
        print("- Проверьте Telegram API credentials в .env")
        return
    
    if messages_count > 0 and orders_count == 0:
        print("\n⚠️  Сообщения обрабатываются, но заказы не обнаружены")
        print("\nЭто нормально, если:")
        print("- В сообщениях нет ключевых слов для детекции")
        print("- Сообщения слишком короткие или не соответствуют паттернам")
        print("\nПроверьте логи userbot на наличие:")
        print("- '✓ Order detected' - заказы обнаружены")
        print("- '⚠️ Skipping message' - сообщения пропускаются")
        return
    
    if orders_count > 0:
        print("\n✅ ВСЕ РАБОТАЕТ КОРРЕКТНО!")
        print(f"   - Чатов: {chats_count}")
        print(f"   - Сообщений: {messages_count}")
        print(f"   - Заказов: {orders_count}")
        return
    
    print("\n✅ Система работает, данные собираются...")
    print(f"   - Чатов: {chats_count}")
    print(f"   - Сообщений: {messages_count}")
    print(f"   - Заказов: {orders_count}")

if __name__ == "__main__":
    main()

