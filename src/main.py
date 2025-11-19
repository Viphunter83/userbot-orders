"""Main entry point for userbot-orders system."""

import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path
from pyrogram.types import Message
from loguru import logger
import typer

from src.telegram.client import TelegramClient
from src.utils.logger import setup_logger
from src.config.settings import get_settings
from src.analysis.regex_analyzer import RegexAnalyzer
from src.database.base import db_manager
from src.database.repository import ChatRepository, MessageRepository, OrderRepository, StatRepository
from src.export.csv_exporter import CSVExporter
from src.export.html_exporter import HTMLExporter
from src.export.filters import ExportFilter, OrderFilter, create_filter_for_period
from src.stats.dashboard import Dashboard
from src.stats.reporter import MetricsReporter
from src.stats.metrics import MetricsCalculator

# Create Typer app
app = typer.Typer(
    help="🤖 Telegram Orders Bot — AI-powered order detection system",
    no_args_is_help=True,
)
export_app = typer.Typer(help="📤 Export commands")
stats_app = typer.Typer(help="📊 Stats and analytics commands")
admin_app = typer.Typer(help="⚙️  Admin commands")
chat_app = typer.Typer(help="💬 Chat management commands")
app.add_typer(export_app, name="export")
app.add_typer(stats_app, name="stats")
app.add_typer(admin_app, name="admin")
app.add_typer(chat_app, name="chat")


class UserbotApp:
    """Main application class for Telegram userbot."""
    
    def __init__(self):
        """Initialize userbot application."""
        settings = get_settings()
        setup_logger(log_level=settings.log_level)
        
        self.client: Optional[TelegramClient] = None
        self.shutdown_event = asyncio.Event()
        self.loop = None
        self.regex_analyzer = RegexAnalyzer()
        self.db_initialized = False
        
        logger.info("Userbot application initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        if self.loop:
            self.loop.call_soon_threadsafe(self.shutdown_event.set)
        else:
            self.shutdown_event.set()
    
    async def message_handler(self, message: Message) -> None:
        """
        Handle incoming Telegram messages.
        
        Args:
            message: Pyrogram Message object
        """
        try:
            # Extract message information
            message_text = message.text or message.caption or ""
            
            # Если сообщение пустое, пропустить (но логировать для отладки)
            if not message_text or len(message_text.strip()) < 1:
                author_info = "Unknown"
                is_bot = False
                if message.from_user:
                    author_info = f"{message.from_user.first_name} (@{message.from_user.username or 'no username'})"
                    is_bot = message.from_user.is_bot
                
                logger.debug(
                    f"⚠️  Skipping message without text from chat {message.chat.id} | "
                    f"Author: {author_info} {'[BOT]' if is_bot else '[USER]'} | "
                    f"Has media: {bool(message.media)} | "
                    f"Media type: {type(message.media).__name__ if message.media else 'None'}"
                )
                return
            
            author_id = message.from_user.id if message.from_user else None
            author_username = (
                message.from_user.username 
                if message.from_user and message.from_user.username 
                else (message.from_user.first_name if message.from_user else "unknown")
            )
            is_bot = message.from_user.is_bot if message.from_user else False
            
            chat_id = message.chat.id
            chat_title = message.chat.title or "Private Chat"
            message_date = message.date
            
            # Format time
            time_str = message_date.strftime("%Y-%m-%d %H:%M")
            
            # Log message with more details
            logger.info(
                f"New Telegram message: '{message_text[:100]}...' | "
                f"Author: {author_username} ({author_id}) {'[BOT]' if is_bot else '[USER]'} | "
                f"Chat: {chat_title} ({chat_id}) | "
                f"Time: {time_str}"
            )
            
            # Save message to database if DB is initialized
            if self.db_initialized:
                try:
                    # Use async generator properly
                    async for session in db_manager.get_session():
                        try:
                            chat_repo = ChatRepository(session)
                            message_repo = MessageRepository(session)
                            
                            # Ensure chat exists
                            chat = await chat_repo.get_by_id(str(chat_id))
                            if not chat:
                                # Determine chat type
                                chat_type = "channel"  # Default
                                if hasattr(message.chat, 'type'):
                                    chat_type_str = str(message.chat.type)
                                    if chat_type_str == "group":
                                        chat_type = "group"
                                    elif chat_type_str == "supergroup":
                                        chat_type = "supergroup"
                                    elif chat_type_str == "channel":
                                        chat_type = "channel"
                                    else:
                                        # Fallback: try to get from chat config
                                        from src.config.chat_config import chat_config_manager
                                        chat_config = chat_config_manager.get_chat_config(str(chat_id))
                                        if chat_config:
                                            chat_type = chat_config.chat_type
                                        else:
                                            logger.warning(f"Unknown chat type: {chat_type_str}, defaulting to 'group'")
                                            chat_type = "group"
                                
                                chat = await chat_repo.create(
                                    chat_id=str(chat_id),
                                    chat_name=chat_title[:255],  # Limit length
                                    chat_type=chat_type
                                )
                            
                            # Save message (метод create сам проверяет на дубликаты)
                            message_id_str = str(message.id)
                            saved_message = await message_repo.create(
                                message_id=message_id_str,
                                chat_id=str(chat_id),
                                author_id=str(author_id) if author_id else "unknown",
                                author_name=author_username[:255] if author_username else None,
                                text=message_text[:10000] if len(message_text) > 10000 else message_text,  # Limit text length
                                timestamp=message_date,
                            )
                            
                            if saved_message:
                                # Update chat's last message time только если сообщение было создано
                                await chat_repo.update_last_message_time(str(chat_id))
                                logger.debug(f"  Message saved to database: {message_id_str}")
                            else:
                                logger.debug(f"  Message already exists in database: {message_id_str}")
                        finally:
                            # Session will be auto-committed/closed by generator
                            break
                except Exception as e:
                    logger.error(f"Error saving message to database: {e}", exc_info=True)
            
            # Analyze message with regex analyzer (first level filter)
            logger.debug(f"  🔍 Analyzing message with regex analyzer (length: {len(message_text)} chars)")
            detection_result = self.regex_analyzer.analyze(message_text)
            
            if detection_result:
                logger.debug(
                    f"  📊 Regex analyzer result: category={detection_result.category.value}, "
                    f"confidence={detection_result.confidence:.2f}, "
                    f"pattern={detection_result.matched_pattern}"
                )
            else:
                logger.debug("  📊 Regex analyzer: No match found")
            
            # If regex found high-confidence match, use it directly
            if detection_result and detection_result.confidence >= 0.80:
                logger.info(
                    f"  ✓ Order detected (regex): {detection_result.category.value} "
                    f"(confidence: {detection_result.confidence:.2f}, "
                    f"pattern: {detection_result.matched_pattern})"
                )
                logger.debug(f"  Matched text: '{detection_result.matched_text}'")
                
                # Save order to database if DB is initialized
                if self.db_initialized:
                    try:
                        # Use async generator properly
                        async for session in db_manager.get_session():
                            try:
                                order_repo = OrderRepository(session)
                                stat_repo = StatRepository(session)
                                
                                # Build telegram link
                                telegram_link = None
                                try:
                                    if hasattr(message.chat, 'username') and message.chat.username:
                                        telegram_link = f"https://t.me/{message.chat.username}/{message.id}"
                                    elif message.chat.id < 0:
                                        # For private groups/channels, format: https://t.me/c/CHAT_ID/MESSAGE_ID
                                        chat_id_str = str(abs(message.chat.id))
                                        # Remove first 4 digits for public link format
                                        if len(chat_id_str) > 4:
                                            telegram_link = f"https://t.me/c/{chat_id_str[4:]}/{message.id}"
                                        else:
                                            telegram_link = f"https://t.me/c/{chat_id_str}/{message.id}"
                                except Exception as link_error:
                                    logger.debug(f"Could not build telegram link: {link_error}")
                                
                                # Save order (метод create сам проверяет на дубликаты)
                                saved_order = await order_repo.create(
                                    message_id=str(message.id),
                                    chat_id=str(chat_id),
                                    author_id=str(author_id) if author_id else "unknown",
                                    author_name=author_username[:255] if author_username else None,
                                    text=message_text[:10000] if len(message_text) > 10000 else message_text,
                                    category=detection_result.category.value,
                                    relevance_score=detection_result.confidence,
                                    detected_by=detection_result.detected_by.value,
                                    telegram_link=telegram_link[:500] if telegram_link else None,
                                )
                                
                                if saved_order:
                                    # Update statistics только если заказ был создан (не дубликат)
                                    await stat_repo.update_metrics(
                                        detected_orders=1,
                                        regex_detections=1,
                                    )
                                    logger.info(f"  ✓ Order saved to database")
                                else:
                                    logger.debug(f"  Order already exists for message_id: {message.id}, skipping duplicate")
                            finally:
                                # Session will be auto-committed/closed by generator
                                break
                    except Exception as e:
                        logger.error(f"Error saving order to database: {e}", exc_info=True)
            
            # Level 2: LLM analysis for ambiguous messages
            # Use LLM if regex didn't find anything OR found low-confidence match
            elif not detection_result or detection_result.confidence < 0.80:
                # Only analyze messages that are long enough and might be orders
                message_length = len(message_text.strip())
                logger.debug(f"  🔍 Considering LLM analysis: message_length={message_length}, threshold=20")
                
                if message_length > 20:  # Skip very short messages
                    try:
                        from src.analysis.llm_classifier import llm_classifier
                        
                        logger.info(
                            f"  → Sending to LLM for analysis "
                            f"(regex: {'no match' if not detection_result else f'low confidence ({detection_result.confidence:.2f})'})"
                        )
                        logger.debug(f"  📝 Message preview for LLM: {message_text[:200]}...")
                        llm_result = await llm_classifier.classify(message_text)
                        
                        if llm_result:
                            logger.debug(
                                f"  📊 LLM result: is_order={llm_result.is_order}, "
                                f"category={llm_result.category}, "
                                f"relevance_score={llm_result.relevance_score:.2f}, "
                                f"threshold={llm_classifier.threshold:.2f}"
                            )
                        else:
                            logger.debug("  📊 LLM result: None (no response or error)")
                        
                        if llm_result and llm_result.is_order and llm_result.relevance_score >= llm_classifier.threshold:
                            logger.info(
                                f"  ✓ Order detected (LLM): {llm_result.category} "
                                f"(confidence: {llm_result.relevance_score:.2f})"
                            )
                            logger.debug(f"  LLM reason: {llm_result.reason}")
                            
                            # Save order to database if DB is initialized
                            if self.db_initialized:
                                try:
                                    async for session in db_manager.get_session():
                                        try:
                                            order_repo = OrderRepository(session)
                                            stat_repo = StatRepository(session)
                                            
                                            # Build telegram link
                                            telegram_link = None
                                            try:
                                                if hasattr(message.chat, 'username') and message.chat.username:
                                                    telegram_link = f"https://t.me/{message.chat.username}/{message.id}"
                                                elif message.chat.id < 0:
                                                    chat_id_str = str(abs(message.chat.id))
                                                    if len(chat_id_str) > 4:
                                                        telegram_link = f"https://t.me/c/{chat_id_str[4:]}/{message.id}"
                                                    else:
                                                        telegram_link = f"https://t.me/c/{chat_id_str}/{message.id}"
                                            except Exception as link_error:
                                                logger.debug(f"Could not build telegram link: {link_error}")
                                            
                                            # Save order (метод create сам проверяет на дубликаты)
                                            saved_order = await order_repo.create(
                                                message_id=str(message.id),
                                                chat_id=str(chat_id),
                                                author_id=str(author_id) if author_id else "unknown",
                                                author_name=author_username[:255] if author_username else None,
                                                text=message_text[:10000] if len(message_text) > 10000 else message_text,
                                                category=llm_result.category,
                                                relevance_score=llm_result.relevance_score,
                                                detected_by="llm",
                                                telegram_link=telegram_link[:500] if telegram_link else None,
                                            )
                                            
                                            if saved_order:
                                                # Update statistics только если заказ был создан (не дубликат)
                                                await stat_repo.update_metrics(
                                                    detected_orders=1,
                                                    llm_detections=1,
                                                    llm_tokens_used=llm_result.tokens_used or 0,
                                                    llm_cost=llm_result.cost_usd or 0.0,
                                                )
                                                logger.info(f"  ✓ Order saved to database (LLM)")
                                            else:
                                                logger.debug(f"  Order already exists for message_id: {message.id}, skipping duplicate (LLM)")
                                        finally:
                                            break
                                except Exception as e:
                                    logger.error(f"Error saving LLM order to database: {e}", exc_info=True)
                        else:
                            logger.debug(f"  LLM analysis: not an order (confidence: {llm_result.relevance_score if llm_result else 'N/A'})")
                    except Exception as e:
                        logger.error(f"Error in LLM classification: {e}", exc_info=True)
                else:
                    logger.debug("  Message too short for LLM analysis")
            
            # Log additional metadata if available
            if message.forward_from_chat:
                logger.debug(
                    f"  Forwarded from: {message.forward_from_chat.title} "
                    f"({message.forward_from_chat.id})"
                )
            
            if message.media:
                logger.debug(f"  Media type: {message.media}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def start(self, monitor_all: bool = False) -> None:
        """Start the userbot application."""
        try:
            # Store loop for signal handler
            self.loop = asyncio.get_event_loop()
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            logger.info("=" * 60)
            logger.info("Starting Telegram Userbot for Order Monitoring")
            logger.info("=" * 60)
            
            # Initialize chat config if not monitoring all
            if not monitor_all:
                from src.config.chat_config import chat_config_manager
                chat_config_manager.initialize()
                active_chats = chat_config_manager.get_active_chats()
                
                if not active_chats:
                    logger.warning("⚠️  No chats configured for monitoring!")
                    logger.info("Run 'python -m src.main chat auto-detect' to add chats")
                    return
                
                logger.info(f"📊 Monitoring {len(active_chats)} chats:")
                for config in active_chats:
                    logger.info(f"  • {config.chat_name} (priority: {config.priority})")
            else:
                logger.warning("⚠️  Monitoring ALL chats (ignoring config)")
            
            # Initialize database connection
            try:
                await db_manager.initialize()
                if db_manager.is_initialized():
                    self.db_initialized = True
                    logger.info("✓ Database connection initialized")
                else:
                    logger.warning("Database not initialized (using REST API mode)")
            except Exception as e:
                logger.warning(f"Database initialization failed: {e}. Continuing without DB...")
                self.db_initialized = False
            
            # Initialize Telegram client
            self.client = TelegramClient(session_name="userbot_orders")
            
            # Start client
            await self.client.start()
            
            logger.info("Userbot is running. Press Ctrl+C to stop.")
            logger.info("-" * 60)
            
            # Start listening for messages
            # This will block until interrupted
            # Run listen_messages in background and wait for shutdown event
            listen_task = asyncio.create_task(
                self.client.listen_messages(self.message_handler, filter_chats=not monitor_all)
            )
            
            # Wait for shutdown signal
            await self.shutdown_event.wait()
            
            # Cancel the listen task
            listen_task.cancel()
            try:
                await listen_task
            except asyncio.CancelledError:
                pass
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Error in userbot: {e}", exc_info=True)
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Shutdown the userbot application gracefully."""
        logger.info("Shutting down userbot...")
        
        if self.client:
            try:
                await self.client.stop()
            except Exception as e:
                logger.error(f"Error stopping client: {e}")
        
        # Close database connections
        if self.db_initialized:
            try:
                await db_manager.close()
                logger.info("✓ Database connections closed")
            except Exception as e:
                logger.error(f"Error closing database: {e}")
        
        # Вывести финальные метрики LLM и остановить cleanup task
        try:
            from src.analysis.llm_classifier import llm_classifier
            # Остановить cleanup task если запущена
            if hasattr(llm_classifier, 'stop_cleanup_task'):
                llm_classifier.stop_cleanup_task()
            if hasattr(llm_classifier, 'get_metrics'):
                metrics = llm_classifier.get_metrics()
                logger.info(
                    f"LLM Stats: {metrics.get('total_requests', 0)} requests, "
                    f"{metrics.get('total_tokens_used', 0)} tokens, "
                    f"${metrics.get('total_cost_usd', 0.0):.2f} cost"
                )
        except Exception as e:
            logger.debug(f"Could not get LLM metrics: {e}")
        
        logger.info("✓ Userbot stopped")


@export_app.command()
def csv(
    period: str = typer.Option("today", help="Period: today, week, month, all"),
    category: str = typer.Option("", help="Filter by category (Backend, Frontend, ...)"),
    output_dir: str = typer.Option("./exports", help="Output directory"),
):
    """Экспортировать заказы в CSV."""
    async def _export():
        from datetime import timedelta
        from src.database.schemas import Order
        
        await db_manager.initialize()
        orders = []
        
        # Попытка использовать прямое подключение к БД
        if db_manager.is_initialized():
            try:
                async for session in db_manager.get_session():
                    try:
                        repo = OrderRepository(session)
                        
                        # Получить заказы в зависимости от периода
                        if period == "today":
                            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                            orders_raw = await repo.get_recent(days=2, limit=1000)
                            orders = [o for o in orders_raw if o.created_at >= today_start]
                        elif period == "week":
                            orders = await repo.get_recent(days=7)
                        elif period == "month":
                            orders = await repo.get_recent(days=30)
                        else:
                            orders = await repo.get_recent(days=365)
                    finally:
                        break
            except Exception as db_error:
                logger.warning(f"Direct DB connection failed: {db_error}, falling back to REST API")
                orders = []
        
        # Fallback на REST API если прямое подключение не работает или нет данных
        if not orders:
            try:
                from src.database.supabase_client import get_supabase_client
                client = await get_supabase_client()
                
                try:
                    # Определить диапазон дат
                    end_date = datetime.utcnow()
                    if period == "today":
                        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    elif period == "week":
                        start_date = end_date - timedelta(days=7)
                    elif period == "month":
                        start_date = end_date - timedelta(days=30)
                    else:
                        start_date = datetime(2000, 1, 1)
                    
                    # Получить заказы через REST API
                    orders_data = await client.get_orders(
                        limit=1000,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    # Конвертировать в объекты Order
                    orders = []
                    for order_data in orders_data:
                        try:
                            order = Order(
                                id=order_data.get('id'),
                                message_id=str(order_data.get('message_id', '')),
                                chat_id=str(order_data.get('chat_id', '')),
                                author_id=str(order_data.get('author_id', '')),
                                author_name=order_data.get('author_name'),
                                text=order_data.get('text', ''),
                                category=order_data.get('category', 'Other'),
                                relevance_score=float(order_data.get('relevance_score', 0.0)),
                                detected_by=order_data.get('detected_by', 'manual'),
                                telegram_link=order_data.get('telegram_link'),
                                created_at=datetime.fromisoformat(order_data['created_at'].replace('Z', '+00:00')) if order_data.get('created_at') else datetime.utcnow(),
                                exported=order_data.get('exported', False),
                            )
                            orders.append(order)
                        except Exception as conv_error:
                            logger.debug(f"Error converting order data: {conv_error}")
                            continue
                    
                    logger.info(f"Retrieved {len(orders)} orders via REST API (period: {period})")
                finally:
                    await client.close()
            except Exception as rest_error:
                logger.error(f"REST API fallback failed: {rest_error}")
                logger.info("No database connection available. Please check your configuration.")
        
        # Применить фильтры
        if orders:
            filter_params = create_filter_for_period(period)
            if category:
                filter_params.categories = [category]
            
            filtered = OrderFilter.apply(orders, filter_params)
            
            # Экспортировать
            exporter = CSVExporter(export_dir=output_dir)
            path = exporter.export(filtered)
            
            typer.echo(f"✓ Exported {len(filtered)} orders to: {path}")
        else:
            typer.echo(f"⚠️  No orders found for period: {period}" + (f", category: {category}" if category else ""))
            typer.echo("   No data to export.")
        
        await db_manager.close()
    
    asyncio.run(_export())


@export_app.command()
def html(
    period: str = typer.Option("week", help="Period: today, week, month, all"),
    category: str = typer.Option("", help="Filter by category"),
    output_dir: str = typer.Option("./exports", help="Output directory"),
):
    """Экспортировать заказы в интерактивную HTML таблицу."""
    async def _export():
        from datetime import datetime
        from src.database.schemas import Order
        
        await db_manager.initialize()
        orders = []
        
        # Попытка использовать прямое подключение к БД
        if db_manager.is_initialized():
            try:
                async for session in db_manager.get_session():
                    try:
                        repo = OrderRepository(session)
                        orders = await repo.get_recent(days=365, limit=1000)
                    finally:
                        break
            except Exception as db_error:
                logger.warning(f"Direct DB connection failed: {db_error}, falling back to REST API")
                orders = []
        
        # Fallback на REST API если прямое подключение не работает или нет данных
        if not orders:
            try:
                from datetime import timedelta
                from src.database.supabase_client import get_supabase_client
                client = await get_supabase_client()
                
                try:
                    # Определить диапазон дат в зависимости от периода
                    end_date = datetime.utcnow()
                    if period == "today":
                        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    elif period == "week":
                        start_date = end_date - timedelta(days=7)
                    elif period == "month":
                        start_date = end_date - timedelta(days=30)
                    else:
                        start_date = datetime(2000, 1, 1)
                    
                    orders_data = await client.get_orders(
                        limit=1000,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    orders = []
                    for order_data in orders_data:
                        try:
                            order = Order(
                                id=order_data.get('id'),
                                message_id=str(order_data.get('message_id', '')),
                                chat_id=str(order_data.get('chat_id', '')),
                                author_id=str(order_data.get('author_id', '')),
                                author_name=order_data.get('author_name'),
                                text=order_data.get('text', ''),
                                category=order_data.get('category', 'Other'),
                                relevance_score=float(order_data.get('relevance_score', 0.0)),
                                detected_by=order_data.get('detected_by', 'manual'),
                                telegram_link=order_data.get('telegram_link'),
                                created_at=datetime.fromisoformat(order_data['created_at'].replace('Z', '+00:00')) if order_data.get('created_at') else datetime.utcnow(),
                                exported=order_data.get('exported', False),
                            )
                            orders.append(order)
                        except Exception as conv_error:
                            logger.debug(f"Error converting order data: {conv_error}")
                            continue
                    
                    logger.info(f"Retrieved {len(orders)} orders via REST API (period: {period})")
                finally:
                    await client.close()
            except Exception as rest_error:
                logger.error(f"REST API fallback failed: {rest_error}")
                logger.info("No database connection available. Please check your configuration.")
        
        # Применить фильтры
        if orders:
            filter_params = create_filter_for_period(period)
            if category:
                filter_params.categories = [category]
            
            filtered = OrderFilter.apply(orders, filter_params)
            
            exporter = HTMLExporter(export_dir=output_dir)
            path = exporter.export(filtered)
            
            typer.echo(f"✓ Exported {len(filtered)} orders to: {path}")
            typer.echo(f"✓ Open in browser: file://{path.absolute()}")
        else:
            typer.echo(f"⚠️  No orders found for period: {period}" + (f", category: {category}" if category else ""))
            typer.echo("   No data to export.")
        
        await db_manager.close()
    
    asyncio.run(_export())


@app.command()
def start(
    monitor_all: bool = typer.Option(
        False,
        "--all",
        help="Monitor ALL chats (ignore config)"
    ),
):
    """
    ▶️  Запустить userbot для мониторинга Telegram.
    
    По умолчанию мониторит только сконфигурированные чаты.
    Используй --all для мониторинга всех чатов.
    
    Процесс:
    1. Подключиться к Telegram
    2. Мониторить входящие сообщения
    3. Анализировать через Regex (быстро)
    4. Анализировать через LLM (для ambiguous)
    5. Сохранять в Supabase
    6. Выводить результаты
    """
    async def _start():
        userbot_app = UserbotApp()
        await userbot_app.start(monitor_all=monitor_all)
    
    try:
        asyncio.run(_start())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


async def main():
    """Main async entry point."""
    userbot_app = UserbotApp()
    await userbot_app.start()


@stats_app.command()
def dashboard(
    period: str = typer.Option("week", help="Period: today, week, month, all"),
):
    """Показать dashboard с метриками."""
    async def _show_dashboard():
        from datetime import datetime, timedelta
        from src.database.schemas import Order
        
        # Получить заказы
        await db_manager.initialize()
        
        orders = []
        
        # Попытка использовать прямое подключение к БД
        if db_manager.is_initialized():
            try:
                async for session in db_manager.get_session():
                    try:
                        repo = OrderRepository(session)
                        
                        if period == "today":
                            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                            orders_raw = await repo.get_recent(days=2, limit=1000)
                            orders = [o for o in orders_raw if o.created_at >= today_start]
                            logger.debug(f"Found {len(orders)} orders for today (since {today_start})")
                        elif period == "week":
                            orders = await repo.get_recent(days=7)
                        elif period == "month":
                            orders = await repo.get_recent(days=30)
                        else:
                            orders = await repo.get_recent(days=365)
                    finally:
                        break
            except Exception as db_error:
                logger.warning(f"Direct DB connection failed: {db_error}, falling back to REST API")
                orders = []  # Сбросить, чтобы попробовать REST API
        
        # Fallback на REST API если прямое подключение не работает или нет данных
        if not orders:
            try:
                from src.database.supabase_client import get_supabase_client
                client = await get_supabase_client()
                
                try:
                    # Определить диапазон дат
                    end_date = datetime.utcnow()
                    if period == "today":
                        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        days_back = 2
                    elif period == "week":
                        start_date = end_date - timedelta(days=7)
                        days_back = 7
                    elif period == "month":
                        start_date = end_date - timedelta(days=30)
                        days_back = 30
                    else:
                        start_date = datetime(2000, 1, 1)
                        days_back = 365
                    
                    # Получить заказы через REST API
                    orders_data = await client.get_orders(
                        limit=1000,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    # Конвертировать в объекты Order
                    orders = []
                    for order_data in orders_data:
                        try:
                            # Преобразовать данные из REST API в объект Order
                            order = Order(
                                id=order_data.get('id'),
                                message_id=str(order_data.get('message_id', '')),
                                chat_id=str(order_data.get('chat_id', '')),
                                author_id=str(order_data.get('author_id', '')),
                                author_name=order_data.get('author_name'),
                                text=order_data.get('text', ''),
                                category=order_data.get('category', 'Other'),
                                relevance_score=float(order_data.get('relevance_score', 0.0)),
                                detected_by=order_data.get('detected_by', 'manual'),
                                telegram_link=order_data.get('telegram_link'),
                                created_at=datetime.fromisoformat(order_data['created_at'].replace('Z', '+00:00')) if order_data.get('created_at') else datetime.utcnow(),
                                exported=order_data.get('exported', False),
                            )
                            orders.append(order)
                        except Exception as conv_error:
                            logger.debug(f"Error converting order data: {conv_error}")
                            continue
                    
                    logger.info(f"Retrieved {len(orders)} orders via REST API (period: {period})")
                finally:
                    await client.close()
            except Exception as rest_error:
                logger.error(f"REST API fallback failed: {rest_error}")
                logger.info("No database connection available. Please check your configuration.")
        
        # Показать dashboard
        logger.debug(f"Displaying dashboard for {len(orders)} orders (period: {period})")
        Dashboard.print_full_dashboard(orders, period)
        
        await db_manager.close()
    
    asyncio.run(_show_dashboard())


@stats_app.command()
def export(
    period: str = typer.Option("week", help="Period: today, week, month, all"),
    output_dir: str = typer.Option("./exports", help="Output directory"),
):
    """Экспортировать метрики в CSV."""
    async def _export_stats():
        from datetime import datetime, timedelta
        from src.database.schemas import Order
        
        await db_manager.initialize()
        orders = []
        
        # Попытка использовать прямое подключение к БД
        if db_manager.is_initialized():
            try:
                async for session in db_manager.get_session():
                    try:
                        repo = OrderRepository(session)
                        
                        if period == "today":
                            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                            orders_raw = await repo.get_recent(days=2, limit=1000)
                            orders = [o for o in orders_raw if o.created_at >= today_start]
                        elif period == "week":
                            orders = await repo.get_recent(days=7)
                        elif period == "month":
                            orders = await repo.get_recent(days=30)
                        else:
                            orders = await repo.get_recent(days=365)
                    finally:
                        break
            except Exception as db_error:
                logger.warning(f"Direct DB connection failed: {db_error}, falling back to REST API")
                orders = []
        
        # Fallback на REST API если прямое подключение не работает или нет данных
        if not orders:
            try:
                from src.database.supabase_client import get_supabase_client
                client = await get_supabase_client()
                
                try:
                    # Определить диапазон дат
                    end_date = datetime.utcnow()
                    if period == "today":
                        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    elif period == "week":
                        start_date = end_date - timedelta(days=7)
                    elif period == "month":
                        start_date = end_date - timedelta(days=30)
                    else:
                        start_date = datetime(2000, 1, 1)
                    
                    # Получить заказы через REST API
                    orders_data = await client.get_orders(
                        limit=1000,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    # Конвертировать в объекты Order
                    orders = []
                    for order_data in orders_data:
                        try:
                            order = Order(
                                id=order_data.get('id'),
                                message_id=str(order_data.get('message_id', '')),
                                chat_id=str(order_data.get('chat_id', '')),
                                author_id=str(order_data.get('author_id', '')),
                                author_name=order_data.get('author_name'),
                                text=order_data.get('text', ''),
                                category=order_data.get('category', 'Other'),
                                relevance_score=float(order_data.get('relevance_score', 0.0)),
                                detected_by=order_data.get('detected_by', 'manual'),
                                telegram_link=order_data.get('telegram_link'),
                                created_at=datetime.fromisoformat(order_data['created_at'].replace('Z', '+00:00')) if order_data.get('created_at') else datetime.utcnow(),
                                exported=order_data.get('exported', False),
                            )
                            orders.append(order)
                        except Exception as conv_error:
                            logger.debug(f"Error converting order data: {conv_error}")
                            continue
                    
                    logger.info(f"Retrieved {len(orders)} orders via REST API (period: {period})")
                finally:
                    await client.close()
            except Exception as rest_error:
                logger.error(f"REST API fallback failed: {rest_error}")
                logger.info("No database connection available. Please check your configuration.")
        
        # Экспортировать метрики
        if orders:
            reporter = MetricsReporter(export_dir=output_dir)
            
            # Daily metrics
            period_metrics = MetricsCalculator.calculate_period_metrics(orders, period)
            daily_path = reporter.export_daily_metrics_csv(period_metrics)
            
            # Category metrics
            category_metrics = MetricsCalculator.calculate_category_metrics(orders)
            category_path = reporter.export_category_metrics_csv(category_metrics)
            
            typer.echo(f"✓ Daily metrics exported to: {daily_path}")
            typer.echo(f"✓ Category metrics exported to: {category_path}")
            typer.echo(f"✓ Exported metrics for {len(orders)} orders")
        else:
            typer.echo(f"⚠️  No orders found for period: {period}")
            typer.echo("   No metrics to export.")
        
        await db_manager.close()
    
    asyncio.run(_export_stats())


@stats_app.command()
def summary(
    period: str = typer.Option("week", help="Period: today, week, month, all"),
):
    """Показать сводный отчет."""
    async def _show_summary():
        from datetime import datetime, timedelta
        from src.database.schemas import Order
        
        await db_manager.initialize()
        orders = []
        
        # Попытка использовать прямое подключение к БД
        if db_manager.is_initialized():
            try:
                async for session in db_manager.get_session():
                    try:
                        repo = OrderRepository(session)
                        
                        if period == "today":
                            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                            orders_raw = await repo.get_recent(days=2, limit=1000)
                            orders = [o for o in orders_raw if o.created_at >= today_start]
                        elif period == "week":
                            orders = await repo.get_recent(days=7)
                        elif period == "month":
                            orders = await repo.get_recent(days=30)
                        else:
                            orders = await repo.get_recent(days=365)
                    finally:
                        break
            except Exception as db_error:
                logger.warning(f"Direct DB connection failed: {db_error}, falling back to REST API")
                orders = []
        
        # Fallback на REST API
        if not orders:
            try:
                from src.database.supabase_client import get_supabase_client
                client = await get_supabase_client()
                try:
                    end_date = datetime.utcnow()
                    if period == "today":
                        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    elif period == "week":
                        start_date = end_date - timedelta(days=7)
                    elif period == "month":
                        start_date = end_date - timedelta(days=30)
                    else:
                        start_date = datetime(2000, 1, 1)
                    
                    orders_data = await client.get_orders(limit=1000, start_date=start_date, end_date=end_date)
                    orders = []
                    for order_data in orders_data:
                        try:
                            order = Order(
                                id=order_data.get('id'),
                                message_id=str(order_data.get('message_id', '')),
                                chat_id=str(order_data.get('chat_id', '')),
                                author_id=str(order_data.get('author_id', '')),
                                author_name=order_data.get('author_name'),
                                text=order_data.get('text', ''),
                                category=order_data.get('category', 'Other'),
                                relevance_score=float(order_data.get('relevance_score', 0.0)),
                                detected_by=order_data.get('detected_by', 'manual'),
                                telegram_link=order_data.get('telegram_link'),
                                created_at=datetime.fromisoformat(order_data['created_at'].replace('Z', '+00:00')) if order_data.get('created_at') else datetime.utcnow(),
                                exported=order_data.get('exported', False),
                            )
                            orders.append(order)
                        except Exception:
                            continue
                finally:
                    await client.close()
            except Exception as rest_error:
                logger.error(f"REST API fallback failed: {rest_error}")
        
        # Генерировать отчет
        reporter = MetricsReporter()
        summary = reporter.generate_summary_report(orders, period)
        
        # Печать
        import json
        typer.echo(json.dumps(summary, indent=2, ensure_ascii=False))
        
        await db_manager.close()
    
    asyncio.run(_show_summary())


# ============================================================================
# ADMIN COMMANDS
# ============================================================================

@admin_app.command()
def init_db():
    """Инициализировать БД (создать таблицы)."""
    async def _init_database():
        logger.info("Initializing database...")
        
        await db_manager.initialize()
        await db_manager.create_tables()
        
        logger.info("✓ Database initialized with all tables")
        await db_manager.close()
    
    asyncio.run(_init_database())


@admin_app.command()
def test_connection():
    """Проверить подключение к Supabase."""
    async def _test_db_connection():
        logger.info("Testing database connection...")
        
        try:
            await db_manager.initialize()
            
            async for session in db_manager.get_session():
                try:
                    # Простой query для проверки
                    from sqlalchemy import text
                    await session.execute(text("SELECT 1"))
                    await session.commit()
                finally:
                    break
            
            logger.info("✓ Database connection successful")
        
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
        
        finally:
            await db_manager.close()
    
    asyncio.run(_test_db_connection())


# ============================================================================
# CHAT MANAGEMENT COMMANDS
# ============================================================================

@chat_app.command()
def list():
    """Показать все чаты (активные и неактивные)."""
    from src.config.chat_config import chat_config_manager
    from rich.console import Console
    from rich.table import Table
    
    console = Console()
    chat_config_manager.initialize()
    
    all_chats = chat_config_manager.get_all_chats()
    
    if not all_chats:
        console.print("[yellow]No chats configured yet[/]")
        return
    
    table = Table(title="📋 Monitored Chats", show_header=True)
    table.add_column("Status", style="cyan")
    table.add_column("Chat Name", style="green")
    table.add_column("Chat ID", style="blue")
    table.add_column("Type", style="magenta")
    table.add_column("Priority", style="yellow")
    table.add_column("Since", style="dim")
    
    for config in sorted(all_chats, key=lambda c: c.priority, reverse=True):
        status = "🟢 Active" if config.is_active else "🔴 Inactive"
        since = config.enabled_at.strftime("%Y-%m-%d") if config.enabled_at else "N/A"
        
        table.add_row(
            status,
            config.chat_name,
            config.chat_id,
            config.chat_type,
            str(config.priority),
            since,
        )
    
    console.print(table)
    console.print(f"\n[dim]Active chats: {len(chat_config_manager.get_active_chats())} / {len(all_chats)}[/]")


@chat_app.command()
def add(
    chat_id: str = typer.Argument(..., help="Chat ID (negative number for groups)"),
    chat_name: str = typer.Option(..., "--name", help="Chat name/title"),
    chat_type: str = typer.Option("group", help="Chat type: group, channel, supergroup"),
    priority: int = typer.Option(1, help="Priority 1-5 (5=highest)"),
):
    """Добавить чат в список мониторинга."""
    from src.config.chat_config import chat_config_manager
    
    chat_config_manager.initialize()
    
    # Валидация
    if not 1 <= priority <= 5:
        typer.echo("❌ Priority must be 1-5")
        return
    
    if chat_type not in ["group", "channel", "supergroup"]:
        typer.echo("❌ Chat type must be: group, channel, or supergroup")
        return
    
    config = chat_config_manager.add_chat(chat_id, chat_name, chat_type, priority)
    typer.echo(f"✓ Added: {config}")


@chat_app.command()
def remove(
    chat_id: str = typer.Argument(..., help="Chat ID to remove"),
    reason: str = typer.Option("", help="Reason for removal"),
):
    """Отключить чат от мониторинга."""
    from src.config.chat_config import chat_config_manager
    
    chat_config_manager.initialize()
    
    if chat_config_manager.remove_chat(chat_id, reason or "Disabled by user"):
        typer.echo(f"✓ Removed chat {chat_id}")
    else:
        typer.echo(f"❌ Chat {chat_id} not found")


@chat_app.command()
def enable(
    chat_id: str = typer.Argument(..., help="Chat ID to enable"),
):
    """Включить мониторинг чата."""
    from src.config.chat_config import chat_config_manager
    
    chat_config_manager.initialize()
    
    if chat_config_manager.enable_chat(chat_id):
        typer.echo(f"✓ Enabled chat {chat_id}")
    else:
        typer.echo(f"❌ Chat {chat_id} not found")


@chat_app.command()
def disable(
    chat_id: str = typer.Argument(..., help="Chat ID to disable"),
    reason: str = typer.Option("", help="Reason"),
):
    """Отключить мониторинг чата."""
    from src.config.chat_config import chat_config_manager
    
    chat_config_manager.initialize()
    
    if chat_config_manager.disable_chat(chat_id, reason):
        typer.echo(f"✓ Disabled chat {chat_id}")
    else:
        typer.echo(f"❌ Chat {chat_id} not found")


@chat_app.command()
def priority(
    chat_id: str = typer.Argument(..., help="Chat ID"),
    level: int = typer.Argument(..., help="Priority level 1-5"),
):
    """Установить приоритет чата."""
    from src.config.chat_config import chat_config_manager
    
    chat_config_manager.initialize()
    
    if chat_config_manager.set_priority(chat_id, level):
        typer.echo(f"✓ Set priority {level} for chat {chat_id}")
    else:
        typer.echo(f"❌ Failed to set priority")


@chat_app.command()
def auto_detect():
    """Автоматически обнаружить все чаты (интерактивно)."""
    async def _auto_detect():
        from src.config.chat_config import chat_config_manager
        
        chat_config_manager.initialize()
        
        # Инициализировать Telegram
        telegram_client = TelegramClient()
        await telegram_client.start()
        
        # Обнаружить чаты
        detected = await telegram_client.auto_detect_chats()
        
        if not detected:
            typer.echo("\n⚠️  No chats found")
            typer.echo("\nPossible reasons:")
            typer.echo("  • Request timed out (try again)")
            typer.echo("  • No group/channel chats in your account")
            typer.echo("  • All chats are private")
            typer.echo("\n💡 You can add chats manually:")
            typer.echo("  python3 -m src.main chat add <chat_id> --name \"Chat Name\"")
            await telegram_client.stop()
            return
        
        # Показать найденные чаты
        from rich.console import Console
        from rich.table import Table
        
        console = Console()
        
        table = Table(title="🔍 Detected Chats", show_header=True)
        table.add_column("№", style="cyan")
        table.add_column("Chat Name", style="green")
        table.add_column("Chat ID", style="blue")
        table.add_column("Type", style="magenta")
        
        for i, config in enumerate(detected, 1):
            table.add_row(
                str(i),
                config.chat_name,
                config.chat_id,
                config.chat_type,
            )
        
        console.print(table)
        
        # Интерактивный выбор
        console.print("\n[bold]Add to monitoring? Enter numbers separated by comma (e.g., 1,3,5)[/]")
        selection = console.input("[bold cyan]→[/] ").strip()
        
        if selection:
            try:
                selected_indices = [int(x.strip()) - 1 for x in selection.split(",")]
                
                added_count = 0
                for idx in selected_indices:
                    if 0 <= idx < len(detected):
                        config = detected[idx]
                        chat_config_manager.add_chat(
                            config.chat_id,
                            config.chat_name,
                            config.chat_type,
                            priority=1,
                        )
                        added_count += 1
                
                console.print(f"\n✓ Added {added_count} chats to monitoring")
            
            except ValueError:
                console.print("[red]Invalid input[/]")
        
        await telegram_client.stop()
    
    asyncio.run(_auto_detect())


@chat_app.command()
def clear():
    """Очистить все сконфигурированные чаты (осторожно!)."""
    from src.config.chat_config import chat_config_manager
    
    chat_config_manager.initialize()
    
    confirm = typer.confirm("Are you sure you want to clear all chats? This cannot be undone!")
    
    if confirm:
        chat_config_manager.clear_all()
        typer.echo("✓ Cleared all chats")
    else:
        typer.echo("Cancelled")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    app()

