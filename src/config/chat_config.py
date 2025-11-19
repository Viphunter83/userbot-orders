"""Chat monitoring configuration and management."""

from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from datetime import datetime
from loguru import logger
import json
from pathlib import Path


@dataclass
class ChatConfig:
    """Конфигурация одного чата для мониторинга."""
    chat_id: str
    chat_name: str
    chat_type: str  # "group", "channel", "supergroup"
    is_active: bool = True
    enabled_at: Optional[datetime] = None
    disabled_at: Optional[datetime] = None
    reason: Optional[str] = None  # Причина отключения
    priority: int = 1  # 1-5, где 5 = самый важный
    
    def __repr__(self):
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.chat_name} ({self.chat_id}) [priority: {self.priority}]"


class ChatConfigManager:
    """Менеджер для управления конфигурацией чатов."""
    
    # Глобальный список отслеживаемых чатов
    _monitored_chats: Dict[str, ChatConfig] = {}
    _config_file = Path("./config/chats.json")
    
    @classmethod
    def initialize(cls):
        """Инициализировать конфиг из файла."""
        if cls._config_file.exists():
            cls._load_from_file()
            logger.info(f"✓ Loaded {len(cls._monitored_chats)} monitored chats from config")
        else:
            logger.info("No chat config file found, starting with empty list")
    
    @classmethod
    def add_chat(
        cls,
        chat_id: str,
        chat_name: str,
        chat_type: str,
        priority: int = 1,
    ) -> ChatConfig:
        """
        Добавить чат в список мониторинга.
        
        Args:
            chat_id: ID чата в Telegram
            chat_name: Имя/название чата
            chat_type: "group", "channel", "supergroup"
            priority: Приоритет (1-5)
        
        Returns:
            ChatConfig
        """
        config = ChatConfig(
            chat_id=chat_id,
            chat_name=chat_name,
            chat_type=chat_type,
            is_active=True,
            enabled_at=datetime.utcnow(),
            priority=priority,
        )
        
        cls._monitored_chats[chat_id] = config
        cls._save_to_file()
        
        logger.info(f"✓ Added chat to monitoring: {config}")
        return config
    
    @classmethod
    def remove_chat(cls, chat_id: str, reason: str = "Disabled by user") -> bool:
        """
        Отключить чат от мониторинга.
        
        Args:
            chat_id: ID чата
            reason: Причина отключения
        
        Returns:
            True если успешно, False если чата нет
        """
        if chat_id not in cls._monitored_chats:
            logger.warning(f"Chat {chat_id} not found in monitored chats")
            return False
        
        config = cls._monitored_chats[chat_id]
        config.is_active = False
        config.disabled_at = datetime.utcnow()
        config.reason = reason
        
        cls._save_to_file()
        logger.info(f"✓ Removed chat from monitoring: {config.chat_name}")
        
        return True
    
    @classmethod
    def enable_chat(cls, chat_id: str) -> bool:
        """Включить мониторинг чата."""
        if chat_id not in cls._monitored_chats:
            return False
        
        config = cls._monitored_chats[chat_id]
        config.is_active = True
        config.enabled_at = datetime.utcnow()
        config.disabled_at = None
        config.reason = None
        
        cls._save_to_file()
        logger.info(f"✓ Enabled chat monitoring: {config.chat_name}")
        return True
    
    @classmethod
    def disable_chat(cls, chat_id: str, reason: str = "") -> bool:
        """Отключить мониторинг чата (сохранив в конфиге)."""
        if chat_id not in cls._monitored_chats:
            return False
        
        config = cls._monitored_chats[chat_id]
        config.is_active = False
        config.disabled_at = datetime.utcnow()
        config.reason = reason
        
        cls._save_to_file()
        logger.info(f"✓ Disabled chat monitoring: {config.chat_name}")
        return True
    
    @classmethod
    def set_priority(cls, chat_id: str, priority: int) -> bool:
        """
        Установить приоритет чата (1-5).
        
        Args:
            chat_id: ID чата
            priority: 1-5, где 5 = наивысший приоритет
        """
        if chat_id not in cls._monitored_chats:
            return False
        
        if not 1 <= priority <= 5:
            logger.warning(f"Priority must be 1-5, got {priority}")
            return False
        
        cls._monitored_chats[chat_id].priority = priority
        cls._save_to_file()
        logger.info(f"✓ Set priority {priority} for chat {chat_id}")
        return True
    
    @classmethod
    def get_all_chats(cls) -> List[ChatConfig]:
        """Получить все чаты (активные и неактивные)."""
        return list(cls._monitored_chats.values())
    
    @classmethod
    def get_active_chats(cls) -> List[ChatConfig]:
        """Получить только активные чаты для мониторинга."""
        active = [c for c in cls._monitored_chats.values() if c.is_active]
        return sorted(active, key=lambda c: c.priority, reverse=True)
    
    @classmethod
    def is_chat_monitored(cls, chat_id: str) -> bool:
        """Проверить активен ли чат для мониторинга."""
        config = cls._monitored_chats.get(str(chat_id))
        return config is not None and config.is_active
    
    @classmethod
    def get_chat_config(cls, chat_id: str) -> Optional[ChatConfig]:
        """Получить конфиг чата."""
        return cls._monitored_chats.get(str(chat_id))
    
    @classmethod
    def clear_all(cls):
        """Очистить список всех чатов."""
        cls._monitored_chats.clear()
        cls._save_to_file()
        logger.info("✓ Cleared all monitored chats")
    
    @classmethod
    def _save_to_file(cls):
        """Сохранить конфиг в JSON файл."""
        cls._config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Конвертировать dataclass в dict
        data = {
            chat_id: {
                **asdict(config),
                "enabled_at": config.enabled_at.isoformat() if config.enabled_at else None,
                "disabled_at": config.disabled_at.isoformat() if config.disabled_at else None,
            }
            for chat_id, config in cls._monitored_chats.items()
        }
        
        with open(cls._config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def _normalize_chat_type(cls, chat_type: str) -> str:
        """
        Нормализовать тип чата из различных форматов.
        
        Args:
            chat_type: Тип чата (может быть "ChatType.SUPERGROUP", "supergroup", "SUPERGROUP" и т.д.)
        
        Returns:
            Нормализованный тип: "group", "channel", "supergroup"
        """
        if not chat_type:
            return "group"
        
        # Убрать префикс "ChatType." если есть
        normalized = chat_type.replace("ChatType.", "").lower()
        
        # Нормализовать варианты
        if normalized in ["supergroup", "super_group"]:
            return "supergroup"
        elif normalized in ["channel", "channels"]:
            return "channel"
        elif normalized in ["group", "groups"]:
            return "group"
        else:
            # По умолчанию возвращаем как есть, но логируем предупреждение
            logger.warning(f"Unknown chat_type format: {chat_type}, using as-is")
            return normalized
    
    @classmethod
    def _load_from_file(cls):
        """Загрузить конфиг из JSON файла."""
        if not cls._config_file.exists():
            return
        
        try:
            with open(cls._config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cls._monitored_chats.clear()
            
            for chat_id, config_data in data.items():
                # Нормализовать chat_type
                raw_chat_type = config_data.get('chat_type', 'group')
                normalized_chat_type = cls._normalize_chat_type(raw_chat_type)
                
                config = ChatConfig(
                    chat_id=config_data['chat_id'],
                    chat_name=config_data['chat_name'],
                    chat_type=normalized_chat_type,
                    is_active=config_data.get('is_active', True),
                    enabled_at=datetime.fromisoformat(config_data['enabled_at']) if config_data.get('enabled_at') else None,
                    disabled_at=datetime.fromisoformat(config_data['disabled_at']) if config_data.get('disabled_at') else None,
                    reason=config_data.get('reason'),
                    priority=config_data.get('priority', 1),
                )
                cls._monitored_chats[chat_id] = config
            
            logger.info(f"✓ Loaded {len(cls._monitored_chats)} chats from config (chat_types normalized)")
        
        except Exception as e:
            logger.error(f"Error loading chat config: {e}", exc_info=True)


# Global instance
chat_config_manager = ChatConfigManager()

