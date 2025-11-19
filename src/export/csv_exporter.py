"""CSV export for orders."""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from loguru import logger

from src.database.schemas import Order
from src.export.filters import OrderFilter, ExportFilter


class CSVExporter:
    """Экспорт заказов в CSV формат."""
    
    # Заголовки для CSV
    HEADERS = [
        "ID",
        "Дата обнаружения",
        "Категория",
        "Релевантность",
        "Метод детекции",
        "Текст заказа",
        "Автор",
        "Чат/Канал",
        "Ссылка на сообщение",
        "Статус",
        "Примечания",
    ]
    
    def __init__(self, export_dir: str = "./exports"):
        """
        Инициализировать экспортер.
        
        Args:
            export_dir: Директория для сохранения CSV файлов
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self,
        orders: List[Order],
        filename: Optional[str] = None,
        include_filters: bool = True,
    ) -> Path:
        """
        Экспортировать заказы в CSV.
        
        Args:
            orders: Список заказов для экспорта
            filename: Имя файла (если None, генерируется автоматически)
            include_filters: Добавить ли информацию о фильтрах в начало файла
        
        Returns:
            Path к созданному файлу
        
        Example:
            exporter = CSVExporter()
            filter = ExportFilter(categories=["Backend"])
            filtered_orders = OrderFilter.apply(orders, filter)
            path = exporter.export(filtered_orders, "backend_orders.csv")
        """
        # Генерировать имя файла если не указано
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"orders_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_ALL)
                
                # Написать заголовки
                writer.writerow(self.HEADERS)
                
                # Написать данные
                for order in orders:
                    row = [
                        order.id,
                        order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        order.category,
                        f"{order.relevance_score:.2%}",  # Как процент
                        order.detected_by,
                        order.text,
                        order.author_name or "Unknown",
                        order.chat_id,
                        order.telegram_link or "N/A",
                        "✓ Exported" if order.exported else "○ Pending",
                        order.notes or "",
                    ]
                    writer.writerow(row)
            
            logger.info(
                f"✓ CSV export completed",
                extra={
                    "filename": filename,
                    "orders_count": len(orders),
                    "path": str(filepath),
                }
            )
            
            return filepath
        
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
    
    def export_by_period(self, orders: List[Order], period: str) -> Path:
        """
        Экспортировать заказы за период в отдельный файл.
        
        Args:
            orders: Все заказы
            period: "today", "week", "month"
        
        Returns:
            Path к файлу
        """
        from src.export.filters import create_filter_for_period
        
        filter_params = create_filter_for_period(period)
        filtered = OrderFilter.apply(orders, filter_params)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        filename = f"orders_{period}_{timestamp}.csv"
        
        return self.export(filtered, filename)
    
    def export_by_category(self, orders: List[Order], category: str) -> Path:
        """
        Экспортировать заказы одной категории.
        
        Args:
            orders: Все заказы
            category: Категория (Backend, Frontend, ...)
        
        Returns:
            Path к файлу
        """
        filter_params = ExportFilter(categories=[category], only_unexported=True)
        filtered = OrderFilter.apply(orders, filter_params)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        filename = f"orders_{category.lower()}_{timestamp}.csv"
        
        return self.export(filtered, filename)

