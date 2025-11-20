"""Health check и самодиагностика системы."""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger

from src.database.base import db_manager
from src.database.supabase_client import SupabaseClient
from sqlalchemy import select, text


class SystemHealthChecker:
    """Проверка работоспособности системы."""
    
    def __init__(self):
        self._supabase_client: Optional[SupabaseClient] = None
    
    def _get_supabase_client(self) -> SupabaseClient:
        """Получить или создать Supabase REST API клиент."""
        if self._supabase_client is None:
            self._supabase_client = SupabaseClient()
        return self._supabase_client
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Проверить здоровье системы.
        
        Returns:
            Словарь с информацией о состоянии компонентов
        """
        health = {
            "database": await self._check_database(),
            "telegram": await self._check_telegram(),
            "llm": await self._check_llm(),
            "storage": await self._check_storage(),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Определить общий статус
        all_ok = all(
            component.get("status") == "ok" 
            for component in health.values() 
            if isinstance(component, dict) and "status" in component
        )
        
        health["overall_status"] = "healthy" if all_ok else "unhealthy"
        
        return health
    
    async def _check_database(self) -> Dict[str, Any]:
        """Проверить подключение к БД."""
        result = {
            "status": "unknown",
            "method": None,
            "error": None,
        }
        
        # Попытка 1: Прямое подключение к PostgreSQL
        if db_manager.is_initialized():
            try:
                async for session in db_manager.get_session():
                    try:
                        # Простой запрос для проверки подключения
                        await session.execute(text("SELECT 1"))
                        result["status"] = "ok"
                        result["method"] = "direct_postgresql"
                        result["connection_pool_size"] = db_manager._engine.pool.size() if hasattr(db_manager._engine, 'pool') else None
                        return result
                    finally:
                        break
            except Exception as e:
                result["error"] = str(e)
                logger.warning(f"Direct PostgreSQL connection failed: {e}")
        
        # Попытка 2: REST API fallback
        try:
            client = self._get_supabase_client()
            is_healthy = await client.health_check()
            if is_healthy:
                result["status"] = "ok"
                result["method"] = "rest_api"
                result["warning"] = "Direct DB unavailable, using REST API"
            else:
                result["status"] = "error"
                result["error"] = "REST API health check failed"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    async def _check_telegram(self) -> Dict[str, Any]:
        """Проверить доступность Telegram API."""
        result = {
            "status": "unknown",
            "error": None,
        }
        
        try:
            # Проверка через Pyrogram (если доступен)
            from src.telegram.client import TelegramClient
            
            # Простая проверка - попытка создать клиент
            client = TelegramClient()
            # Не запускаем клиент, просто проверяем что он создается
            result["status"] = "ok"
            result["note"] = "Telegram client can be initialized"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    async def _check_llm(self) -> Dict[str, Any]:
        """Проверить доступность LLM сервиса."""
        result = {
            "status": "unknown",
            "error": None,
        }
        
        try:
            from src.config.settings import get_settings
            settings = get_settings()
            
            if not settings.proxyapi_api_key:
                result["status"] = "warning"
                result["error"] = "LLM API key not configured"
                return result
            
            # Проверка доступности через импорт (не делаем реальный запрос)
            from src.analysis.llm_classifier import llm_classifier
            
            result["status"] = "ok"
            result["provider"] = "ProxyAPI"
            result["threshold"] = llm_classifier.threshold
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    async def _check_storage(self) -> Dict[str, Any]:
        """Проверить доступность хранилища (файловая система)."""
        result = {
            "status": "unknown",
            "error": None,
        }
        
        try:
            from pathlib import Path
            
            # Проверка доступности директорий для экспорта
            export_dir = Path("./exports")
            logs_dir = Path("./logs")
            data_dir = Path("./data")
            
            directories = {
                "exports": export_dir.exists() and export_dir.is_dir(),
                "logs": logs_dir.exists() and logs_dir.is_dir(),
                "data": data_dir.exists() and data_dir.is_dir(),
            }
            
            # Попытка создать файл для проверки записи
            test_file = export_dir / ".health_check"
            try:
                test_file.touch()
                test_file.unlink()
                write_ok = True
            except Exception:
                write_ok = False
            
            if all(directories.values()) and write_ok:
                result["status"] = "ok"
                result["directories"] = directories
                result["writable"] = True
            else:
                result["status"] = "warning"
                result["directories"] = directories
                result["writable"] = write_ok
                result["error"] = "Some directories missing or not writable"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    async def get_detailed_report(self) -> str:
        """Получить детальный отчет о здоровье системы."""
        health = await self.check_health()
        
        report = []
        report.append("=" * 70)
        report.append("SYSTEM HEALTH REPORT")
        report.append("=" * 70)
        report.append(f"Timestamp: {health.get('timestamp')}")
        report.append(f"Overall Status: {health.get('overall_status', 'unknown').upper()}")
        report.append("")
        
        for component_name, component_data in health.items():
            if component_name in ["timestamp", "overall_status"]:
                continue
            
            report.append(f"📊 {component_name.upper()}")
            report.append("-" * 70)
            
            if isinstance(component_data, dict):
                status = component_data.get("status", "unknown")
                status_icon = "✅" if status == "ok" else "⚠️" if status == "warning" else "❌"
                report.append(f"Status: {status_icon} {status}")
                
                for key, value in component_data.items():
                    if key != "status":
                        report.append(f"  {key}: {value}")
            else:
                report.append(f"  {component_data}")
            
            report.append("")
        
        report.append("=" * 70)
        
        return "\n".join(report)
    
    async def close(self):
        """Закрыть соединения."""
        if self._supabase_client:
            await self._supabase_client.client.aclose()
            self._supabase_client = None


# Global instance
health_checker = SystemHealthChecker()

