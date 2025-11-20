"""Fallback mechanism for database operations."""

from typing import Optional, Dict, Any, Callable, Awaitable
from datetime import datetime, timezone
from loguru import logger

from src.database.base import db_manager
from src.database.supabase_client import SupabaseClient
from src.database.repository import ChatRepository, MessageRepository, OrderRepository, StatRepository
from src.monitoring.error_monitor import error_monitor


class DatabaseFallback:
    """Fallback механизм для сохранения данных через REST API при проблемах с прямым подключением."""
    
    def __init__(self):
        self._supabase_client: Optional[SupabaseClient] = None
    
    def _get_supabase_client(self) -> SupabaseClient:
        """Получить или создать Supabase REST API клиент."""
        if self._supabase_client is None:
            self._supabase_client = SupabaseClient()
        return self._supabase_client
    
    async def save_message_with_fallback(
        self,
        message_id: str,
        chat_id: str,
        author_id: str,
        author_name: Optional[str],
        text: str,
        timestamp: datetime,
    ) -> bool:
        """
        Сохранить сообщение с fallback на REST API.
        
        Returns:
            True если сохранено успешно, False если не удалось
        """
        # Попытка 1: Прямое подключение к БД
        if db_manager.is_initialized():
            try:
                async for session in db_manager.get_session():
                    try:
                        chat_repo = ChatRepository(session)
                        message_repo = MessageRepository(session)
                        
                        # Убедиться, что чат существует
                        chat = await chat_repo.get_by_id(chat_id)
                        if not chat:
                            # Чат будет создан автоматически при сохранении сообщения
                            # если есть foreign key constraint
                            pass
                        
                        saved_message = await message_repo.create(
                            message_id=message_id,
                            chat_id=chat_id,
                            author_id=author_id,
                            author_name=author_name,
                            text=text,
                            timestamp=timestamp,
                        )
                        
                        if saved_message:
                            await chat_repo.update_last_message_time(chat_id)
                            logger.debug(f"Message saved via direct DB: {message_id}")
                            return True
                        else:
                            logger.debug(f"Message already exists (direct DB): {message_id}")
                            return True  # Уже существует - считаем успехом
                    finally:
                        break
            except Exception as e:
                logger.warning(f"Direct DB save failed for message {message_id}: {e}, trying REST API fallback")
                error_monitor.record_error(
                    "database_save_error",
                    component="database",
                    details={"message_id": message_id, "operation": "save_message"},
                    exc=e
                )
        
        # Попытка 2: REST API fallback
        try:
            client = self._get_supabase_client()
            
            # Убедиться, что чат существует
            try:
                response = await client.client.get(f"/chats?chat_id=eq.{chat_id}&select=chat_id")
                if response.status_code == 200:
                    chats = response.json()
                    if not chats:
                        # Создать чат через REST API
                        # Нужно получить chat_name и chat_type из конфига или сообщения
                        from src.config.chat_config import chat_config_manager
                        chat_config = chat_config_manager.get_chat_config(chat_id)
                        
                        chat_name = chat_config.chat_name if chat_config else f"Chat {chat_id}"
                        chat_type = chat_config.chat_type if chat_config else "group"
                        
                        await client.client.post(
                            "/chats",
                            json={
                                "chat_id": chat_id,
                                "chat_name": chat_name[:255],
                                "chat_type": chat_type,
                                "is_active": True,
                            }
                        )
            except Exception as chat_error:
                logger.debug(f"Error ensuring chat exists: {chat_error}")
            
            # Сохранить сообщение
            response = await client.client.post(
                "/messages",
                json={
                    "message_id": message_id,
                    "chat_id": chat_id,
                    "author_id": author_id,
                    "author_name": author_name[:255] if author_name else None,
                    "text": text[:10000] if len(text) > 10000 else text,
                    "timestamp": timestamp.isoformat(),
                }
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Message saved via REST API fallback: {message_id}")
                return True
            elif response.status_code == 409:
                logger.debug(f"Message already exists (REST API): {message_id}")
                return True  # Уже существует - считаем успехом
            else:
                logger.error(f"REST API save failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"REST API fallback also failed for message {message_id}: {e}", exc_info=True)
            error_monitor.record_error(
                "rest_api_save_error",
                component="database",
                details={"message_id": message_id, "operation": "save_message_fallback"},
                exc=e
            )
            return False
    
    async def save_order_with_fallback(
        self,
        message_id: str,
        chat_id: str,
        author_id: str,
        author_name: Optional[str],
        text: str,
        category: str,
        relevance_score: float,
        detected_by: str,
        telegram_link: Optional[str] = None,
    ) -> bool:
        """
        Сохранить заказ с fallback на REST API.
        
        Returns:
            True если сохранено успешно, False если не удалось
        """
        # Попытка 1: Прямое подключение к БД
        if db_manager.is_initialized():
            try:
                async for session in db_manager.get_session():
                    try:
                        order_repo = OrderRepository(session)
                        stat_repo = StatRepository(session)
                        
                        saved_order = await order_repo.create(
                            message_id=message_id,
                            chat_id=chat_id,
                            author_id=author_id,
                            author_name=author_name,
                            text=text,
                            category=category,
                            relevance_score=relevance_score,
                            detected_by=detected_by,
                            telegram_link=telegram_link,
                        )
                        
                        if saved_order:
                            await stat_repo.update_metrics(
                                detected_orders=1,
                                regex_detections=1 if detected_by == "regex" else 0,
                                llm_detections=1 if detected_by == "llm" else 0,
                            )
                            logger.debug(f"Order saved via direct DB: {message_id}")
                            return True
                        else:
                            logger.debug(f"Order already exists (direct DB): {message_id}")
                            return True  # Уже существует - считаем успехом
                    finally:
                        break
            except Exception as e:
                logger.warning(f"Direct DB save failed for order {message_id}: {e}, trying REST API fallback")
                error_monitor.record_error(
                    "database_save_error",
                    component="database",
                    details={"message_id": message_id, "operation": "save_order"},
                    exc=e
                )
        
        # Попытка 2: REST API fallback
        try:
            client = self._get_supabase_client()
            
            # Убедиться, что чат существует
            try:
                response = await client.client.get(f"/chats?chat_id=eq.{chat_id}&select=chat_id")
                if response.status_code == 200:
                    chats = response.json()
                    if not chats:
                        # Создать чат через REST API
                        from src.config.chat_config import chat_config_manager
                        chat_config = chat_config_manager.get_chat_config(chat_id)
                        
                        chat_name = chat_config.chat_name if chat_config else f"Chat {chat_id}"
                        chat_type = chat_config.chat_type if chat_config else "group"
                        
                        await client.client.post(
                            "/chats",
                            json={
                                "chat_id": chat_id,
                                "chat_name": chat_name[:255],
                                "chat_type": chat_type,
                                "is_active": True,
                            }
                        )
            except Exception as chat_error:
                logger.debug(f"Error ensuring chat exists: {chat_error}")
            
            # Сохранить заказ
            response = await client.client.post(
                "/userbot_orders",
                json={
                    "message_id": message_id,
                    "chat_id": chat_id,
                    "author_id": author_id,
                    "author_name": author_name[:255] if author_name else None,
                    "text": text[:10000] if len(text) > 10000 else text,
                    "category": category,
                    "relevance_score": relevance_score,
                    "detected_by": detected_by,
                    "telegram_link": telegram_link[:500] if telegram_link else None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Order saved via REST API fallback: {message_id}")
                return True
            elif response.status_code == 409:
                logger.debug(f"Order already exists (REST API): {message_id}")
                return True  # Уже существует - считаем успехом
            else:
                logger.error(f"REST API save failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"REST API fallback also failed for order {message_id}: {e}", exc_info=True)
            error_monitor.record_error(
                "rest_api_save_error",
                component="database",
                details={"message_id": message_id, "operation": "save_order_fallback"},
                exc=e
            )
            return False
    
    async def close(self):
        """Закрыть соединения."""
        if self._supabase_client:
            await self._supabase_client.client.aclose()
            self._supabase_client = None


# Global instance
db_fallback = DatabaseFallback()

