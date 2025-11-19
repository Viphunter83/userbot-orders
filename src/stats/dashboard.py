"""CLI Dashboard for metrics visualization."""

from typing import List, Dict
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

from src.stats.metrics import DailyMetrics, PeriodMetrics, CategoryMetrics, MetricsCalculator
from src.database.schemas import Order

console = Console()


class Dashboard:
    """CLI Dashboard для отображения метрик."""
    
    @staticmethod
    def print_header(title: str, subtitle: str = ""):
        """Печать заголовка dashboard."""
        # Не очищаем экран, чтобы не терять вывод в некоторых терминалах
        console.print(f"\n📊 {title}", style="bold cyan", justify="center")
        if subtitle:
            console.print(f"   {subtitle}", style="dim", justify="center")
        console.print()
    
    @staticmethod
    def print_daily_metrics(metrics: DailyMetrics):
        """Печать ежедневных метрик."""
        table = Table(title=f"📅 Daily Metrics - {metrics.date}", show_header=True)
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Messages", str(metrics.total_messages))
        table.add_row("Detected Orders", str(metrics.detected_orders))
        table.add_row("Detection Rate", f"{metrics.detection_rate:.1f}%")
        table.add_row("Regex Detections", str(metrics.regex_detections))
        table.add_row("LLM Detections", str(metrics.llm_detections))
        table.add_row("LLM Usage Rate", f"{metrics.llm_usage_rate:.1f}%")
        table.add_row("LLM Cost (USD)", f"${metrics.llm_cost_usd:.4f}")
        table.add_row("Cost per Order", f"${metrics.cost_per_order:.4f}")
        table.add_row("Avg Response Time", f"{metrics.avg_response_time_ms}ms")
        table.add_row("Precision", f"{metrics.precision:.1f}%")
        
        console.print(table)
    
    @staticmethod
    def print_period_metrics(metrics: PeriodMetrics):
        """Печать метрик за период."""
        title = f"📈 Period Metrics - {metrics.period_name.upper()} ({metrics.start_date.date()} to {metrics.end_date.date()})"
        table = Table(title=title, show_header=True)
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Days in Period", str(len(metrics.daily_metrics)))
        table.add_row("Total Messages", f"{metrics.total_messages:,}")
        table.add_row("Total Orders", f"{metrics.total_orders:,}")
        table.add_row("Avg Daily Orders", f"{metrics.avg_daily_orders:.1f}")
        table.add_row("Avg Detection Rate", f"{metrics.avg_detection_rate:.1f}%")
        table.add_row("Total LLM Cost", f"${metrics.total_cost_usd:.2f}")
        table.add_row("Avg Daily Cost", f"${metrics.avg_daily_cost:.2f}")
        table.add_row("Budget Remaining", f"${10.0 - metrics.total_cost_usd:.2f}")
        
        console.print(table)
    
    @staticmethod
    def print_category_breakdown(metrics_dict: Dict[str, CategoryMetrics]):
        """Печать разбивки по категориям."""
        table = Table(title="📂 Orders by Category", show_header=True)
        
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Regex", style="blue")
        table.add_column("LLM", style="yellow")
        table.add_column("Avg Relevance", style="magenta")
        
        for category, metric in sorted(
            metrics_dict.items(),
            key=lambda x: x[1].order_count,
            reverse=True,
        ):
            table.add_row(
                category,
                str(metric.order_count),
                str(metric.regex_count),
                str(metric.llm_count),
                f"{metric.avg_relevance:.2%}",
            )
        
        console.print(table)
    
    @staticmethod
    def print_top_items(items: List[tuple], title: str, max_items: int = 10):
        """Печать топ элементов."""
        table = Table(title=title, show_header=True)
        table.add_column("Rank", style="cyan")
        table.add_column("Item", style="green")
        table.add_column("Count", style="yellow")
        
        for i, (item, count) in enumerate(items[:max_items], 1):
            table.add_row(str(i), str(item), str(count))
        
        console.print(table)
    
    @staticmethod
    def print_health_status(metrics: PeriodMetrics, total_cost: float):
        """Печать статуса здоровья системы."""
        console.print("\n[bold cyan]🏥 System Health Status[/]")
        
        # Detection rate status
        avg_detection = metrics.avg_detection_rate
        detection_status = "🟢" if avg_detection > 5 else "🟡" if avg_detection > 2 else "🔴"
        console.print(f"{detection_status} Detection Rate: {avg_detection:.2f}%")
        
        # LLM budget status
        remaining = 10.0 - total_cost
        budget_status = "🟢" if remaining > 5 else "🟡" if remaining > 2 else "🔴"
        console.print(f"{budget_status} LLM Budget: ${remaining:.2f} remaining")
        
        # Daily order trend
        if len(metrics.daily_metrics) >= 2:
            last_day = metrics.daily_metrics[-1].detected_orders
            prev_day = metrics.daily_metrics[-2].detected_orders
            trend = "📈" if last_day > prev_day else "📉" if last_day < prev_day else "➡️"
            console.print(f"{trend} Daily Trend: {prev_day} → {last_day} orders")
        
        console.print()
    
    @staticmethod
    def print_full_dashboard(orders: List[Order], period: str = "week"):
        """Печать полного dashboard."""
        Dashboard.print_header("Telegram Orders Monitoring System", "Real-time Analytics")
        
        # Проверка на пустые данные
        if not orders:
            period_display = {
                "today": "сегодня",
                "week": "неделю",
                "month": "месяц",
                "all": "всё время"
            }.get(period, period)
            
            console.print(f"\n[yellow]⚠️  Нет данных за {period_display}[/]")
            console.print("\n[dim]Возможные причины:[/]")
            console.print("  • Userbot еще не обработал сообщения")
            console.print("  • Нет активных чатов в мониторинге")
            console.print("  • Заказы не были обнаружены")
            console.print("\n[cyan]💡 Рекомендации:[/]")
            console.print("  • Проверьте: [bold]python3 -m src.main chat list[/]")
            console.print("  • Проверьте работу userbot: [bold]python3 -m src.main start[/]")
            console.print("  • Попробуйте другой период: [bold]--period week[/] или [bold]--period all[/]")
            console.print()
            return
        
        # Расчитать метрики
        period_metrics = MetricsCalculator.calculate_period_metrics(orders, period)
        category_metrics = MetricsCalculator.calculate_category_metrics(orders)
        total_cost = sum(0.00015 for o in orders if o.detected_by == "llm")
        
        # Печать основных метрик
        Dashboard.print_period_metrics(period_metrics)
        console.print()
        
        # Печать по категориям (только если есть категории)
        if category_metrics:
            Dashboard.print_category_breakdown(category_metrics)
            console.print()
        
        # Печать топ элементов
        top_cats = MetricsCalculator.get_top_categories(orders, limit=5)
        if top_cats:
            Dashboard.print_top_items(top_cats, "🏆 Top Categories")
            console.print()
        
        top_authors = MetricsCalculator.get_top_authors(orders, limit=8)
        if top_authors:
            Dashboard.print_top_items(top_authors, "👥 Top Order Authors")
            console.print()
        
        # Статус здоровья
        Dashboard.print_health_status(period_metrics, total_cost)
        
        # Footer
        console.print("[dim]💡 Use 'python -m src.main stats export' to export metrics to CSV[/]")
        console.print()

