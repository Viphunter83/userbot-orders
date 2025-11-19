"""Integration tests for database layer."""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.database.base import Base
from src.database.schemas import Chat, Message, Order
from src.database.repository import ChatRepository, MessageRepository, OrderRepository


@pytest.fixture
async def test_db():
    """Создать тестовую БД в памяти (SQLite async)."""
    # Использовать SQLite для тестов (быстрее)
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_maker() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def chat_repo(test_db):
    """Создать ChatRepository с тестовой сессией."""
    return ChatRepository(test_db)


@pytest.fixture
async def message_repo(test_db):
    """Создать MessageRepository с тестовой сессией."""
    return MessageRepository(test_db)


@pytest.fixture
async def order_repo(test_db):
    """Создать OrderRepository с тестовой сессией."""
    return OrderRepository(test_db)


class TestChatRepository:
    """Тесты для ChatRepository."""
    
    @pytest.mark.asyncio
    async def test_create_chat(self, chat_repo, test_db):
        """Должен создать новый чат."""
        chat = await chat_repo.create(
            chat_id="-100123456789",
            chat_name="Test Channel",
            chat_type="channel"
        )
        await test_db.commit()
        
        assert chat.chat_id == "-100123456789"
        assert chat.chat_name == "Test Channel"
        assert chat.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, chat_repo, test_db):
        """Должен получить чат по ID."""
        await chat_repo.create(
            chat_id="-100123456789",
            chat_name="Test Channel",
        )
        await test_db.commit()
        
        chat = await chat_repo.get_by_id("-100123456789")
        assert chat is not None
        assert chat.chat_name == "Test Channel"
    
    @pytest.mark.asyncio
    async def test_get_all_active(self, chat_repo, test_db):
        """Должен получить только активные чаты."""
        await chat_repo.create("-100111", "Chat 1")
        await chat_repo.create("-100222", "Chat 2")
        await test_db.commit()
        
        await chat_repo.deactivate("-100111")
        await test_db.commit()
        
        active = await chat_repo.get_all_active()
        assert len(active) == 1
        assert active[0].chat_id == "-100222"
    
    @pytest.mark.asyncio
    async def test_deactivate(self, chat_repo, test_db):
        """Должен отключить чат."""
        chat = await chat_repo.create("-100123", "Chat")
        await test_db.commit()
        
        await chat_repo.deactivate("-100123")
        await test_db.commit()
        
        updated = await chat_repo.get_by_id("-100123")
        assert updated.is_active is False


class TestMessageRepository:
    """Тесты для MessageRepository."""
    
    @pytest.mark.asyncio
    async def test_create_message(self, message_repo, chat_repo, test_db):
        """Должен создать новое сообщение."""
        await chat_repo.create("-100123", "Channel")
        await test_db.commit()
        
        msg = await message_repo.create(
            message_id="msg_123",
            chat_id="-100123",
            author_id="user_1",
            author_name="John",
            text="Нужен Python разработчик",
            timestamp=datetime.utcnow(),
        )
        await test_db.commit()
        
        assert msg.text == "Нужен Python разработчик"
        assert msg.processed is False
    
    @pytest.mark.asyncio
    async def test_exists_deduplication(self, message_repo, chat_repo, test_db):
        """Должен определить дубликат сообщения."""
        await chat_repo.create("-100123", "Channel")
        await test_db.commit()
        
        await message_repo.create(
            message_id="msg_123",
            chat_id="-100123",
            author_id="user_1",
            author_name="John",
            text="Test",
            timestamp=datetime.utcnow(),
        )
        await test_db.commit()
        
        exists = await message_repo.exists("msg_123", "-100123")
        assert exists is True
        
        not_exists = await message_repo.exists("msg_999", "-100123")
        assert not_exists is False
    
    @pytest.mark.asyncio
    async def test_mark_processed(self, message_repo, chat_repo, test_db):
        """Должен отметить сообщение как обработанное."""
        await chat_repo.create("-100123", "Channel")
        msg = await message_repo.create(
            message_id="msg_123",
            chat_id="-100123",
            author_id="user_1",
            author_name="John",
            text="Test",
            timestamp=datetime.utcnow(),
        )
        await test_db.commit()
        
        await message_repo.mark_processed(msg.id)
        await test_db.commit()
        
        # Reload from DB
        msg = await message_repo.session.get(Message, msg.id)
        assert msg.processed is True


class TestOrderRepository:
    """Тесты для OrderRepository."""
    
    @pytest.mark.asyncio
    async def test_create_order(self, order_repo, chat_repo, message_repo, test_db):
        """Должен создать новый заказ."""
        await chat_repo.create("-100123", "Channel")
        await message_repo.create(
            message_id="msg_123",
            chat_id="-100123",
            author_id="user_1",
            author_name="John",
            text="Нужен Python разработчик",
            timestamp=datetime.utcnow(),
        )
        await test_db.commit()
        
        order = await order_repo.create(
            message_id="msg_123",
            chat_id="-100123",
            author_id="user_1",
            author_name="John",
            text="Нужен Python разработчик",
            category="Backend",
            relevance_score=0.95,
            detected_by="regex",
            telegram_link="https://t.me/channel/123",
        )
        await test_db.commit()
        
        assert order.category == "Backend"
        assert order.exported is False
    
    @pytest.mark.asyncio
    async def test_get_by_category(self, order_repo, chat_repo, message_repo, test_db):
        """Должен получить заказы по категории."""
        await chat_repo.create("-100123", "Channel")
        
        for i in range(5):
            await message_repo.create(
                message_id=f"msg_{i}",
                chat_id="-100123",
                author_id=f"user_{i}",
                author_name="User",
                text=f"Test {i}",
                timestamp=datetime.utcnow(),
            )
            category = "Backend" if i % 2 == 0 else "Frontend"
            await order_repo.create(
                message_id=f"msg_{i}",
                chat_id="-100123",
                author_id=f"user_{i}",
                author_name="User",
                text=f"Test {i}",
                category=category,
                relevance_score=0.9,
                detected_by="regex",
            )
        await test_db.commit()
        
        backend = await order_repo.get_by_category("Backend")
        assert len(backend) == 3
        
        frontend = await order_repo.get_by_category("Frontend")
        assert len(frontend) == 2
    
    @pytest.mark.asyncio
    async def test_mark_exported(self, order_repo, chat_repo, message_repo, test_db):
        """Должен отметить заказ как экспортированный."""
        await chat_repo.create("-100123", "Channel")
        await message_repo.create(
            message_id="msg_123",
            chat_id="-100123",
            author_id="user_1",
            author_name="John",
            text="Test",
            timestamp=datetime.utcnow(),
        )
        
        order = await order_repo.create(
            message_id="msg_123",
            chat_id="-100123",
            author_id="user_1",
            author_name="John",
            text="Test",
            category="Backend",
            relevance_score=0.9,
            detected_by="regex",
        )
        await test_db.commit()
        
        await order_repo.mark_exported(order.id)
        await test_db.commit()
        
        updated = await order_repo.get_by_id(order.id)
        assert updated.exported is True
    
    @pytest.mark.asyncio
    async def test_get_stats_summary(self, order_repo, chat_repo, message_repo, test_db):
        """Должен вернуть сводную статистику."""
        await chat_repo.create("-100123", "Channel")
        
        for i in range(10):
            await message_repo.create(
                message_id=f"msg_{i}",
                chat_id="-100123",
                author_id=f"user_{i}",
                author_name="User",
                text=f"Test {i}",
                timestamp=datetime.utcnow(),
            )
            category = "Backend" if i % 2 == 0 else "Frontend"
            await order_repo.create(
                message_id=f"msg_{i}",
                chat_id="-100123",
                author_id=f"user_{i}",
                author_name="User",
                text=f"Test {i}",
                category=category,
                relevance_score=0.9,
                detected_by="regex",
            )
        await test_db.commit()
        
        stats = await order_repo.get_stats_summary(days=30)
        
        assert stats["total_orders"] == 10
        assert "Backend" in stats["by_category"]
        assert "regex" in stats["by_method"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

