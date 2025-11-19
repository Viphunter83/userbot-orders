"""Metrics calculation and KPI tracking."""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger

from src.database.schemas import Order, Stat, ChatStat
from src.models.enums import OrderCategory


@dataclass
class DailyMetrics:
    """Ежедневные метрики."""
    date: str  # YYYY-MM-DD
    total_messages: int = 0
    detected_orders: int = 0
    regex_detections: int = 0
    llm_detections: int = 0
    llm_tokens_used: int = 0
    llm_cost_usd: float = 0.0
    avg_response_time_ms: int = 0
    false_positives: int = 0
    
    # Производные метрики
    @property
    def detection_rate(self) -> float:
        """% заказов из всех сообщений."""
        if self.total_messages == 0:
            return 0.0
        return (self.detected_orders / self.total_messages) * 100
    
    @property
    def llm_usage_rate(self) -> float:
        """% использования LLM из всех детекций."""
        total_detections = self.regex_detections + self.llm_detections
        if total_detections == 0:
            return 0.0
        return (self.llm_detections / total_detections) * 100
    
    @property
    def cost_per_order(self) -> float:
        """Средняя стоимость LLM на один заказ."""
        if self.llm_detections == 0:
            return 0.0
        return self.llm_cost_usd / self.llm_detections
    
    @property
    def precision(self) -> float:
        """Precision = (заказы - false_positives) / заказы."""
        if self.detected_orders == 0:
            return 0.0
        return ((self.detected_orders - self.false_positives) / self.detected_orders) * 100


@dataclass
class PeriodMetrics:
    """Метрики за период (неделя, месяц, всё время)."""
    period_name: str  # "week", "month", "all"
    start_date: datetime
    end_date: datetime
    daily_metrics: List[DailyMetrics]
    
    @property
    def total_messages(self) -> int:
        """Сумма всех сообщений за период."""
        return sum(m.total_messages for m in self.daily_metrics)
    
    @property
    def total_orders(self) -> int:
        """Сумма всех заказов за период."""
        return sum(m.detected_orders for m in self.daily_metrics)
    
    @property
    def total_cost_usd(self) -> float:
        """Сумма всех расходов LLM за период."""
        return sum(m.llm_cost_usd for m in self.daily_metrics)
    
    @property
    def avg_daily_cost(self) -> float:
        """Средняя дневная стоимость LLM."""
        days_with_cost = sum(1 for m in self.daily_metrics if m.llm_cost_usd > 0)
        if days_with_cost == 0:
            return 0.0
        return self.total_cost_usd / days_with_cost
    
    @property
    def avg_daily_orders(self) -> float:
        """Средние заказы в день."""
        if len(self.daily_metrics) == 0:
            return 0.0
        return self.total_orders / len(self.daily_metrics)
    
    @property
    def avg_detection_rate(self) -> float:
        """Средний % детекции."""
        if len(self.daily_metrics) == 0:
            return 0.0
        return sum(m.detection_rate for m in self.daily_metrics) / len(self.daily_metrics)


@dataclass
class CategoryMetrics:
    """Метрики по категориям заказов."""
    category: str
    order_count: int = 0
    regex_count: int = 0
    llm_count: int = 0
    total_relevance: float = 0.0
    
    @property
    def avg_relevance(self) -> float:
        """Средняя релевантность для категории."""
        if self.order_count == 0:
            return 0.0
        return self.total_relevance / self.order_count


class MetricsCalculator:
    """Калькулятор метрик и KPI."""
    
    @staticmethod
    def calculate_daily_metrics(
        orders: List[Order],
        date: str,
        total_messages: int = 0,
        avg_response_time_ms: int = 0,
    ) -> DailyMetrics:
        """
        Расчитать ежедневные метрики.
        
        Args:
            orders: Заказы за этот день
            date: Дата в формате YYYY-MM-DD
            total_messages: Всего сообщений за день
            avg_response_time_ms: Средний response time
        
        Returns:
            DailyMetrics
        """
        regex_count = sum(1 for o in orders if o.detected_by == "regex")
        llm_count = sum(1 for o in orders if o.detected_by == "llm")
        # Упрощённый расчёт стоимости LLM (в реальности берётся из Stat)
        llm_cost = sum(0.00015 for o in orders if o.detected_by == "llm")  # Примерная стоимость
        
        metrics = DailyMetrics(
            date=date,
            total_messages=total_messages,
            detected_orders=len(orders),
            regex_detections=regex_count,
            llm_detections=llm_count,
            llm_cost_usd=llm_cost,
            avg_response_time_ms=avg_response_time_ms,
        )
        
        return metrics
    
    @staticmethod
    def calculate_period_metrics(
        orders: List[Order],
        period_name: str = "week",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PeriodMetrics:
        """
        Расчитать метрики за период.
        
        Args:
            orders: Все заказы за период
            period_name: "week", "month", "all"
            start_date: Начало периода (если None, вычисляется)
            end_date: Конец периода (если None, сейчас)
        
        Returns:
            PeriodMetrics
        """
        # Установить дефолтные даты
        if end_date is None:
            end_date = datetime.utcnow()
        
        if start_date is None:
            if period_name == "week":
                start_date = end_date - timedelta(days=7)
            elif period_name == "month":
                start_date = end_date - timedelta(days=30)
            else:
                start_date = datetime(2000, 1, 1)
        
        # Группировать заказы по дням
        daily_dict: Dict[str, List[Order]] = {}
        for order in orders:
            date_key = order.created_at.strftime("%Y-%m-%d")
            if date_key not in daily_dict:
                daily_dict[date_key] = []
            daily_dict[date_key].append(order)
        
        # Создать DailyMetrics для каждого дня в периоде
        daily_metrics = []
        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.strftime("%Y-%m-%d")
            orders_for_day = daily_dict.get(date_key, [])
            
            regex_count = sum(1 for o in orders_for_day if o.detected_by == "regex")
            llm_count = sum(1 for o in orders_for_day if o.detected_by == "llm")
            llm_cost = sum(0.00015 for o in orders_for_day if o.detected_by == "llm")
            
            daily = DailyMetrics(
                date=date_key,
                total_messages=len(orders_for_day),  # Упрощённо
                detected_orders=len(orders_for_day),
                regex_detections=regex_count,
                llm_detections=llm_count,
                llm_cost_usd=llm_cost,
            )
            daily_metrics.append(daily)
            current_date += timedelta(days=1)
        
        return PeriodMetrics(
            period_name=period_name,
            start_date=start_date,
            end_date=end_date,
            daily_metrics=daily_metrics,
        )
    
    @staticmethod
    def calculate_category_metrics(orders: List[Order]) -> Dict[str, CategoryMetrics]:
        """
        Расчитать метрики по категориям.
        
        Args:
            orders: Список заказов
        
        Returns:
            Dict[category_name] -> CategoryMetrics
        """
        metrics = {}
        
        for order in orders:
            if order.category not in metrics:
                metrics[order.category] = CategoryMetrics(category=order.category)
            
            cat_metric = metrics[order.category]
            cat_metric.order_count += 1
            cat_metric.total_relevance += order.relevance_score
            
            if order.detected_by == "regex":
                cat_metric.regex_count += 1
            elif order.detected_by == "llm":
                cat_metric.llm_count += 1
        
        return metrics
    
    @staticmethod
    def get_top_categories(
        orders: List[Order],
        limit: int = 5,
    ) -> List[tuple[str, int]]:
        """
        Получить топ категорий по кол-во заказов.
        
        Args:
            orders: Список заказов
            limit: Макс кол-во категорий
        
        Returns:
            Список (category, count) отсортированный по count
        """
        category_counts = {}
        for order in orders:
            category_counts[order.category] = category_counts.get(order.category, 0) + 1
        
        return sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:limit]
    
    @staticmethod
    def get_top_authors(
        orders: List[Order],
        limit: int = 10,
    ) -> List[tuple[str, int]]:
        """
        Получить топ авторов заказов.
        
        Args:
            orders: Список заказов
            limit: Макс кол-во авторов
        
        Returns:
            Список (author_name, count)
        """
        author_counts = {}
        for order in orders:
            author = order.author_name or "Unknown"
            author_counts[author] = author_counts.get(author, 0) + 1
        
        return sorted(
            author_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:limit]
    
    @staticmethod
    def get_top_chats(
        orders: List[Order],
        limit: int = 10,
    ) -> List[tuple[str, int]]:
        """
        Получить топ чатов по кол-во заказов.
        
        Args:
            orders: Список заказов
            limit: Макс кол-во чатов
        
        Returns:
            Список (chat_id, count)
        """
        chat_counts = {}
        for order in orders:
            chat_counts[order.chat_id] = chat_counts.get(order.chat_id, 0) + 1
        
        return sorted(
            chat_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:limit]

