"""Supabase client for database operations."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import httpx
from loguru import logger

from src.config.settings import get_settings
from src.models.order import Order, TelegramMessage, OrderAnalysis


class SupabaseClient:
    """Client for Supabase database operations."""
    
    def __init__(self):
        """Initialize Supabase client."""
        settings = get_settings()
        self.url = settings.supabase_url
        self.key = settings.supabase_key
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and key must be configured")
        
        self.client = httpx.AsyncClient(
            base_url=f"{self.url}/rest/v1",
            headers={
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation",
            },
            timeout=30.0,
        )
        logger.info(f"Supabase client initialized: {self.url}")
    
    async def health_check(self) -> bool:
        """Check if Supabase connection is healthy."""
        try:
            # Try to query a simple endpoint
            response = await self.client.get("/")
            return response.status_code < 500
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False
    
    async def insert_message(
        self,
        message: TelegramMessage,
        channel_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Insert Telegram message into database."""
        data = {
            "message_id": message.id,
            "chat_id": message.chat_id,
            "channel_name": channel_name,
            "message_text": message.message_text,
            "date": message.date.isoformat(),
            "author_id": message.author_id,
            "author_username": message.author_username,
            "is_forwarded": message.is_forwarded,
            "forwarded_from_chat_id": message.forwarded_from_chat_id,
            "has_media": message.has_media,
            "media_type": message.media_type,
            "raw_data": message.raw_data,
        }
        
        try:
            response = await self.client.post(
                "/telegram_messages",
                json=data
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Message inserted: {message.id}")
            return result[0] if isinstance(result, list) else result
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to insert message: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error inserting message: {e}")
            raise
    
    async def insert_order(
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
    ) -> Dict[str, Any]:
        """
        Insert order into database via REST API.
        
        Args match OrderRepository.create() signature for consistency.
        """
        # Структура таблицы userbot_orders:
        # message_id, chat_id, author_id, author_name, text, category, 
        # relevance_score, detected_by, telegram_link, created_at, exported, feedback, notes
        
        data = {
            "message_id": str(message_id),
            "chat_id": str(chat_id),
            "author_id": str(author_id),
            "author_name": author_name[:255] if author_name else None,
            "text": text[:10000] if len(text) > 10000 else text,
            "category": category,
            "relevance_score": float(relevance_score),
            "detected_by": detected_by,
            "telegram_link": telegram_link[:500] if telegram_link else None,
        }
        
        try:
            response = await self.client.post(
                "/userbot_orders",
                json=data
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Order inserted via REST API: {message_id}")
            return result[0] if isinstance(result, list) else result
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to insert order: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error inserting order: {e}")
            raise
    
    async def insert_order_analysis(
        self,
        message_id: int,
        chat_id: int,
        analysis: OrderAnalysis
    ) -> Dict[str, Any]:
        """Insert order analysis result."""
        data = {
            "message_id": message_id,
            "chat_id": chat_id,
            "is_order": analysis.is_order,
            "order_title": analysis.order_title,
            "description": analysis.description,
            "price": analysis.price,
            "deadline": analysis.deadline,
            "requirements": analysis.requirements,
            "contact": analysis.contact,
            "category": analysis.category,
            "confidence": analysis.confidence,
            "error": analysis.error,
            "raw_content": analysis.raw_content,
        }
        
        try:
            response = await self.client.post(
                "/order_analysis",
                json=data
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Order analysis inserted for message {message_id}")
            return result[0] if isinstance(result, list) else result
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to insert order analysis: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error inserting order analysis: {e}")
            raise
    
    async def get_orders(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get orders from database via REST API.
        
        Args:
            status: Filter by status
            limit: Maximum number of orders to return
            offset: Offset for pagination
            start_date: Filter orders created after this date
            end_date: Filter orders created before this date
        """
        params = {
            "limit": limit,
            "offset": offset,
            "order": "created_at.desc"  # Сортировка по дате создания (новые сначала)
        }
        
        if status:
            params["status"] = f"eq.{status}"
        
        # Фильтрация по датам через PostgREST
        # PostgREST требует формат ISO: YYYY-MM-DDTHH:MM:SS или YYYY-MM-DD
        # Для диапазона дат используем отдельные параметры
        if start_date:
            # Форматируем дату в ISO формат для PostgREST (только дата для простоты)
            start_str = start_date.strftime("%Y-%m-%d")
            params["created_at"] = f"gte.{start_str}"
        if end_date:
            end_str = end_date.strftime("%Y-%m-%d")
            # PostgREST поддерживает множественные фильтры через повторение параметра
            # Но лучше использовать один параметр с правильным форматом
            if "created_at" in params:
                # Используем формат: created_at=gte.2025-11-19&created_at=lte.2025-11-19
                # Но httpx может не поддерживать множественные параметры с одним именем
                # Поэтому используем формат диапазона через запятую (если поддерживается)
                # Или просто фильтруем на клиенте
                pass  # Оставим только start_date фильтр, end_date обработаем на клиенте
            else:
                params["created_at"] = f"lte.{end_str}"
        
        try:
            # Используем правильную таблицу userbot_orders
            response = await self.client.get(
                "/userbot_orders",
                params=params
            )
            response.raise_for_status()
            orders = response.json()
            
            # Фильтровать по end_date на клиенте, если нужно
            if end_date and orders:
                end_date_str = end_date.strftime("%Y-%m-%d")
                filtered_orders = []
                for order in orders:
                    order_date_str = order.get('created_at', '')
                    if order_date_str:
                        # Извлечь дату из ISO строки
                        order_date = order_date_str.split('T')[0] if 'T' in order_date_str else order_date_str.split(' ')[0]
                        if order_date <= end_date_str:
                            filtered_orders.append(order)
                return filtered_orders
            
            return orders
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get orders: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            raise
    
    async def update_order_status(
        self,
        order_id: UUID,
        status: str
    ) -> Dict[str, Any]:
        """Update order status."""
        try:
            response = await self.client.patch(
                f"/orders?id=eq.{order_id}",
                json={"status": status, "updated_at": datetime.utcnow().isoformat()}
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Order {order_id} status updated to {status}")
            return result[0] if isinstance(result, list) else result
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to update order status: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            raise
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Singleton instance
_client: Optional[SupabaseClient] = None


async def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client instance."""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client

