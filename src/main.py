"""Main entry point for Telegram userbot."""

import asyncio
import signal
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
app = typer.Typer(help="Telegram Userbot for Order Monitoring")
export_app = typer.Typer(help="Export commands")
stats_app = typer.Typer(help="Stats and analytics commands")
app.add_typer(export_app, name="export")
app.add_typer(stats_app, name="stats")


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
            message_text = message.text or message.caption or "[No text]"
            author_id = message.from_user.id if message.from_user else None
            author_username = (
                message.from_user.username 
                if message.from_user and message.from_user.username 
                else "unknown"
            )
            chat_id = message.chat.id
            chat_title = message.chat.title or "Private Chat"
            message_date = message.date
            
            # Format time
            time_str = message_date.strftime("%Y-%m-%d %H:%M")
            
            # Log message
            logger.info(
                f"New Telegram message: '{message_text[:100]}...' | "
                f"Author: {author_username} ({author_id}) | "
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
                                chat_type = "channel"
                                if hasattr(message.chat, 'type'):
                                    if message.chat.type == "group":
                                        chat_type = "group"
                                    elif message.chat.type == "supergroup":
                                        chat_type = "group"
                                
                                chat = await chat_repo.create(
                                    chat_id=str(chat_id),
                                    chat_name=chat_title[:255],  # Limit length
                                    chat_type=chat_type
                                )
                            
                            # Check if message already exists (deduplication)
                            message_id_str = str(message.id)
                            if not await message_repo.exists(message_id_str, str(chat_id)):
                                # Save message
                                await message_repo.create(
                                    message_id=message_id_str,
                                    chat_id=str(chat_id),
                                    author_id=str(author_id) if author_id else "unknown",
                                    author_name=author_username[:255] if author_username else None,
                                    text=message_text[:10000] if len(message_text) > 10000 else message_text,  # Limit text length
                                    timestamp=message_date,
                                )
                                
                                # Update chat's last message time
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
            detection_result = self.regex_analyzer.analyze(message_text)
            
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
                                
                                # Save order
                                await order_repo.create(
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
                                
                                # Update statistics
                                await stat_repo.update_metrics(
                                    detected_orders=1,
                                    regex_detections=1,
                                )
                                
                                logger.info(f"  ✓ Order saved to database")
                            finally:
                                # Session will be auto-committed/closed by generator
                                break
                    except Exception as e:
                        logger.error(f"Error saving order to database: {e}", exc_info=True)
            
            # Level 2: LLM analysis for ambiguous messages
            # Use LLM if regex didn't find anything OR found low-confidence match
            elif not detection_result or detection_result.confidence < 0.80:
                # Only analyze messages that are long enough and might be orders
                if len(message_text.strip()) > 20:  # Skip very short messages
                    try:
                        from src.analysis.llm_classifier import llm_classifier
                        
                        logger.debug("  → Sending to LLM for analysis (ambiguous or no regex match)")
                        llm_result = await llm_classifier.classify(message_text)
                        
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
                                            
                                            # Save order
                                            await order_repo.create(
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
                                            
                                            # Update statistics
                                            await stat_repo.update_metrics(
                                                detected_orders=1,
                                                llm_detections=1,
                                                llm_tokens_used=llm_result.tokens_used or 0,
                                                llm_cost=llm_result.cost_usd or 0.0,
                                            )
                                            
                                            logger.info(f"  ✓ Order saved to database (LLM)")
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
    
    async def start(self) -> None:
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
                self.client.listen_messages(self.message_handler)
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
        
        logger.info("✓ Userbot stopped")


@export_app.command()
def csv(
    period: str = typer.Option("today", help="Period: today, week, month, all"),
    category: str = typer.Option("", help="Filter by category (Backend, Frontend, ...)"),
    output_dir: str = typer.Option("./exports", help="Output directory"),
):
    """Экспортировать заказы в CSV."""
    async def _export():
        # Получить заказы из БД
        await db_manager.initialize()
        
        async for session in db_manager.get_session():
            try:
                repo = OrderRepository(session)
                
                # Создать фильтр
                filter_params = create_filter_for_period(period)
                if category:
                    filter_params.categories = [category]
                
                # Получить заказы
                orders = await repo.get_recent(days=365)  # Получить все
                filtered = OrderFilter.apply(orders, filter_params)
                
                # Экспортировать
                exporter = CSVExporter(export_dir=output_dir)
                path = exporter.export(filtered)
                
                typer.echo(f"✓ Exported {len(filtered)} orders to: {path}")
            finally:
                break
        
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
        await db_manager.initialize()
        
        async for session in db_manager.get_session():
            try:
                repo = OrderRepository(session)
                
                filter_params = create_filter_for_period(period)
                if category:
                    filter_params.categories = [category]
                
                orders = await repo.get_recent(days=365)
                filtered = OrderFilter.apply(orders, filter_params)
                
                exporter = HTMLExporter(export_dir=output_dir)
                path = exporter.export(filtered)
                
                typer.echo(f"✓ Exported {len(filtered)} orders to: {path}")
                typer.echo(f"✓ Open in browser: file://{path.absolute()}")
            finally:
                break
        
        await db_manager.close()
    
    asyncio.run(_export())


@app.command()
def start():
    """Запустить Telegram userbot."""
    async def _start():
        userbot_app = UserbotApp()
        await userbot_app.start()
    
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
    period: str = typer.Option("week", help="Period: week, month, all"),
):
    """Показать dashboard с метриками."""
    async def _show_dashboard():
        # Получить заказы
        await db_manager.initialize()
        
        async for session in db_manager.get_session():
            try:
                repo = OrderRepository(session)
                
                if period == "week":
                    orders = await repo.get_recent(days=7)
                elif period == "month":
                    orders = await repo.get_recent(days=30)
                else:
                    orders = await repo.get_recent(days=365)
                
                # Показать dashboard
                Dashboard.print_full_dashboard(orders, period)
            finally:
                break
        
        await db_manager.close()
    
    asyncio.run(_show_dashboard())


@stats_app.command()
def export(
    period: str = typer.Option("week", help="Period: week, month, all"),
    output_dir: str = typer.Option("./exports", help="Output directory"),
):
    """Экспортировать метрики в CSV."""
    async def _export_stats():
        await db_manager.initialize()
        
        async for session in db_manager.get_session():
            try:
                repo = OrderRepository(session)
                
                # Получить заказы
                if period == "week":
                    orders = await repo.get_recent(days=7)
                elif period == "month":
                    orders = await repo.get_recent(days=30)
                else:
                    orders = await repo.get_recent(days=365)
                
                # Экспортировать
                reporter = MetricsReporter(export_dir=output_dir)
                
                # Daily metrics
                period_metrics = MetricsCalculator.calculate_period_metrics(orders, period)
                daily_path = reporter.export_daily_metrics_csv(period_metrics)
                
                # Category metrics
                category_metrics = MetricsCalculator.calculate_category_metrics(orders)
                category_path = reporter.export_category_metrics_csv(category_metrics)
                
                typer.echo(f"✓ Daily metrics exported to: {daily_path}")
                typer.echo(f"✓ Category metrics exported to: {category_path}")
            finally:
                break
        
        await db_manager.close()
    
    asyncio.run(_export_stats())


@stats_app.command()
def summary(
    period: str = typer.Option("week", help="Period: week, month, all"),
):
    """Показать сводный отчет."""
    async def _show_summary():
        await db_manager.initialize()
        
        async for session in db_manager.get_session():
            try:
                repo = OrderRepository(session)
                
                # Получить заказы
                if period == "week":
                    orders = await repo.get_recent(days=7)
                elif period == "month":
                    orders = await repo.get_recent(days=30)
                else:
                    orders = await repo.get_recent(days=365)
                
                # Генерировать отчет
                reporter = MetricsReporter()
                summary = reporter.generate_summary_report(orders, period)
                
                # Печать
                import json
                typer.echo(json.dumps(summary, indent=2, ensure_ascii=False))
            finally:
                break
        
        await db_manager.close()
    
    asyncio.run(_show_summary())


if __name__ == "__main__":
    # If run directly, use Typer CLI
    app()

