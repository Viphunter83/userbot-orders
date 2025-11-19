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
            )
            
            logger.info("Starting Telegram client...")
            await self.client.start()
            
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
        callback: Callable[[Message], Awaitable[None]]
    ) -> None:
        """
        Register handler for new messages.
        
        Args:
            callback: Async function that will be called for each new message
        """
        if not self.client:
            raise RuntimeError("Client not started. Call start() first.")
        
        if not self.is_running:
            raise RuntimeError("Client is not running.")
        
        self.message_callback = callback
        logger.info("Message listener registered")
        
        @self.client.on_message()
        async def message_handler(client: Client, message: Message):
            """Handle incoming messages."""
            try:
                if self.message_callback:
                    await self.message_callback(message)
            except Exception as e:
                logger.error(f"Error in message callback: {e}")
        
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
    
    async def stop(self) -> None:
        """Stop Telegram client gracefully."""
        if self.client and self.is_running:
            logger.info("Stopping Telegram client...")
            try:
                await self.client.stop()
                self.is_running = False
                logger.info("✓ Telegram client stopped")
            except Exception as e:
                logger.error(f"Error stopping client: {e}")
                raise
        else:
            logger.warning("Client is not running")
    
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

