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
        order: Order
    ) -> Dict[str, Any]:
        """Insert order into database."""
        data = {
            "message_id": order.message_id,
            "chat_id": order.chat_id,
            "channel_name": order.channel_name,
            "order_title": order.order_title,
            "description": order.description,
            "price": order.price,
            "deadline": order.deadline,
            "requirements": order.requirements,
            "contact": order.contact,
            "category": order.category,
            "confidence": order.confidence,
            "status": order.status,
            "analysis_metadata": order.analysis_metadata,
        }
        
        try:
            response = await self.client.post(
                "/orders",
                json=data
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Order inserted: {order.order_title}")
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
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get orders from database."""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = f"eq.{status}"
        
        try:
            response = await self.client.get(
                "/orders",
                params=params
            )
            response.raise_for_status()
            return response.json()
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

