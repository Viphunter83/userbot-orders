"""Main entry point for Telegram userbot."""

import asyncio
import signal
from datetime import datetime
from typing import Optional
from pyrogram.types import Message
from loguru import logger

from src.telegram.client import TelegramClient
from src.utils.logger import setup_logger
from src.config.settings import get_settings
from src.analysis.regex_analyzer import RegexAnalyzer
from src.database.base import db_manager
from src.database.repository import ChatRepository, MessageRepository, OrderRepository, StatRepository


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
            if detection_result:
                logger.info(
                    f"  ✓ Order detected: {detection_result.category.value} "
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
                                    regex_detections=1 if detection_result.detected_by.value == "regex" else 0,
                                )
                                
                                logger.info(f"  ✓ Order saved to database")
                            finally:
                                # Session will be auto-committed/closed by generator
                                break
                    except Exception as e:
                        logger.error(f"Error saving order to database: {e}", exc_info=True)
            else:
                logger.debug("  No order detected by regex")
            
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


async def main():
    """Main async entry point."""
    app = UserbotApp()
    await app.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

