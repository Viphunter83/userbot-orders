"""Telegram client using Pyrogram for userbot functionality."""

import asyncio
from typing import Optional, Callable, Awaitable
from datetime import datetime
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import AuthKeyUnregistered, SessionPasswordNeeded
from loguru import logger

from src.config.settings import get_settings
from src.utils.logger import setup_logger

# Suppress Pyrogram warnings about unhandled updates
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*Task exception was never retrieved.*")


class TelegramClient:
    """Telegram userbot client using Pyrogram."""
    
    def __init__(self, session_name: str = "userbot_session"):
        """
        Initialize Telegram client.
        
        Args:
            session_name: Name for Pyrogram session file
        """
        settings = get_settings()
        self.settings = settings
        self.session_name = session_name
        self.client: Optional[Client] = None
        self.is_running = False
        self.message_callback: Optional[Callable[[Message], Awaitable[None]]] = None
        
        # Setup logger
        setup_logger(log_level=settings.log_level)
        
        logger.info("TelegramClient initialized")
    
    async def start(self) -> None:
        """Start and authorize Telegram client."""
        try:
            credentials = self.settings.telegram_credentials
            
            self.client = Client(
                name=self.session_name,
                api_id=credentials["api_id"],
                api_hash=credentials["api_hash"],
                phone_number=credentials["phone_number"],
                password=self.settings.telegram_password if self.settings.telegram_password else None,
                no_updates=False,  # Enable updates
            )
            
            logger.info("Starting Telegram client...")
            await self.client.start()
            
            # Set up exception handler for asyncio tasks to catch Pyrogram internal errors
            def exception_handler(loop, context):
                """Handle unhandled exceptions in asyncio tasks."""
                exception = context.get('exception')
                message = context.get('message', '')
                
                if exception:
                    error_str = str(exception)
                    # Ignore invalid peer ID errors
                    if isinstance(exception, ValueError) and "Peer id invalid" in error_str:
                        logger.debug(f"Skipping update with invalid peer ID: {error_str}")
                        return
                    if isinstance(exception, KeyError) and "ID not found" in error_str:
                        logger.debug(f"Skipping update from unknown peer: {error_str}")
                        return
                    # Ignore database closed errors during shutdown
                    if "closed database" in error_str.lower() or "cannot operate" in error_str.lower():
                        logger.debug(f"Ignoring database closed error: {error_str}")
                        return
                    # Log other exceptions
                    if "Peer id invalid" not in error_str and "ID not found" not in error_str:
                        logger.warning(f"Unhandled exception in asyncio task: {exception}")
                else:
                    # Filter out socket.send() errors during shutdown
                    if "socket.send()" in message or ("socket" in message.lower() and "exception" in message.lower()):
                        logger.debug(f"Ignoring socket error during shutdown: {message}")
                        return
                    # Log other context errors
                    if "Peer id invalid" not in message and "ID not found" not in message:
                        logger.warning(f"Asyncio context error: {message}")
            
            # Set exception handler for current event loop
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(exception_handler)
            
            # Get user info
            me = await self.client.get_me()
            logger.info(f"✓ Telegram client started successfully")
            logger.info(f"  User: {me.first_name} (@{me.username or 'no username'})")
            logger.info(f"  User ID: {me.id}")
            logger.info(f"  Phone: {me.phone_number}")
            
            self.is_running = True
            
            # Check connection
            await self._check_connection()
            
        except SessionPasswordNeeded:
            logger.error("2FA password required but not provided in settings")
            raise
        except AuthKeyUnregistered:
            logger.error("Session expired. Please delete session file and re-authenticate")
            raise
        except Exception as e:
            logger.error(f"Failed to start Telegram client: {e}")
            raise
    
    async def _check_connection(self) -> None:
        """Check Telegram connection status."""
        try:
            if self.client:
                me = await self.client.get_me()
                logger.info(f"✓ Connection check: OK (User: {me.first_name})")
        except Exception as e:
            logger.error(f"✗ Connection check failed: {e}")
            raise
    
    async def listen_messages(
        self,
        callback: Callable[[Message], Awaitable[None]],
        filter_chats: bool = True,
    ) -> None:
        """
        Register handler for new messages with optional chat filtering.
        
        Args:
            callback: Async function that will be called for each new message
            filter_chats: If True, listen only to configured chats
        """
        if not self.client:
            raise RuntimeError("Client not started. Call start() first.")
        
        if not self.is_running:
            raise RuntimeError("Client is not running.")
        
        self.message_callback = callback
        logger.info("Message listener registered")
        
        # Import chat config manager if filtering is enabled
        if filter_chats:
            from src.config.chat_config import chat_config_manager
            chat_config_manager.initialize()
        
        @self.client.on_message()
        async def message_handler(client: Client, message: Message):
            """Handle incoming messages."""
            try:
                # Get chat info first for logging
                try:
                    chat_id = str(message.chat.id)
                    chat_title = getattr(message.chat, 'title', None) or getattr(message.chat, 'first_name', 'Unknown')
                except Exception as e:
                    logger.debug(f"Error getting chat info: {e}")
                    return
                
                # Log ALL incoming messages for debugging
                logger.info(f"📥 Received message from chat: {chat_title} ({chat_id})")
                
                # Skip if message is from bot itself
                if message.from_user and message.from_user.is_self:
                    logger.debug(f"Skipping message from self")
                    return
                
                # Skip empty messages (check both text and caption)
                if not message.text and not message.caption:
                    # Логируем пропуск пустых сообщений для отладки
                    author_info = "Unknown"
                    if message.from_user:
                        author_info = f"{message.from_user.first_name} (@{message.from_user.username or 'no username'})"
                        if message.from_user.is_bot:
                            author_info += " [BOT]"
                    
                    logger.debug(
                        f"Skipping empty message from chat {chat_id} "
                        f"(author: {author_info}, has_media: {bool(message.media)}, "
                        f"media_type: {type(message.media).__name__ if message.media else 'None'})"
                    )
                    return
                
                # Validate chat ID
                if not chat_id or chat_id == "0" or chat_id == "unknown":
                    logger.debug(f"Skipping message with invalid chat ID")
                    return
                
                # Filter by chat configuration
                if filter_chats:
                    is_monitored = chat_config_manager.is_chat_monitored(chat_id)
                    monitored_ids = [c.chat_id for c in chat_config_manager.get_active_chats()]
                    
                    if not is_monitored:
                        logger.info(f"⚠️  Chat {chat_title} ({chat_id}) NOT in monitored list")
                        logger.info(f"   Monitored chats: {monitored_ids}")
                        logger.info(f"   💡 To add this chat: python3 -m src.main chat add {chat_id} --name \"{chat_title}\"")
                        return
                    else:
                        logger.info(f"✓ Chat {chat_title} ({chat_id}) IS monitored, processing message")
                
                # Детальная информация о сообщении для отладки
                author_info = "Unknown"
                is_bot = False
                if message.from_user:
                    author_info = f"{message.from_user.first_name} (@{message.from_user.username or 'no username'})"
                    is_bot = message.from_user.is_bot
                
                message_preview = (message.text or message.caption or "[No text]")[:100]
                
                # Детальное логирование для отладки
                logger.info(
                    f"📨 Message received from chat {chat_id} | "
                    f"Author: {author_info} {'[BOT]' if is_bot else '[USER]'} | "
                    f"Text length: {len(message.text or message.caption or '')} | "
                    f"Preview: {message_preview}"
                )
                
                # Важно: передать сообщение в callback только если есть текст или caption
                if self.message_callback:
                    try:
                        await self.message_callback(message)
                    except Exception as callback_error:
                        logger.error(f"Error in message callback: {callback_error}", exc_info=True)
            except ValueError as ve:
                # Skip invalid peer IDs
                logger.debug(f"Skipping message with invalid peer: {ve}")
            except KeyError as ke:
                # Skip chats not found in storage
                logger.debug(f"Skipping message from chat not in storage: {ke}")
            except Exception as e:
                logger.error(f"Error in message callback: {e}", exc_info=True)
        
        logger.info("✓ Message listener started. Waiting for messages...")
        
        # Keep the client running
        # In Pyrogram 2.0, handlers are registered and client stays alive
        # We use asyncio.sleep in a loop to keep the coroutine alive
        import asyncio
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Message listener cancelled")
    
    async def auto_detect_chats(self) -> list:
        """
        Automatically detect all chats where user participates.
        
        Returns:
            List of detected ChatConfig objects
        """
        from src.config.chat_config import ChatConfig
        
        logger.info("🔍 Auto-detecting chats...")
        logger.info("   This may take a while if you have many chats...")
        
        detected_chats = []
        max_retries = 5  # Увеличить количество попыток для таймаутов
        retry_delay = 3  # Начать с 3 секунд
        
        # Set up exception handler for asyncio to catch Pyrogram internal errors
        def exception_handler(loop, context):
            """Handle unhandled exceptions from asyncio event loop."""
            exception = context.get('exception')
            if exception:
                error_msg = str(exception)
                # Filter out known Pyrogram errors that we can safely ignore
                if "Peer id invalid" in error_msg or "ID not found" in error_msg:
                    logger.debug(f"Ignoring Pyrogram peer ID error: {error_msg}")
                    return
            # Log other exceptions
            logger.error(f"Unhandled exception in event loop: {context}")
        
        # Get current event loop and set exception handler
        loop = asyncio.get_event_loop()
        old_handler = loop.get_exception_handler()
        loop.set_exception_handler(exception_handler)
        
        try:
            for attempt in range(max_retries):
                try:
                    logger.info(f"   Attempt {attempt + 1}/{max_retries}...")
                    
                    # Get all dialogs with timeout
                    dialog_count = 0
                    skipped_count = 0
                    
                    try:
                        # Получить диалоги с обработкой таймаутов
                        # Используем limit=None для получения всех диалогов
                        async for dialog in self.client.get_dialogs(limit=None):
                            try:
                                chat = dialog.chat
                                dialog_count += 1
                                
                                # Skip private chats
                                if chat.type == "private":
                                    skipped_count += 1
                                    continue
                                
                                # Validate chat ID
                                try:
                                    chat_id = str(chat.id)
                                    if not chat_id or chat_id == "0":
                                        skipped_count += 1
                                        logger.debug(f"Skipping chat with invalid ID: {chat_id}")
                                        continue
                                except Exception as e:
                                    skipped_count += 1
                                    logger.debug(f"Error getting chat ID: {e}")
                                    continue
                                
                                # Get title
                                try:
                                    title = getattr(chat, 'title', None) or getattr(chat, 'first_name', 'Unknown')
                                except Exception:
                                    title = 'Unknown'
                                
                                # Skip if title is empty
                                if not title or title == "Unknown":
                                    skipped_count += 1
                                    logger.debug(f"Skipping chat without title: {chat_id}")
                                    continue
                                
                                chat_config = ChatConfig(
                                    chat_id=chat_id,
                                    chat_name=title[:255],  # Limit length
                                    chat_type=str(chat.type),
                                    is_active=False,  # По умолчанию не активны
                                )
                                
                                detected_chats.append(chat_config)
                                logger.info(f"   ✓ Detected: {title} ({chat_id})")
                            
                            except ValueError as ve:
                                # Skip invalid peer IDs
                                skipped_count += 1
                                error_msg = str(ve)
                                if "Peer id invalid" in error_msg:
                                    logger.debug(f"Skipping chat with invalid peer ID")
                                else:
                                    logger.debug(f"Skipping chat: {ve}")
                                continue
                            except KeyError as ke:
                                # Skip chats not found in storage
                                skipped_count += 1
                                error_msg = str(ke)
                                if "ID not found" in error_msg:
                                    logger.debug(f"Skipping chat not in storage")
                                else:
                                    logger.debug(f"Skipping chat: {ke}")
                                continue
                            except Exception as e:
                                # Skip any other errors for this chat
                                skipped_count += 1
                                error_msg = str(e)
                                if "Peer id invalid" in error_msg or "ID not found" in error_msg:
                                    logger.debug(f"Skipping chat with peer error")
                                else:
                                    logger.debug(f"Error processing chat: {e}")
                                continue
                    
                    except ValueError as ve:
                        # Handle ValueError at dialog level
                        error_msg = str(ve)
                        if "Peer id invalid" in error_msg:
                            logger.warning(f"   Encountered invalid peer IDs, but continuing...")
                            # Continue processing - we've already caught individual chat errors
                        else:
                            raise
                    
                    # If we got here, we successfully processed dialogs
                    logger.info(f"   Processed {dialog_count} dialogs (skipped {skipped_count})")
                    break
                    
                except Exception as e:
                    error_str = str(e)
                    # Handle timeout errors
                    if "timed out" in error_str.lower() or "timeout" in error_str.lower() or "Request timed out" in error_str:
                        if attempt < max_retries - 1:
                            logger.warning(f"   Request timed out, retrying in {retry_delay} seconds... ({attempt + 1}/{max_retries})")
                            logger.info("   💡 This is normal if you have many chats. Please wait...")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            logger.error(f"   Failed after {max_retries} attempts due to timeout: {e}")
                            logger.info("   💡 Telegram API timed out. This can happen if:")
                            logger.info("      • You have many chats/dialogs")
                            logger.info("      • Your internet connection is slow")
                            logger.info("      • Telegram servers are busy")
                            logger.info("   💡 Try again later or add chats manually with: chat add")
                            break
                    elif "Connection lost" in error_str or "Connection" in error_str:
                        if attempt < max_retries - 1:
                            logger.warning(f"   Connection lost, retrying in {retry_delay} seconds... ({attempt + 1}/{max_retries})")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            logger.error(f"   Failed after {max_retries} attempts: {e}")
                            logger.info("   💡 Try again later or check your internet connection")
                            break
                    elif "Peer id invalid" in error_str or "ID not found" in error_str:
                        # These are expected errors, continue
                        logger.warning(f"   Encountered peer ID errors, but continuing...")
                        break
                    else:
                        logger.error(f"Error auto-detecting chats: {e}", exc_info=True)
                        break
        
        finally:
            # Restore original exception handler
            if old_handler:
                loop.set_exception_handler(old_handler)
            else:
                loop.set_exception_handler(None)
        
        logger.info(f"✓ Auto-detected {len(detected_chats)} chats")
        
        return detected_chats
    
    async def stop(self) -> None:
        """Stop Telegram client gracefully."""
        if self.client and self.is_running:
            logger.info("Stopping Telegram client...")
            self.is_running = False
            
            try:
                # Give tasks time to finish before closing
                await asyncio.sleep(0.5)
                
                # Stop the client gracefully
                try:
                    await self.client.stop()
                except Exception as e:
                    # Ignore socket errors during shutdown
                    error_msg = str(e).lower()
                    if "socket" in error_msg or "closed" in error_msg:
                        logger.debug(f"Ignoring socket error during shutdown: {e}")
                    else:
                        logger.warning(f"Error stopping client: {e}")
                
                logger.info("✓ Telegram client stopped")
            
            except Exception as e:
                # Ignore errors during shutdown
                error_msg = str(e).lower()
                if "closed" in error_msg or "socket" in error_msg or "database" in error_msg:
                    logger.debug(f"Ignoring shutdown error: {e}")
                else:
                    logger.warning(f"Error during client shutdown: {e}")
        else:
            logger.debug("Client is not running")
    
    async def get_chat_info(self, chat_id: int) -> Optional[dict]:
        """
        Get chat information.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            Dict with chat info or None
        """
        if not self.client:
            return None
        
        try:
            chat = await self.client.get_chat(chat_id)
            return {
                "id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "type": str(chat.type),
            }
        except Exception as e:
            logger.error(f"Failed to get chat info for {chat_id}: {e}")
            return None
    
    def __enter__(self):
        """Context manager entry (sync)."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit (sync)."""
        if self.is_running:
            asyncio.run(self.stop())
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

