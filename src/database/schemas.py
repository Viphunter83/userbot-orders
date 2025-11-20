"""SQLAlchemy ORM models for Supabase."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Text,
    Boolean,
    ForeignKey,
    Index,
    UniqueConstraint,
    BigInteger,
    CheckConstraint,
)
from sqlalchemy.orm import foreign
from sqlalchemy.orm import relationship

from src.database.base import Base


def utcnow():
    """Get current UTC datetime with timezone."""
    return datetime.now(timezone.utc)


class Chat(Base):
    """
    Таблица для отслеживаемых Telegram-чатов/каналов.
    Один чат = один источник заказов.
    """
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(50), unique=True, nullable=False, index=True)
    chat_name = Column(String(255), nullable=False)
    chat_type = Column(String(20), nullable=False)  # "group", "channel", "private"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="chat", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_chats_active_type", "is_active", "chat_type"),
    )
    
    def __repr__(self):
        return f"<Chat {self.chat_id}>"


class Message(Base):
    """
    Таблица для сохранения всех сообщений из мониторящихся чатов.
    Используется для дедупликации и аудита.
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String(50), nullable=False)
    chat_id = Column(String(50), ForeignKey("chats.chat_id"), nullable=False, index=True)
    author_id = Column(String(50), nullable=False, index=True)
    author_name = Column(String(255), nullable=True)
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    processed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    order = relationship(
        "Order", 
        back_populates="message", 
        uselist=False, 
        cascade="all, delete-orphan",
        primaryjoin="Message.message_id == foreign(Order.message_id)"
    )
    
    __table_args__ = (
        UniqueConstraint("message_id", "chat_id", name="uq_messages_id_chat"),
        Index("ix_messages_chat_timestamp", "chat_id", "timestamp"),
        Index("ix_messages_processed", "processed"),
    )
    
    def __repr__(self):
        return f"<Message {self.message_id} from {self.author_id}>"


class Order(Base):
    """
    Таблица для обнаруженных заказов.
    Ключевая таблица — именно отсюда экспортируем данные для работы.
    """
    __tablename__ = "userbot_orders"
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String(50), nullable=False, unique=True)
    chat_id = Column(String(50), ForeignKey("chats.chat_id"), nullable=False, index=True)
    author_id = Column(String(50), nullable=False, index=True)
    author_name = Column(String(255), nullable=True)
    text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)  # Backend, Frontend, AI/ML, etc
    relevance_score = Column(
        Float, 
        CheckConstraint('relevance_score >= 0 AND relevance_score <= 1'),
        nullable=False
    )  # 0.0-1.0
    detected_by = Column(String(20), nullable=False)  # "regex", "llm", "manual"
    telegram_link = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    exported = Column(Boolean, default=False, nullable=False)
    feedback = Column(String(20), nullable=True)  # "good", "bad", "duplicate"
    notes = Column(Text, nullable=True)
    
    # Relationships
    message = relationship(
        "Message", 
        back_populates="order",
        primaryjoin="Order.message_id == Message.message_id",
        foreign_keys="[Order.message_id]"
    )
    chat = relationship("Chat", back_populates="orders")
    
    __table_args__ = (
        Index("ix_orders_category_created", "category", "created_at"),
        Index("ix_orders_exported_created", "exported", "created_at"),
        Index("ix_orders_relevance", "relevance_score"),
    )
    
    def __repr__(self):
        return f"<Order {self.id} - {self.category}>"


class Stat(Base):
    """
    Таблица для хранения ежедневной статистики.
    Используется для расчёта KPI и metrics dashboard.
    """
    __tablename__ = "stats"
    
    id = Column(Integer, primary_key=True)
    date = Column(String(10), unique=True, nullable=False, index=True)  # "YYYY-MM-DD"
    total_messages = Column(Integer, default=0, nullable=False)
    detected_orders = Column(Integer, default=0, nullable=False)
    regex_detections = Column(Integer, default=0, nullable=False)
    llm_detections = Column(Integer, default=0, nullable=False)
    llm_tokens_used = Column(Integer, default=0, nullable=False)
    llm_cost = Column(Float, default=0.0, nullable=False)  # USD
    avg_response_time_ms = Column(Integer, default=0, nullable=False)
    false_positive_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Stat {self.date}>"


class ChatStat(Base):
    """
    Таблица для статистики по каждому чату.
    Используется для анализа: какой чат самый "урожайный" по заказам.
    """
    __tablename__ = "chat_stats"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(50), ForeignKey("chats.chat_id"), nullable=False, index=True)
    date = Column(String(10), nullable=False)  # "YYYY-MM-DD"
    messages_count = Column(Integer, default=0, nullable=False)
    orders_count = Column(Integer, default=0, nullable=False)
    order_percentage = Column(Float, default=0.0, nullable=False)  # % orders из всех messages
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    __table_args__ = (
        UniqueConstraint("chat_id", "date", name="uq_chat_stats_date"),
        Index("ix_chat_stats_date", "date"),
    )
    
    def __repr__(self):
        return f"<ChatStat {self.chat_id} - {self.date}>"


class Feedback(Base):
    """
    Таблица для сбора feedback от оператора.
    Используется для ML улучшения: какие заказы оператор помечает как "хорошие".
    """
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("userbot_orders.id"), nullable=False, index=True)
    feedback_type = Column(String(20), nullable=False)  # "good", "bad", "duplicate", "not_an_order"
    reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    __table_args__ = (
        Index("ix_feedback_order_type", "order_id", "feedback_type"),
    )
    
    def __repr__(self):
        return f"<Feedback {self.order_id} - {self.feedback_type}>"

