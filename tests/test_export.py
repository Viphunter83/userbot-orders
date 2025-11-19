"""Unit tests for export modules."""

import pytest
from pathlib import Path
from datetime import datetime, timedelta

from src.export.filters import ExportFilter, OrderFilter, get_date_range, create_filter_for_period
from src.export.csv_exporter import CSVExporter
from src.export.html_exporter import HTMLExporter
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
            author_name="John Doe",
            text="Нужен Python разработчик",
            category="Backend",
            relevance_score=0.95,
            detected_by="regex",
            telegram_link="https://t.me/channel/123",
            created_at=now,
            exported=False,
        ),
        Order(
            id=2,
            message_id="msg_2",
            chat_id="-100123",
            author_id="user_2",
            author_name="Jane Smith",
            text="Ищем React специалиста",
            category="Frontend",
            relevance_score=0.92,
            detected_by="regex",
            telegram_link="https://t.me/channel/124",
            created_at=now - timedelta(days=1),
            exported=False,
        ),
        Order(
            id=3,
            message_id="msg_3",
            chat_id="-100456",
            author_id="user_3",
            author_name="Bob Wilson",
            text="Нужна помощь с AI интеграцией",
            category="AI/ML",
            relevance_score=0.65,
            detected_by="llm",
            telegram_link="https://t.me/channel/125",
            created_at=now - timedelta(days=5),
            exported=True,
        ),
    ]


# ============================================================================
# FILTER TESTS
# ============================================================================

class TestOrderFilter:
    """Тесты для фильтрации заказов."""
    
    def test_filter_by_category(self, sample_orders):
        """Должен фильтровать по категории."""
        filter_params = ExportFilter(categories=["Backend"])
        result = OrderFilter.apply(sample_orders, filter_params)
        
        assert len(result) == 1
        assert result[0].category == "Backend"
    
    def test_filter_by_relevance(self, sample_orders):
        """Должен фильтровать по релевантности."""
        filter_params = ExportFilter(min_relevance=0.9)
        result = OrderFilter.apply(sample_orders, filter_params)
        
        assert len(result) == 2
        assert all(o.relevance_score >= 0.9 for o in result)
    
    def test_filter_by_detection_method(self, sample_orders):
        """Должен фильтровать по методу детекции."""
        filter_params = ExportFilter(detection_methods=["llm"])
        result = OrderFilter.apply(sample_orders, filter_params)
        
        assert len(result) == 1
        assert result[0].detected_by == "llm"
    
    def test_search_text(self, sample_orders):
        """Должен выполнить полнотекстовый поиск."""
        filter_params = ExportFilter(search_text="Python")
        result = OrderFilter.apply(sample_orders, filter_params)
        
        assert len(result) == 1
        assert "Python" in result[0].text
    
    def test_filter_by_date_range(self, sample_orders):
        """Должен фильтровать по диапазону дат."""
        now = datetime.utcnow()
        filter_params = ExportFilter(
            start_date=now - timedelta(days=3),
            end_date=now,
        )
        result = OrderFilter.apply(sample_orders, filter_params)
        
        assert len(result) == 2
    
    def test_multiple_filters(self, sample_orders):
        """Должен применять несколько фильтров одновременно."""
        filter_params = ExportFilter(
            categories=["Backend", "AI/ML"],
            min_relevance=0.6,
            detection_methods=["regex"],
        )
        result = OrderFilter.apply(sample_orders, filter_params)
        
        assert len(result) == 1
        assert result[0].category == "Backend"
    
    def test_filter_only_unexported(self, sample_orders):
        """Должен фильтровать только неэкспортированные."""
        filter_params = ExportFilter(only_unexported=True)
        result = OrderFilter.apply(sample_orders, filter_params)
        
        assert len(result) == 2
        assert all(not o.exported for o in result)
    
    def test_sort_by_relevance_desc(self, sample_orders):
        """Должен сортировать по релевантности по убыванию."""
        filter_params = ExportFilter(sort_by="relevance_score", sort_order="desc")
        result = OrderFilter.apply(sample_orders, filter_params)
        
        assert len(result) == 3
        assert result[0].relevance_score >= result[1].relevance_score
        assert result[1].relevance_score >= result[2].relevance_score


class TestDateRange:
    """Тесты для функции date range."""
    
    def test_period_today(self):
        """Должен вернуть диапазон на сегодня."""
        start, end = get_date_range("today")
        
        assert start.date() == datetime.utcnow().date()
        assert end.date() == (datetime.utcnow() + timedelta(days=1)).date()
    
    def test_period_week(self):
        """Должен вернуть диапазон на неделю."""
        start, end = get_date_range("week")
        
        assert (datetime.utcnow() - start).days >= 7
        assert (end - datetime.utcnow()).days <= 1
    
    def test_period_month(self):
        """Должен вернуть диапазон на месяц."""
        start, end = get_date_range("month")
        
        assert (datetime.utcnow() - start).days >= 30
        assert (end - datetime.utcnow()).days <= 1
    
    def test_period_all(self):
        """Должен вернуть полный диапазон."""
        start, end = get_date_range("all")
        
        assert start.year == 2000
        assert end.year == 2099
    
    def test_invalid_period(self):
        """Должен выбросить ошибку для неверного периода."""
        with pytest.raises(ValueError):
            get_date_range("invalid")


class TestCreateFilterForPeriod:
    """Тесты для создания фильтра по периоду."""
    
    def test_create_filter_today(self):
        """Должен создать фильтр для сегодня."""
        filter_params = create_filter_for_period("today")
        
        assert filter_params.start_date is not None
        assert filter_params.end_date is not None
        assert filter_params.only_unexported is True


# ============================================================================
# CSV EXPORT TESTS
# ============================================================================

class TestCSVExporter:
    """Тесты для CSV экспорта."""
    
    def test_export_creates_file(self, sample_orders, tmp_path):
        """Должен создать CSV файл."""
        exporter = CSVExporter(export_dir=str(tmp_path))
        filepath = exporter.export(sample_orders, "test.csv")
        
        assert filepath.exists()
        assert filepath.suffix == ".csv"
    
    def test_export_content(self, sample_orders, tmp_path):
        """Должен содержать правильное содержимое."""
        exporter = CSVExporter(export_dir=str(tmp_path))
        filepath = exporter.export(sample_orders, "test.csv")
        
        content = filepath.read_text(encoding='utf-8-sig')
        
        assert "ID" in content
        assert "Категория" in content
        assert "Python разработчик" in content
        assert "Backend" in content
    
    def test_export_by_category(self, sample_orders, tmp_path):
        """Должен экспортировать только одну категорию."""
        exporter = CSVExporter(export_dir=str(tmp_path))
        filepath = exporter.export_by_category(sample_orders, "Backend")
        
        content = filepath.read_text(encoding='utf-8-sig')
        
        assert "Python разработчик" in content
        assert "React специалиста" not in content
    
    def test_export_auto_filename(self, sample_orders, tmp_path):
        """Должен сгенерировать имя файла автоматически."""
        exporter = CSVExporter(export_dir=str(tmp_path))
        filepath = exporter.export(sample_orders)
        
        assert "orders_" in filepath.name
        assert filepath.suffix == ".csv"
    
    def test_export_by_period(self, sample_orders, tmp_path):
        """Должен экспортировать за период."""
        exporter = CSVExporter(export_dir=str(tmp_path))
        filepath = exporter.export_by_period(sample_orders, "week")
        
        assert filepath.exists()
        assert "week" in filepath.name


# ============================================================================
# HTML EXPORT TESTS
# ============================================================================

class TestHTMLExporter:
    """Тесты для HTML экспорта."""
    
    def test_export_creates_file(self, sample_orders, tmp_path):
        """Должен создать HTML файл."""
        exporter = HTMLExporter(export_dir=str(tmp_path))
        filepath = exporter.export(sample_orders, "test.html")
        
        assert filepath.exists()
        assert filepath.suffix == ".html"
    
    def test_export_contains_table(self, sample_orders, tmp_path):
        """Должен содержать HTML таблицу."""
        exporter = HTMLExporter(export_dir=str(tmp_path))
        filepath = exporter.export(sample_orders, "test.html")
        
        content = filepath.read_text(encoding='utf-8')
        
        assert "<table" in content
        assert "<tr>" in content
        assert "Python разработчик" in content
    
    def test_export_contains_filters(self, sample_orders, tmp_path):
        """Должен содержать интерактивные фильтры."""
        exporter = HTMLExporter(export_dir=str(tmp_path))
        filepath = exporter.export(sample_orders, "test.html")
        
        content = filepath.read_text(encoding='utf-8')
        
        assert 'id="search"' in content
        assert 'id="categoryFilter"' in content
        assert 'filterTable()' in content
    
    def test_export_auto_filename(self, sample_orders, tmp_path):
        """Должен сгенерировать имя файла автоматически."""
        exporter = HTMLExporter(export_dir=str(tmp_path))
        filepath = exporter.export(sample_orders)
        
        assert "orders_" in filepath.name
        assert filepath.suffix == ".html"
    
    def test_export_empty_orders(self, tmp_path):
        """Должен обработать пустой список заказов."""
        exporter = HTMLExporter(export_dir=str(tmp_path))
        filepath = exporter.export([], "empty.html")
        
        assert filepath.exists()
        content = filepath.read_text()
        assert "0" in content
    
    def test_export_contains_stats(self, sample_orders, tmp_path):
        """Должен содержать статистику."""
        exporter = HTMLExporter(export_dir=str(tmp_path))
        filepath = exporter.export(sample_orders, "test.html")
        
        content = filepath.read_text(encoding='utf-8')
        
        assert "Всего заказов" in content
        assert "Backend" in content
        assert "Frontend" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

