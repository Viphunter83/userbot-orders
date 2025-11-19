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
            
            # Analyze message with regex analyzer (first level filter)
            detection_result = self.regex_analyzer.analyze(message_text)
            if detection_result:
                logger.info(
                    f"  ✓ Order detected: {detection_result.category.value} "
                    f"(confidence: {detection_result.confidence:.2f}, "
                    f"pattern: {detection_result.matched_pattern})"
                )
                logger.debug(f"  Matched text: '{detection_result.matched_text}'")
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

