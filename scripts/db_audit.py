#!/usr/bin/env python3
"""Professional Database Audit Script."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.base import db_manager
from src.database.repository import OrderRepository, ChatRepository, MessageRepository, StatRepository
from datetime import datetime, timedelta
from sqlalchemy import text
from rich.console import Console
from rich.table import Table

console = Console()


async def audit_database():
    """Провести полный аудит базы данных."""
    console.print("\n[bold cyan]" + "=" * 70)
    console.print("[bold cyan]🔍 PROFESSIONAL DATABASE AUDIT[/]")
    console.print("[bold cyan]" + "=" * 70 + "[/]\n")
    
    try:
        # Инициализация БД
        await db_manager.initialize()
        if not db_manager.is_initialized():
            console.print("[red]❌ Database not initialized![/]")
            console.print("[yellow]Check your .env file and database connection settings.[/]")
            return False
        
        console.print("[green]✓ Database connection: OK[/]\n")
        
        # Используем async generator правильно - через async for
        async for session in db_manager.get_session():
            try:
                # 1. Проверка структуры таблиц
                console.print("[bold cyan]📊 Checking table structure...[/]")
                tables_query = text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('chats', 'messages', 'userbot_orders', 'stats', 'chat_stats', 'feedback')
                    ORDER BY table_name
                """)
                result = await session.execute(tables_query)
                tables = [row[0] for row in result]
                
                table = Table(title="Database Tables", show_header=True)
                table.add_column("Table Name", style="cyan")
                table.add_column("Status", style="green")
                
                expected_tables = ['chats', 'messages', 'userbot_orders', 'stats', 'chat_stats', 'feedback']
                for expected in expected_tables:
                    status = "✓ Exists" if expected in tables else "✗ Missing"
                    table.add_row(expected, status)
                
                console.print(table)
                console.print()
                
                # 2. Проверка данных в таблицах
                console.print("[bold cyan]📈 Checking data counts...[/]")
                data_table = Table(title="Data Counts", show_header=True)
                data_table.add_column("Table", style="cyan")
                data_table.add_column("Records", style="green")
                data_table.add_column("Status", style="yellow")
                
                for table_name in tables:
                    try:
                        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
                        count_result = await session.execute(count_query)
                        count = count_result.scalar()
                        status = "✓ Has data" if count > 0 else "⚠️ Empty"
                        data_table.add_row(table_name, str(count), status)
                    except Exception as e:
                        data_table.add_row(table_name, "Error", f"✗ {str(e)[:30]}")
                
                console.print(data_table)
                console.print()
                
                # 3. Детальная проверка заказов
                console.print("[bold cyan]📦 Detailed Orders Analysis...[/]")
                order_repo = OrderRepository(session)
                
                # Все заказы
                all_orders = await order_repo.get_recent(days=365, limit=1000)
                console.print(f"   Total orders (last 365 days): [green]{len(all_orders)}[/]")
                
                if all_orders:
                    latest = all_orders[0]
                    oldest = all_orders[-1]
                    console.print(f"   Latest order: [cyan]{latest.created_at}[/] (ID: {latest.id})")
                    console.print(f"   Oldest in result: [cyan]{oldest.created_at}[/]")
                    
                    # По категориям
                    categories = {}
                    for order in all_orders:
                        categories[order.category] = categories.get(order.category, 0) + 1
                    
                    if categories:
                        cat_table = Table(title="Orders by Category", show_header=True)
                        cat_table.add_column("Category", style="cyan")
                        cat_table.add_column("Count", style="green")
                        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                            cat_table.add_row(cat, str(count))
                        console.print(cat_table)
                
                # Заказы за сегодня
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                today_orders_raw = await order_repo.get_recent(days=2, limit=1000)
                today_orders = [o for o in today_orders_raw if o.created_at >= today_start]
                console.print(f"\n   Orders today (since {today_start.strftime('%Y-%m-%d %H:%M')}): [green]{len(today_orders)}[/]")
                
                # 4. Проверка чатов
                console.print("\n[bold cyan]💬 Checking chats...[/]")
                chat_repo = ChatRepository(session)
                active_chats = await chat_repo.get_all_active()
                console.print(f"   Active chats: [green]{len(active_chats)}[/]")
                
                if active_chats:
                    chat_table = Table(title="Active Chats", show_header=True)
                    chat_table.add_column("Chat ID", style="cyan")
                    chat_table.add_column("Name", style="green")
                    chat_table.add_column("Type", style="yellow")
                    chat_table.add_column("Last Message", style="dim")
                    
                    for chat in active_chats[:10]:  # Показать первые 10
                        last_msg = chat.last_message_at.strftime("%Y-%m-%d %H:%M") if chat.last_message_at else "Never"
                        chat_table.add_row(
                            chat.chat_id,
                            chat.chat_name[:30],
                            chat.chat_type,
                            last_msg
                        )
                    console.print(chat_table)
                
                # 5. Проверка сообщений
                console.print("\n[bold cyan]📨 Checking messages...[/]")
                msg_repo = MessageRepository(session)
                recent_msgs = await msg_repo.get_unprocessed(limit=10)
                console.print(f"   Unprocessed messages (sample): [yellow]{len(recent_msgs)}[/]")
                
                # 6. Проверка статистики
                console.print("\n[bold cyan]📊 Checking stats...[/]")
                stat_repo = StatRepository(session)
                today_stat = await stat_repo.get_or_create_today()
                
                stat_table = Table(title="Today's Statistics", show_header=True)
                stat_table.add_column("Metric", style="cyan")
                stat_table.add_column("Value", style="green")
                
                stat_table.add_row("Date", today_stat.date)
                stat_table.add_row("Total Messages", str(today_stat.total_messages))
                stat_table.add_row("Detected Orders", str(today_stat.detected_orders))
                stat_table.add_row("Regex Detections", str(today_stat.regex_detections))
                stat_table.add_row("LLM Detections", str(today_stat.llm_detections))
                stat_table.add_row("LLM Tokens Used", str(today_stat.llm_tokens_used))
                stat_table.add_row("LLM Cost (USD)", f"${today_stat.llm_cost:.4f}")
                
                console.print(stat_table)
                
                # 7. Проверка индексов
                console.print("\n[bold cyan]🔍 Checking indexes...[/]")
                indexes_query = text("""
                    SELECT tablename, indexname 
                    FROM pg_indexes 
                    WHERE schemaname = 'public'
                    AND tablename IN ('chats', 'messages', 'userbot_orders', 'stats', 'chat_stats', 'feedback')
                    ORDER BY tablename, indexname
                """)
                indexes_result = await session.execute(indexes_query)
                indexes = list(indexes_result)
                
                if indexes:
                    idx_table = Table(title="Database Indexes", show_header=True)
                    idx_table.add_column("Table", style="cyan")
                    idx_table.add_column("Index", style="green")
                    for table_name, index_name in indexes:
                        idx_table.add_row(table_name, index_name)
                    console.print(idx_table)
                
                # Итоговый отчет
                console.print("\n[bold green]" + "=" * 70)
                console.print("[bold green]✓ Audit completed successfully[/]")
                console.print("[bold green]" + "=" * 70 + "[/]\n")
                
                return True
            except Exception as e:
                console.print(f"\n[red]❌ Error in session: {e}[/]")
                import traceback
                console.print(f"[dim]{traceback.format_exc()}[/]")
                return False
            finally:
                # Важно: break здесь завершает async for и закрывает сессию
                break
        
        await db_manager.close()
        
    except Exception as e:
        console.print(f"\n[red]❌ Error during audit: {e}[/]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/]")
        return False


if __name__ == "__main__":
    success = asyncio.run(audit_database())
    sys.exit(0 if success else 1)
