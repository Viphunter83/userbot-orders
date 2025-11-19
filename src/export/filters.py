"""Export filters for orders."""

from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

from src.database.schemas import Order


@dataclass
class ExportFilter:
    """Параметры фильтрации при экспорте."""
    
    start_date: Optional[datetime] = None  # От какой даты
    end_date: Optional[datetime] = None    # До какой даты
    categories: Optional[List[str]] = None  # Какие категории (Backend, Frontend, ...)
    min_relevance: float = 0.0              # Минимальный score (0.0-1.0)
    max_relevance: float = 1.0              # Максимальный score
    detection_methods: Optional[List[str]] = None  # regex, llm, manual
    only_exported: bool = False             # Только уже экспортированные?
    only_unexported: bool = False           # Только не экспортированные?
    search_text: Optional[str] = None       # Полнотекстовый поиск
    sort_by: str = "created_at"             # Сортировать по
    sort_order: str = "desc"                # asc или desc


class OrderFilter:
    """Применять фильтры к списку заказов."""
    
    @staticmethod
    def apply(orders: List[Order], filter_params: ExportFilter) -> List[Order]:
        """
        Применить фильтры к списку заказов.
        
        Args:
            orders: Список заказов из БД
            filter_params: Параметры фильтрации
        
        Returns:
            Отфильтрованный список
        """
        result = orders.copy()
        
        # Фильтр по датам
        if filter_params.start_date:
            result = [o for o in result if o.created_at >= filter_params.start_date]
        if filter_params.end_date:
            result = [o for o in result if o.created_at <= filter_params.end_date]
        
        # Фильтр по категориям
        if filter_params.categories:
            result = [o for o in result if o.category in filter_params.categories]
        
        # Фильтр по релевантности
        result = [
            o for o in result
            if filter_params.min_relevance <= o.relevance_score <= filter_params.max_relevance
        ]
        
        # Фильтр по методу детекции
        if filter_params.detection_methods:
            result = [o for o in result if o.detected_by in filter_params.detection_methods]
        
        # Фильтр по статусу экспорта
        if filter_params.only_exported:
            result = [o for o in result if o.exported]
        if filter_params.only_unexported:
            result = [o for o in result if not o.exported]
        
        # Полнотекстовый поиск
        if filter_params.search_text:
            search_lower = filter_params.search_text.lower()
            result = [
                o for o in result
                if search_lower in o.text.lower()
                or search_lower in (o.author_name or "").lower()
                or search_lower in o.category.lower()
            ]
        
        # Сортировка
        sort_key = getattr(Order, filter_params.sort_by, Order.created_at)
        reverse = filter_params.sort_order == "desc"
        result.sort(key=lambda o: getattr(o, filter_params.sort_by), reverse=reverse)
        
        return result


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_date_range(period: str) -> tuple[datetime, datetime]:
    """
    Получить диапазон дат для периода.
    
    Args:
        period: "today", "week", "month", "all"
    
    Returns:
        Кортеж (start_date, end_date)
    """
    now = datetime.utcnow()
    
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
    elif period == "week":
        start = now - timedelta(days=7)
        end = now
    elif period == "month":
        start = now - timedelta(days=30)
        end = now
    elif period == "all":
        start = datetime(2000, 1, 1)
        end = datetime(2099, 12, 31)
    else:
        raise ValueError(f"Unknown period: {period}")
    
    return start, end


def create_filter_for_period(period: str) -> ExportFilter:
    """
    Создать фильтр для периода.
    
    Args:
        period: "today", "week", "month", "all"
    
    Returns:
        ExportFilter
    """
    start, end = get_date_range(period)
    return ExportFilter(
        start_date=start,
        end_date=end,
        only_unexported=True,  # По умолчанию только новые
    )

