"""Repository pattern for database access."""

from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.database.schemas import Chat, Message, Order, Stat, ChatStat, Feedback
from src.models.enums import OrderCategory, DetectionMethod


class ChatRepository:
    """Repository для работы с таблицей chats."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, chat_id: str, chat_name: str, chat_type: str = "group") -> Chat:
        """
        Добавить новый чат в мониторинг.
        
        Returns:
            Chat если создан успешно или уже существует
        
        Raises:
            IntegrityError если произошла другая ошибка целостности данных
        """
        # Проверить существование чата перед созданием
        existing_chat = await self.get_by_id(chat_id)
        if existing_chat:
            logger.debug(f"Chat already exists: {chat_id}, returning existing")
            return existing_chat
        
        try:
            chat = Chat(chat_id=chat_id, chat_name=chat_name, chat_type=chat_type)
            self.session.add(chat)
            await self.session.flush()
            logger.info(f"Chat created: {chat_id}")
            return chat
        except IntegrityError as e:
            # Обработать race condition: чат был создан между проверкой и вставкой
            await self.session.rollback()
            logger.warning(f"IntegrityError creating chat (likely duplicate): {chat_id}, attempting to fetch existing")
            existing_chat = await self.get_by_id(chat_id)
            if existing_chat:
                logger.debug(f"Found existing chat: {chat_id}")
                return existing_chat
            # Если не удалось получить, пробросить ошибку дальше
            logger.error(f"Failed to create or fetch chat: {chat_id}, error: {e}")
            raise
    
    async def get_by_id(self, chat_id: str) -> Optional[Chat]:
        """Получить чат по ID."""
        stmt = select(Chat).where(Chat.chat_id == chat_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_active(self) -> List[Chat]:
        """Получить все активные чаты."""
        stmt = select(Chat).where(Chat.is_active == True).order_by(Chat.created_at)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def deactivate(self, chat_id: str) -> None:
        """Отключить мониторинг чата."""
        chat = await self.get_by_id(chat_id)
        if chat:
            chat.is_active = False
            await self.session.flush()
            logger.info(f"Chat deactivated: {chat_id}")
    
    async def update_last_message_time(self, chat_id: str) -> None:
        """Обновить время последнего сообщения."""
        chat = await self.get_by_id(chat_id)
        if chat:
            chat.last_message_at = datetime.utcnow()
            await self.session.flush()


class MessageRepository:
    """Repository для работы с таблицей messages."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        message_id: str,
        chat_id: str,
        author_id: str,
        author_name: Optional[str],
        text: str,
        timestamp: datetime,
    ) -> Optional[Message]:
        """
        Создать новое сообщение.
        
        Returns:
            Message если создано успешно, None если сообщение уже существует (дубликат)
        
        Raises:
            IntegrityError если произошла другая ошибка целостности данных
        """
        # Проверить существование сообщения перед созданием (защита от race condition)
        if await self.exists(message_id, chat_id):
            logger.debug(f"Message already exists: {message_id} in chat {chat_id}")
            return None
        
        try:
            message = Message(
                message_id=message_id,
                chat_id=chat_id,
                author_id=author_id,
                author_name=author_name,
                text=text,
                timestamp=timestamp,
            )
            self.session.add(message)
            await self.session.flush()
            return message
        except IntegrityError as e:
            # Обработать race condition: сообщение было создано между проверкой и вставкой
            await self.session.rollback()
            logger.warning(f"IntegrityError creating message (likely duplicate): {message_id} in chat {chat_id}")
            # Сообщение уже существует, это нормально
            return None
    
    async def exists(self, message_id: str, chat_id: str) -> bool:
        """Проверить существование сообщения (дедупликация)."""
        stmt = select(func.count()).select_from(Message).where(
            and_(Message.message_id == message_id, Message.chat_id == chat_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar() > 0
    
    async def get_unprocessed(self, limit: int = 100) -> List[Message]:
        """Получить необработанные сообщения."""
        stmt = (
            select(Message)
            .where(Message.processed == False)
            .order_by(Message.timestamp)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def mark_processed(self, message_id: int) -> None:
        """Отметить сообщение как обработанное."""
        message = await self.session.get(Message, message_id)
        if message:
            message.processed = True
            await self.session.flush()


class OrderRepository:
    """Repository для работы с таблицей orders."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def exists(self, message_id: str) -> bool:
        """Проверить существование заказа по message_id (дедупликация)."""
        stmt = select(func.count()).select_from(Order).where(
            Order.message_id == message_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() > 0
    
    async def get_by_message_id(self, message_id: str) -> Optional[Order]:
        """Получить заказ по message_id."""
        stmt = select(Order).where(Order.message_id == message_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create(
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
    ) -> Optional[Order]:
        """
        Создать новый обнаруженный заказ.
        
        Returns:
            Order если создан успешно, None если заказ уже существует (дубликат)
        
        Raises:
            IntegrityError если произошла другая ошибка целостности данных
        """
        # Проверить существование заказа перед созданием (защита от race condition)
        if await self.exists(message_id):
            logger.debug(f"Order already exists for message_id: {message_id}, skipping duplicate")
            return await self.get_by_message_id(message_id)
        
        try:
            order = Order(
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
            self.session.add(order)
            await self.session.flush()
            logger.info(f"Order created: {category} from {author_id}")
            return order
        except IntegrityError as e:
            # Обработать случай когда заказ был создан между проверкой и вставкой (race condition)
            await self.session.rollback()
            logger.warning(f"IntegrityError creating order (likely duplicate): {message_id}, attempting to fetch existing")
            # Попытаться получить существующий заказ
            existing_order = await self.get_by_message_id(message_id)
            if existing_order:
                logger.debug(f"Found existing order for message_id: {message_id}")
                return existing_order
            # Если не удалось получить, пробросить ошибку дальше
            logger.error(f"Failed to create or fetch order for message_id: {message_id}, error: {e}")
            raise
    
    async def get_by_id(self, order_id: int) -> Optional[Order]:
        """Получить заказ по ID."""
        return await self.session.get(Order, order_id)
    
    async def get_recent(self, days: int = 7, limit: int = 100) -> List[Order]:
        """Получить последние заказы за N дней."""
        since = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(Order)
            .where(Order.created_at >= since)
            .order_by(desc(Order.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_category(self, category: str, limit: int = 50) -> List[Order]:
        """Получить заказы по категории."""
        stmt = (
            select(Order)
            .where(Order.category == category)
            .order_by(desc(Order.created_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_unexported(self, limit: int = 100) -> List[Order]:
        """Получить необработанные (неэкспортированные) заказы."""
        stmt = (
            select(Order)
            .where(Order.exported == False)
            .order_by(Order.created_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def mark_exported(self, order_id: int) -> None:
        """Отметить заказ как экспортированный."""
        order = await self.get_by_id(order_id)
        if order:
            order.exported = True
            await self.session.flush()
    
    async def add_feedback(self, order_id: int, feedback_type: str, reason: Optional[str] = None) -> None:
        """Добавить feedback от оператора."""
        feedback = Feedback(order_id=order_id, feedback_type=feedback_type, reason=reason)
        self.session.add(feedback)
        await self.session.flush()
        logger.info(f"Feedback added: Order {order_id} - {feedback_type}")
    
    async def get_stats_summary(self, days: int = 30) -> dict:
        """Получить сводную статистику по заказам."""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Всего заказов
        stmt_total = select(func.count()).select_from(Order).where(Order.created_at >= since)
        total_orders = await self.session.execute(stmt_total)
        total = total_orders.scalar() or 0
        
        # По категориям
        stmt_by_category = (
            select(Order.category, func.count().label("count"))
            .where(Order.created_at >= since)
            .group_by(Order.category)
            .order_by(desc("count"))
        )
        category_result = await self.session.execute(stmt_by_category)
        by_category = {row[0]: row[1] for row in category_result}
        
        # По методу детекции
        stmt_by_method = (
            select(Order.detected_by, func.count().label("count"))
            .where(Order.created_at >= since)
            .group_by(Order.detected_by)
        )
        method_result = await self.session.execute(stmt_by_method)
        by_method = {row[0]: row[1] for row in method_result}
        
        return {
            "total_orders": total,
            "by_category": by_category,
            "by_method": by_method,
            "period_days": days,
        }


class StatRepository:
    """Repository для работы с таблицей stats."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_or_create_today(self) -> Stat:
        """Получить или создать stat для сегодняшнего дня."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        stmt = select(Stat).where(Stat.date == today)
        result = await self.session.execute(stmt)
        stat = result.scalar_one_or_none()
        
        if not stat:
            stat = Stat(date=today)
            self.session.add(stat)
            await self.session.flush()
        
        return stat
    
    async def update_metrics(
        self,
        total_messages: Optional[int] = None,
        detected_orders: Optional[int] = None,
        regex_detections: Optional[int] = None,
        llm_detections: Optional[int] = None,
        llm_tokens_used: Optional[int] = None,
        llm_cost: Optional[float] = None,
        avg_response_time_ms: Optional[int] = None,
    ) -> None:
        """Обновить метрики за сегодня."""
        stat = await self.get_or_create_today()
        
        if total_messages is not None:
            stat.total_messages += total_messages
        if detected_orders is not None:
            stat.detected_orders += detected_orders
        if regex_detections is not None:
            stat.regex_detections += regex_detections
        if llm_detections is not None:
            stat.llm_detections += llm_detections
        if llm_tokens_used is not None:
            stat.llm_tokens_used += llm_tokens_used
        if llm_cost is not None:
            stat.llm_cost += llm_cost
        if avg_response_time_ms is not None:
            stat.avg_response_time_ms = avg_response_time_ms
        
        await self.session.flush()

