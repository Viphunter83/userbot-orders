"""Unit tests for stats modules."""

import pytest
from datetime import datetime, timedelta

from src.stats.metrics import (
    DailyMetrics,
    PeriodMetrics,
    CategoryMetrics,
    MetricsCalculator,
)
from src.database.schemas import Order


@pytest.fixture
def sample_orders():
    """Создать тестовые заказы."""
    now = datetime.utcnow()
    return [
        Order(
            id=1,
            message_id="msg_1",
            chat_id="-100123",
            author_id="user_1",
            author_name="John",
            text="Test 1",
            category="Backend",
            relevance_score=0.95,
            detected_by="regex",
            telegram_link="https://t.me/test/1",
            created_at=now,
            exported=False,
        ),
        Order(
            id=2,
            message_id="msg_2",
            chat_id="-100123",
            author_id="user_2",
            author_name="Jane",
            text="Test 2",
            category="Backend",
            relevance_score=0.92,
            detected_by="regex",
            telegram_link="https://t.me/test/2",
            created_at=now - timedelta(days=1),
            exported=False,
        ),
        Order(
            id=3,
            message_id="msg_3",
            chat_id="-100456",
            author_id="user_3",
            author_name="Bob",
            text="Test 3",
            category="Frontend",
            relevance_score=0.85,
            detected_by="llm",
            telegram_link="https://t.me/test/3",
            created_at=now - timedelta(days=5),
            exported=False,
        ),
    ]


class TestDailyMetrics:
    """Тесты для DailyMetrics."""
    
    def test_detection_rate(self):
        """Должен правильно считать detection rate."""
        metrics = DailyMetrics(
            date="2025-11-19",
            total_messages=100,
            detected_orders=5,
        )
        
        assert metrics.detection_rate == 5.0
    
    def test_llm_usage_rate(self):
        """Должен считать % использования LLM."""
        metrics = DailyMetrics(
            date="2025-11-19",
            regex_detections=8,
            llm_detections=2,
        )
        
        assert metrics.llm_usage_rate == 20.0
    
    def test_precision(self):
        """Должен считать precision."""
        metrics = DailyMetrics(
            date="2025-11-19",
            detected_orders=10,
            false_positives=2,
        )
        
        assert metrics.precision == 80.0
    
    def test_cost_per_order(self):
        """Должен считать стоимость на заказ."""
        metrics = DailyMetrics(
            date="2025-11-19",
            llm_detections=5,
            llm_cost_usd=0.0015,
        )
        
        assert metrics.cost_per_order == pytest.approx(0.0003)


class TestMetricsCalculator:
    """Тесты для MetricsCalculator."""
    
    def test_calculate_daily_metrics(self, sample_orders):
        """Должен правильно посчитать daily metrics."""
        metrics = MetricsCalculator.calculate_daily_metrics(
            sample_orders[:2],  # 2 regex заказа
            "2025-11-19",
            total_messages=50,
        )
        
        assert metrics.detected_orders == 2
        assert metrics.regex_detections == 2
        assert metrics.llm_detections == 0
    
    def test_calculate_period_metrics(self, sample_orders):
        """Должен расчитать period metrics."""
        metrics = MetricsCalculator.calculate_period_metrics(
            sample_orders,
            "week",
        )
        
        assert metrics.total_orders == 3
        assert metrics.period_name == "week"
        assert len(metrics.daily_metrics) > 0
    
    def test_calculate_category_metrics(self, sample_orders):
        """Должен расчитать category metrics."""
        metrics = MetricsCalculator.calculate_category_metrics(sample_orders)
        
        assert "Backend" in metrics
        assert metrics["Backend"].order_count == 2
        assert metrics["Backend"].regex_count == 2
        
        assert "Frontend" in metrics
        assert metrics["Frontend"].order_count == 1
        assert metrics["Frontend"].llm_count == 1
    
    def test_get_top_categories(self, sample_orders):
        """Должен вернуть топ категорий."""
        top = MetricsCalculator.get_top_categories(sample_orders, limit=2)
        
        assert len(top) <= 2
        assert top[0][0] == "Backend"  # Backend на вершине (2 заказа)
        assert top[0][1] == 2
    
    def test_get_top_authors(self, sample_orders):
        """Должен вернуть топ авторов."""
        top = MetricsCalculator.get_top_authors(sample_orders, limit=3)
        
        assert len(top) == 3
        assert all(isinstance(item, tuple) for item in top)
    
    def test_get_top_chats(self, sample_orders):
        """Должен вернуть топ чатов."""
        top = MetricsCalculator.get_top_chats(sample_orders, limit=2)
        
        assert len(top) <= 2
        assert "-100123" in [chat for chat, _ in top]


class TestPeriodMetrics:
    """Тесты для PeriodMetrics."""
    
    def test_total_properties(self, sample_orders):
        """Должны правильно считаться total свойства."""
        metrics = MetricsCalculator.calculate_period_metrics(sample_orders, "week")
        
        assert metrics.total_orders == 3
        assert metrics.avg_daily_orders > 0
    
    def test_cost_calculations(self, sample_orders):
        """Должны правильно считаться стоимости."""
        metrics = MetricsCalculator.calculate_period_metrics(sample_orders, "week")
        
        assert metrics.total_cost_usd >= 0
        assert metrics.avg_daily_cost >= 0
    
    def test_avg_detection_rate(self, sample_orders):
        """Должен правильно считать средний detection rate."""
        metrics = MetricsCalculator.calculate_period_metrics(sample_orders, "week")
        
        assert metrics.avg_detection_rate >= 0


class TestCategoryMetrics:
    """Тесты для CategoryMetrics."""
    
    def test_avg_relevance(self):
        """Должен правильно считать среднюю релевантность."""
        metric = CategoryMetrics(
            category="Backend",
            order_count=2,
            total_relevance=1.87,  # 0.95 + 0.92
        )
        
        assert metric.avg_relevance == pytest.approx(0.935)
    
    def test_empty_category(self):
        """Должен обработать пустую категорию."""
        metric = CategoryMetrics(category="Test", order_count=0)
        
        assert metric.avg_relevance == 0.0

