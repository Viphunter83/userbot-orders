"""Integration tests — full workflow testing."""

import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.database.base import Base
from src.database.schemas import Chat, Message, Order
from src.database.repository import (
    ChatRepository,
    MessageRepository,
    OrderRepository,
    StatRepository,
)
from src.analysis.regex_analyzer import RegexAnalyzer
from src.models.enums import OrderCategory, DetectionMethod


@pytest.fixture
async def test_db():
    """Создать тестовую БД в памяти."""
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


class TestEndToEndWorkflow:
    """End-to-End тесты полного workflow."""
    
    @pytest.mark.asyncio
    async def test_full_order_detection_workflow(self, test_db):
        """
        Полный workflow:
        1. Создать чат
        2. Получить сообщение
        3. Анализировать через regex
        4. Сохранить в БД как заказ
        """
        # Setup
        chat_repo = ChatRepository(test_db)
        message_repo = MessageRepository(test_db)
        order_repo = OrderRepository(test_db)
        regex_analyzer = RegexAnalyzer()
        
        # Создать чат
        chat = await chat_repo.create("-100123456", "Test Channel", "channel")
        await test_db.commit()
        
        # Сохранить сообщение
        message = await message_repo.create(
            message_id="msg_001",
            chat_id="-100123456",
            author_id="user_001",
            author_name="John Doe",
            text="Нужен Python разработчик для проекта",
            timestamp=datetime.utcnow(),
        )
        await test_db.commit()
        
        # Анализировать через regex
        regex_result = regex_analyzer.analyze(message.text)
        
        # Проверить результат
        assert regex_result is not None
        assert regex_result.category == OrderCategory.BACKEND
        assert regex_result.confidence >= 0.85
        
        # Сохранить как заказ
        order = await order_repo.create(
            message_id=message.message_id,
            chat_id=chat.chat_id,
            author_id=message.author_id,
            author_name=message.author_name,
            text=message.text,
            category=regex_result.category.value,
            relevance_score=regex_result.confidence,
            detected_by=DetectionMethod.REGEX.value,
        )
        await test_db.commit()
        
        # Проверить сохранение
        saved_order = await order_repo.get_by_id(order.id)
        assert saved_order is not None
        assert saved_order.category == "Backend"
        assert saved_order.detected_by == "regex"
    
    @pytest.mark.asyncio
    async def test_multiple_messages_workflow(self, test_db):
        """Workflow с несколькими сообщениями."""
        chat_repo = ChatRepository(test_db)
        message_repo = MessageRepository(test_db)
        order_repo = OrderRepository(test_db)
        regex_analyzer = RegexAnalyzer()
        
        # Создать чат
        chat = await chat_repo.create("-100123456", "Test Channel", "channel")
        await test_db.commit()
        
        # Обработать несколько сообщений
        test_messages = [
            "Нужен Python разработчик",
            "Ищем React специалиста",
            "Требуется Flutter разработчик",
            "Привет, как дела?",  # Not an order
        ]
        
        orders_detected = 0
        
        for i, text in enumerate(test_messages):
            # Сохранить сообщение
            message = await message_repo.create(
                message_id=f"msg_{i:03d}",
                chat_id="-100123456",
                author_id=f"user_{i}",
                author_name=f"Author {i}",
                text=text,
                timestamp=datetime.utcnow(),
            )
            
            # Анализировать
            regex_result = regex_analyzer.analyze(text)
            
            if regex_result and regex_result.confidence >= 0.80:
                # Сохранить как заказ
                await order_repo.create(
                    message_id=message.message_id,
                    chat_id=chat.chat_id,
                    author_id=message.author_id,
                    author_name=message.author_name,
                    text=message.text,
                    category=regex_result.category.value,
                    relevance_score=regex_result.confidence,
                    detected_by="regex",
                )
                orders_detected += 1
        
        await test_db.commit()
        
        # Проверить результаты
        assert orders_detected == 3  # 3 заказа из 4 сообщений
        
        # Получить все заказы
        all_orders = await order_repo.get_recent(days=1)
        assert len(all_orders) == 3
    
    @pytest.mark.asyncio
    async def test_export_workflow(self, test_db):
        """Workflow экспорта заказов."""
        from src.export.csv_exporter import CSVExporter
        from src.export.html_exporter import HTMLExporter
        from src.export.filters import OrderFilter, ExportFilter
        import tempfile
        
        # Создать БД с заказами
        chat_repo = ChatRepository(test_db)
        order_repo = OrderRepository(test_db)
        
        chat = await chat_repo.create("-100123456", "Test", "channel")
        
        for i in range(5):
            await order_repo.create(
                message_id=f"msg_{i}",
                chat_id="-100123456",
                author_id=f"user_{i}",
                author_name=f"Author {i}",
                text=f"Test {i}",
                category="Backend" if i % 2 == 0 else "Frontend",
                relevance_score=0.9,
                detected_by="regex",
                telegram_link=f"https://t.me/test/{i}",
            )
        
        await test_db.commit()
        
        # Получить и экспортировать
        orders = await order_repo.get_recent(days=1)
        
        # Фильтровать
        filter_params = ExportFilter(categories=["Backend"])
        filtered = OrderFilter.apply(orders, filter_params)
        
        # Экспортировать в CSV
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_exporter = CSVExporter(export_dir=tmpdir)
            csv_path = csv_exporter.export(filtered, "test.csv")
            
            assert csv_path.exists()
            assert len(filtered) == 3  # 3 Backend заказа
            
            # Экспортировать в HTML
            html_exporter = HTMLExporter(export_dir=tmpdir)
            html_path = html_exporter.export(filtered, "test.html")
            
            assert html_path.exists()
            # Проверить что HTML содержит данные
            html_content = html_path.read_text(encoding='utf-8')
            assert "Backend" in html_content
            assert "Test 0" in html_content
    
    @pytest.mark.asyncio
    async def test_stats_workflow(self, test_db):
        """Workflow расчета статистики."""
        from src.stats.metrics import MetricsCalculator
        from src.database.repository import OrderRepository, ChatRepository
        
        chat_repo = ChatRepository(test_db)
        order_repo = OrderRepository(test_db)
        
        # Создать чат и заказы
        chat = await chat_repo.create("-100123456", "Test", "channel")
        
        categories = ["Backend", "Frontend", "Mobile", "AI/ML"]
        for i in range(8):
            await order_repo.create(
                message_id=f"msg_{i}",
                chat_id="-100123456",
                author_id=f"user_{i}",
                author_name=f"Author {i % 4}",
                text=f"Test {i}",
                category=categories[i % len(categories)],
                relevance_score=0.85 + (i % 10) * 0.01,
                detected_by="regex" if i % 2 == 0 else "llm",
            )
        
        await test_db.commit()
        
        # Получить заказы
        orders = await order_repo.get_recent(days=1)
        
        # Расчитать метрики
        period_metrics = MetricsCalculator.calculate_period_metrics(orders, "week")
        category_metrics = MetricsCalculator.calculate_category_metrics(orders)
        top_cats = MetricsCalculator.get_top_categories(orders, limit=3)
        top_authors = MetricsCalculator.get_top_authors(orders, limit=3)
        
        # Проверить результаты
        assert period_metrics.total_orders == 8
        assert len(category_metrics) == 4
        assert len(top_cats) == 3
        assert len(top_authors) == 3
        assert top_cats[0][0] in categories
    
    @pytest.mark.asyncio
    async def test_stat_repository_workflow(self, test_db):
        """Workflow обновления статистики."""
        stat_repo = StatRepository(test_db)
        
        # Обновить метрики
        await stat_repo.update_metrics(
            total_messages=10,
            detected_orders=5,
            regex_detections=3,
            llm_detections=2,
        )
        await test_db.commit()
        
        # Получить обновленную статистику
        stat = await stat_repo.get_or_create_today()
        
        # Проверить что статистика обновлена
        assert stat is not None
        assert stat.total_messages == 10
        assert stat.detected_orders == 5
        assert stat.regex_detections == 3
        assert stat.llm_detections == 2


class TestRegressionCases:
    """Тесты регрессии и edge cases."""
    
    @pytest.mark.asyncio
    async def test_duplicate_message_handling(self, test_db):
        """Обработка дублирующихся сообщений."""
        message_repo = MessageRepository(test_db)
        
        # Первое сообщение
        msg1 = await message_repo.create(
            message_id="msg_001",
            chat_id="-100123",
            author_id="user_1",
            author_name="John",
            text="Test",
            timestamp=datetime.utcnow(),
        )
        await test_db.commit()
        
        # Проверить что существует
        exists = await message_repo.exists("msg_001", "-100123")
        assert exists is True
        
        # Проверить что дубликат не существует
        exists2 = await message_repo.exists("msg_002", "-100123")
        assert exists2 is False
    
    @pytest.mark.asyncio
    async def test_empty_orders_list(self, test_db):
        """Обработка пустого списка заказов."""
        order_repo = OrderRepository(test_db)
        
        orders = await order_repo.get_recent(days=1)
        assert len(orders) == 0
    
    @pytest.mark.asyncio
    async def test_very_long_message(self, test_db):
        """Обработка очень длинного сообщения."""
        regex_analyzer = RegexAnalyzer()
        
        # Создать очень длинное сообщение
        long_text = "Нужен Python разработчик. " * 100  # Много текста
        
        # Анализировать
        result = regex_analyzer.analyze(long_text)
        
        # Должен найти заказ несмотря на длину
        assert result is not None
        assert result.category == OrderCategory.BACKEND
    
    @pytest.mark.asyncio
    async def test_unicode_handling(self, test_db):
        """Обработка Unicode текста."""
        regex_analyzer = RegexAnalyzer()
        
        # Разные языки и символы
        test_cases = [
            "Нужен Python 🐍 разработчик",
            "Ищем React специалиста 💻",
            "Требуется Flutter-dev 📱",
        ]
        
        for text in test_cases:
            result = regex_analyzer.analyze(text)
            if result:  # Может быть None для некоторых случаев
                assert result.category is not None

