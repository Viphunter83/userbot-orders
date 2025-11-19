"""HTML interactive table export for orders."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from loguru import logger

from src.database.schemas import Order
from src.export.filters import OrderFilter, ExportFilter


class HTMLExporter:
    """Экспорт заказов в интерактивную HTML таблицу."""
    
    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IT Заказы — {title}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            margin: 0;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        
        h1 {{
            color: #1f33a0;
            margin-top: 0;
            margin-bottom: 10px;
        }}
        
        .meta {{
            font-size: 14px;
            color: #666;
            margin-bottom: 20px;
            border-bottom: 1px solid #eee;
            padding-bottom: 15px;
        }}
        
        .controls {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .control-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .control-group label {{
            font-weight: 500;
            font-size: 14px;
        }}
        
        input[type="text"],
        input[type="number"],
        select {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            font-family: inherit;
        }}
        
        input[type="text"]:focus,
        input[type="number"]:focus,
        select:focus {{
            outline: none;
            border-color: #1f33a0;
            box-shadow: 0 0 0 2px rgba(31, 51, 160, 0.1);
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #1f33a0;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #1f33a0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        
        thead {{
            background: #f9f9f9;
            border-bottom: 2px solid #ddd;
        }}
        
        th {{
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #333;
            cursor: pointer;
            user-select: none;
        }}
        
        th:hover {{
            background: #f0f0f0;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        
        tbody tr:hover {{
            background: #f9f9f9;
        }}
        
        .category-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-weight: 500;
            font-size: 12px;
        }}
        
        .category-backend {{
            background: #e3f2fd;
            color: #1565c0;
        }}
        
        .category-frontend {{
            background: #f3e5f5;
            color: #6a1b9a;
        }}
        
        .category-mobile {{
            background: #e0f2f1;
            color: #00695c;
        }}
        
        .category-ai_ml {{
            background: #fff3e0;
            color: #e65100;
        }}
        
        .category-low-code {{
            background: #fce4ec;
            color: #c2185b;
        }}
        
        .category-other {{
            background: #e0e0e0;
            color: #424242;
        }}
        
        .relevance {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .relevance-bar {{
            width: 60px;
            height: 6px;
            background: #ddd;
            border-radius: 3px;
            overflow: hidden;
        }}
        
        .relevance-fill {{
            height: 100%;
            background: linear-gradient(to right, #ff6b6b, #ffd93d, #6bcf7f);
            border-radius: 3px;
        }}
        
        .detection-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: 500;
        }}
        
        .detection-regex {{
            background: #e8f5e9;
            color: #2e7d32;
        }}
        
        .detection-llm {{
            background: #e1f5fe;
            color: #0277bd;
        }}
        
        .text-preview {{
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            cursor: help;
        }}
        
        .link {{
            color: #1f33a0;
            text-decoration: none;
        }}
        
        .link:hover {{
            text-decoration: underline;
        }}
        
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #999;
        }}
        
        .footer {{
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #999;
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            
            table {{
                font-size: 12px;
            }}
            
            th, td {{
                padding: 8px;
            }}
            
            .controls {{
                flex-direction: column;
                align-items: flex-start;
            }}
            
            .control-group {{
                width: 100%;
            }}
            
            input[type="text"],
            select {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 IT-Заказы из Telegram</h1>
        <div class="meta">
            <p>Отчет сгенерирован: <strong>{generated_at}</strong></p>
            <p>Всего заказов: <strong>{total_count}</strong></p>
        </div>
        
        <div class="stats">
            {stats_html}
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label for="search">🔍 Поиск:</label>
                <input type="text" id="search" placeholder="Введите текст..." onkeyup="filterTable()">
            </div>
            <div class="control-group">
                <label for="categoryFilter">📂 Категория:</label>
                <select id="categoryFilter" onchange="filterTable()">
                    <option value="">Все категории</option>
                    <option value="Backend">Backend</option>
                    <option value="Frontend">Frontend</option>
                    <option value="Mobile">Mobile</option>
                    <option value="AI/ML">AI/ML</option>
                    <option value="Low-Code">Low-Code</option>
                    <option value="Other">Other</option>
                </select>
            </div>
            <div class="control-group">
                <label for="methodFilter">🔧 Метод:</label>
                <select id="methodFilter" onchange="filterTable()">
                    <option value="">Все методы</option>
                    <option value="regex">Regex</option>
                    <option value="llm">LLM</option>
                </select>
            </div>
            <div class="control-group">
                <label for="minRelevance">📈 Мин. релевантность:</label>
                <input type="number" id="minRelevance" min="0" max="1" step="0.1" value="0" onchange="filterTable()">
            </div>
        </div>
        
        <table id="ordersTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">ID ↕</th>
                    <th onclick="sortTable(1)">Дата ↕</th>
                    <th onclick="sortTable(2)">Категория ↕</th>
                    <th onclick="sortTable(3)">Релевантность ↕</th>
                    <th onclick="sortTable(4)">Метод</th>
                    <th>Текст заказа</th>
                    <th>Автор</th>
                    <th>Ссылка</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        
        <div class="no-data" id="noData" style="display: none;">
            <p>❌ Нет заказов соответствующих вашим фильтрам</p>
        </div>
        
        <div class="footer">
            <p>💡 Совет: Нажимайте на заголовки таблицы для сортировки по столбцам.</p>
        </div>
    </div>
    
    <script>
        function filterTable() {{
            const searchInput = document.getElementById('search').value.toLowerCase();
            const categoryFilter = document.getElementById('categoryFilter').value;
            const methodFilter = document.getElementById('methodFilter').value;
            const minRelevance = parseFloat(document.getElementById('minRelevance').value) || 0;
            
            const table = document.getElementById('ordersTable');
            const rows = table.querySelectorAll('tbody tr');
            let visibleCount = 0;
            
            rows.forEach(row => {{
                const category = row.cells[2].textContent;
                const relevance = parseFloat(row.cells[3].querySelector('[data-value]')?.dataset.value || 0);
                const method = row.cells[4].textContent.toLowerCase();
                const text = row.cells[5].textContent.toLowerCase();
                const author = row.cells[6].textContent.toLowerCase();
                
                let show = true;
                
                // Фильтр поиска
                if (searchInput && !text.includes(searchInput) && !author.includes(searchInput) && !category.toLowerCase().includes(searchInput)) {{
                    show = false;
                }}
                
                // Фильтр категории
                if (categoryFilter && !category.includes(categoryFilter)) {{
                    show = false;
                }}
                
                // Фильтр метода
                if (methodFilter && !method.includes(methodFilter)) {{
                    show = false;
                }}
                
                // Фильтр релевантности
                if (relevance < minRelevance) {{
                    show = false;
                }}
                
                row.style.display = show ? '' : 'none';
                if (show) visibleCount++;
            }});
            
            document.getElementById('noData').style.display = visibleCount === 0 ? 'block' : 'none';
        }}
        
        function sortTable(colIndex) {{
            const table = document.getElementById('ordersTable');
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            
            const isAsc = table.dataset.sortCol === String(colIndex) && table.dataset.sortOrder === 'asc';
            
            rows.sort((a, b) => {{
                let aVal = a.cells[colIndex].textContent.trim();
                let bVal = b.cells[colIndex].textContent.trim();
                
                // Попытаться парсить как числа
                const aNum = parseFloat(aVal);
                const bNum = parseFloat(bVal);
                
                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    return isAsc ? bNum - aNum : aNum - bNum;
                }}
                
                return isAsc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
            }});
            
            rows.forEach(row => table.querySelector('tbody').appendChild(row));
            
            table.dataset.sortCol = String(colIndex);
            table.dataset.sortOrder = isAsc ? 'desc' : 'asc';
        }}
    </script>
</body>
</html>"""
    
    def __init__(self, export_dir: str = "./exports"):
        """Инициализировать HTML экспортер."""
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self,
        orders: List[Order],
        filename: Optional[str] = None,
    ) -> Path:
        """
        Экспортировать заказы в интерактивную HTML таблицу.
        
        Args:
            orders: Список заказов для экспорта
            filename: Имя файла (если None, генерируется автоматически)
        
        Returns:
            Path к созданному файлу
        """
        if not filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"orders_{timestamp}.html"
        
        filepath = self.export_dir / filename
        
        try:
            # Подготовить статистику
            stats_html = self._generate_stats(orders)
            
            # Подготовить строки таблицы
            table_rows = self._generate_table_rows(orders)
            
            # Заполнить шаблон
            html_content = self.HTML_TEMPLATE.format(
                title=f"Отчет ({len(orders)} заказов)",
                generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                total_count=len(orders),
                stats_html=stats_html,
                table_rows=table_rows,
            )
            
            # Сохранить файл
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(
                f"✓ HTML export completed",
                extra={
                    "filename": filename,
                    "orders_count": len(orders),
                    "path": str(filepath),
                }
            )
            
            return filepath
        
        except Exception as e:
            logger.error(f"Failed to export HTML: {e}")
            raise
    
    @staticmethod
    def _generate_stats(orders: List[Order]) -> str:
        """Генерировать HTML для статистических карточек."""
        if not orders:
            return ""
        
        # Подсчитать по категориям
        category_counts = {}
        method_counts = {}
        
        for order in orders:
            category_counts[order.category] = category_counts.get(order.category, 0) + 1
            method_counts[order.detected_by] = method_counts.get(order.detected_by, 0) + 1
        
        # Средняя релевантность
        avg_relevance = sum(o.relevance_score for o in orders) / len(orders)
        
        stats = f"""
        <div class="stat-card">
            <div class="stat-label">Всего заказов</div>
            <div class="stat-value">{len(orders)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Средняя релевантность</div>
            <div class="stat-value">{avg_relevance:.1%}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Backend</div>
            <div class="stat-value">{category_counts.get('Backend', 0)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Frontend</div>
            <div class="stat-value">{category_counts.get('Frontend', 0)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">AI/ML</div>
            <div class="stat-value">{category_counts.get('AI/ML', 0)}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Regex детекция</div>
            <div class="stat-value">{method_counts.get('regex', 0)}</div>
        </div>
        """
        
        return stats
    
    @staticmethod
    def _generate_table_rows(orders: List[Order]) -> str:
        """Генерировать HTML для строк таблицы."""
        rows = []
        
        for order in orders:
            category_class = f"category-{order.category.lower().replace('/', '_').replace('-', '-')}"
            detection_class = f"detection-{order.detected_by}"
            
            row_html = f"""
            <tr>
                <td>{order.id}</td>
                <td>{order.created_at.strftime("%Y-%m-%d %H:%M")}</td>
                <td><span class="category-badge {category_class}">{order.category}</span></td>
                <td>
                    <div class="relevance">
                        <div class="relevance-bar">
                            <div class="relevance-fill" style="width: {order.relevance_score * 100}%"></div>
                        </div>
                        <span data-value="{order.relevance_score}">{order.relevance_score:.0%}</span>
                    </div>
                </td>
                <td><span class="detection-badge {detection_class}">{order.detected_by}</span></td>
                <td><div class="text-preview" title="{order.text.replace('"', '&quot;')}">{order.text[:100]}{'...' if len(order.text) > 100 else ''}</div></td>
                <td>{order.author_name or "Unknown"}</td>
                <td>
                    {f'<a href="{order.telegram_link}" class="link" target="_blank">📱</a>' if order.telegram_link else "N/A"}
                </td>
            </tr>
            """
            rows.append(row_html)
        
        return "\n".join(rows)

