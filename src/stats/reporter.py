"""Stats reporting and CSV export."""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from loguru import logger

from src.stats.metrics import PeriodMetrics, CategoryMetrics, MetricsCalculator
from src.database.schemas import Order


class MetricsReporter:
    """Генератор отчётов по метрикам."""
    
    def __init__(self, export_dir: str = "./exports"):
        """Инициализировать reporter."""
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_daily_metrics_csv(
        self,
        metrics: PeriodMetrics,
        filename: str = None,
    ) -> Path:
        """
        Экспортировать ежедневные метрики в CSV.
        
        Args:
            metrics: PeriodMetrics объект
            filename: Имя файла
        
        Returns:
            Path к файлу
        """
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_daily_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                # Заголовки
                writer.writerow([
                    "Date",
                    "Total Messages",
                    "Detected Orders",
                    "Detection Rate %",
                    "Regex Detections",
                    "LLM Detections",
                    "LLM Cost USD",
                    "Cost per Order",
                    "Precision %",
                ])
                
                # Данные
                for metric in metrics.daily_metrics:
                    writer.writerow([
                        metric.date,
                        metric.total_messages,
                        metric.detected_orders,
                        f"{metric.detection_rate:.2f}",
                        metric.regex_detections,
                        metric.llm_detections,
                        f"{metric.llm_cost_usd:.4f}",
                        f"{metric.cost_per_order:.4f}",
                        f"{metric.precision:.2f}",
                    ])
            
            logger.info(f"✓ Daily metrics exported: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Failed to export daily metrics: {e}")
            raise
    
    def export_category_metrics_csv(
        self,
        metrics_dict: Dict[str, CategoryMetrics],
        filename: str = None,
    ) -> Path:
        """
        Экспортировать метрики по категориям.
        
        Args:
            metrics_dict: Dict[category] -> CategoryMetrics
            filename: Имя файла
        
        Returns:
            Path к файлу
        """
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_categories_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                
                writer.writerow([
                    "Category",
                    "Total Orders",
                    "Regex Detections",
                    "LLM Detections",
                    "Avg Relevance %",
                ])
                
                for category, metric in sorted(
                    metrics_dict.items(),
                    key=lambda x: x[1].order_count,
                    reverse=True,
                ):
                    writer.writerow([
                        category,
                        metric.order_count,
                        metric.regex_count,
                        metric.llm_count,
                        f"{metric.avg_relevance * 100:.2f}",
                    ])
            
            logger.info(f"✓ Category metrics exported: {filepath}")
            return filepath
        
        except Exception as e:
            logger.error(f"Failed to export category metrics: {e}")
            raise
    
    def generate_summary_report(
        self,
        orders: List[Order],
        period: str = "week",
    ) -> Dict:
        """
        Генерировать сводный отчет.
        
        Args:
            orders: Список заказов
            period: "week", "month", "all"
        
        Returns:
            Dict с ключевыми метриками
        """
        metrics = MetricsCalculator.calculate_period_metrics(orders, period)
        categories = MetricsCalculator.calculate_category_metrics(orders)
        
        return {
            "period": period,
            "date_range": {
                "start": metrics.start_date.isoformat(),
                "end": metrics.end_date.isoformat(),
            },
            "summary": {
                "total_orders": metrics.total_orders,
                "total_messages": metrics.total_messages,
                "avg_daily_orders": round(metrics.avg_daily_orders, 2),
                "detection_rate": round(metrics.avg_detection_rate, 2),
            },
            "llm": {
                "total_cost_usd": round(metrics.total_cost_usd, 2),
                "avg_daily_cost": round(metrics.avg_daily_cost, 2),
                "budget_remaining": round(10.0 - metrics.total_cost_usd, 2),
            },
            "top_categories": MetricsCalculator.get_top_categories(orders, 5),
            "top_authors": MetricsCalculator.get_top_authors(orders, 5),
        }

