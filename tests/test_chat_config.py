"""Tests for chat configuration management."""

import pytest
from datetime import datetime
from pathlib import Path
import json
import tempfile
import shutil

from src.config.chat_config import ChatConfig, ChatConfigManager


@pytest.fixture
def manager():
    """Create a fresh manager for each test."""
    ChatConfigManager._monitored_chats.clear()
    # Use temporary config file for tests
    original_file = ChatConfigManager._config_file
    temp_dir = tempfile.mkdtemp()
    ChatConfigManager._config_file = Path(temp_dir) / "chats.json"
    
    yield ChatConfigManager
    
    # Cleanup
    ChatConfigManager._monitored_chats.clear()
    ChatConfigManager._config_file = original_file
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestChatConfig:
    """Tests for ChatConfig dataclass."""
    
    def test_chat_config_creation(self):
        """Should create chat config correctly."""
        config = ChatConfig(
            chat_id="-100123456",
            chat_name="Test Group",
            chat_type="group",
            priority=3,
        )
        
        assert config.chat_id == "-100123456"
        assert config.chat_name == "Test Group"
        assert config.is_active is True
        assert config.priority == 3
    
    def test_chat_config_inactive(self):
        """Should mark chat as inactive."""
        config = ChatConfig(
            chat_id="-100123456",
            chat_name="Test Group",
            chat_type="group",
            is_active=False,
            disabled_at=datetime.utcnow(),
            reason="Testing",
        )
        
        assert config.is_active is False
        assert config.reason == "Testing"


class TestChatConfigManager:
    """Tests for ChatConfigManager."""
    
    def test_add_chat(self, manager):
        """Should add chat to monitored list."""
        config = manager.add_chat(
            "-100123456",
            "Test Group",
            "group",
            priority=3,
        )
        
        assert config.chat_id == "-100123456"
        assert config.chat_name == "Test Group"
        assert len(manager.get_all_chats()) == 1
    
    def test_remove_chat(self, manager):
        """Should disable chat monitoring."""
        manager.add_chat("-100123456", "Test", "group")
        
        result = manager.remove_chat("-100123456")
        
        assert result is True
        config = manager.get_chat_config("-100123456")
        assert config.is_active is False
    
    def test_remove_nonexistent_chat(self, manager):
        """Should return False for nonexistent chat."""
        result = manager.remove_chat("-100999999")
        
        assert result is False
    
    def test_enable_chat(self, manager):
        """Should enable disabled chat."""
        manager.add_chat("-100123456", "Test", "group")
        manager.disable_chat("-100123456")
        
        result = manager.enable_chat("-100123456")
        
        assert result is True
        config = manager.get_chat_config("-100123456")
        assert config.is_active is True
    
    def test_disable_chat(self, manager):
        """Should disable chat with reason."""
        manager.add_chat("-100123456", "Test", "group")
        
        result = manager.disable_chat("-100123456", "Testing")
        
        assert result is True
        config = manager.get_chat_config("-100123456")
        assert config.reason == "Testing"
    
    def test_set_priority(self, manager):
        """Should set chat priority."""
        manager.add_chat("-100123456", "Test", "group")
        
        result = manager.set_priority("-100123456", 5)
        
        assert result is True
        config = manager.get_chat_config("-100123456")
        assert config.priority == 5
    
    def test_set_invalid_priority(self, manager):
        """Should reject invalid priority."""
        manager.add_chat("-100123456", "Test", "group")
        
        result = manager.set_priority("-100123456", 10)
        
        assert result is False
    
    def test_get_active_chats(self, manager):
        """Should return only active chats."""
        manager.add_chat("-100111111", "Group 1", "group", priority=1)
        manager.add_chat("-100222222", "Group 2", "group", priority=2)
        manager.add_chat("-100333333", "Group 3", "group", priority=3)
        
        manager.disable_chat("-100222222")
        
        active = manager.get_active_chats()
        
        assert len(active) == 2
        assert all(c.is_active for c in active)
    
    def test_get_active_chats_sorted_by_priority(self, manager):
        """Should return active chats sorted by priority (high first)."""
        manager.add_chat("-100111111", "Low", "group", priority=1)
        manager.add_chat("-100222222", "High", "group", priority=5)
        manager.add_chat("-100333333", "Medium", "group", priority=3)
        
        active = manager.get_active_chats()
        
        assert active[0].priority == 5
        assert active[1].priority == 3
        assert active[2].priority == 1
    
    def test_is_chat_monitored(self, manager):
        """Should check if chat is monitored."""
        manager.add_chat("-100123456", "Test", "group")
        
        assert manager.is_chat_monitored("-100123456") is True
        assert manager.is_chat_monitored("-100999999") is False
    
    def test_is_inactive_chat_not_monitored(self, manager):
        """Should not monitor inactive chats."""
        manager.add_chat("-100123456", "Test", "group")
        manager.disable_chat("-100123456")
        
        assert manager.is_chat_monitored("-100123456") is False
    
    def test_get_chat_config(self, manager):
        """Should get chat config by ID."""
        manager.add_chat("-100123456", "Test", "group")
        
        config = manager.get_chat_config("-100123456")
        
        assert config is not None
        assert config.chat_name == "Test"
    
    def test_clear_all(self, manager):
        """Should clear all chats."""
        manager.add_chat("-100111111", "Group 1", "group")
        manager.add_chat("-100222222", "Group 2", "group")
        
        manager.clear_all()
        
        assert len(manager.get_all_chats()) == 0
    
    def test_multiple_chats(self, manager):
        """Should handle multiple chats."""
        chats_data = [
            ("-100111111", "Group 1", "group", 3),
            ("-100222222", "Channel 1", "channel", 5),
            ("-100333333", "Group 2", "group", 1),
        ]
        
        for chat_id, name, chat_type, priority in chats_data:
            manager.add_chat(chat_id, name, chat_type, priority)
        
        all_chats = manager.get_all_chats()
        assert len(all_chats) == 3
        
        active = manager.get_active_chats()
        assert len(active) == 3
        assert active[0].priority == 5  # Sorted by priority
    
    def test_save_and_load_config(self, manager):
        """Should save and load config from file."""
        manager.add_chat("-100111111", "Group 1", "group", priority=3)
        manager.add_chat("-100222222", "Group 2", "group", priority=5)
        
        # Save
        manager._save_to_file()
        
        # Clear and reload
        manager._monitored_chats.clear()
        manager._load_from_file()
        
        assert len(manager.get_all_chats()) == 2
        config = manager.get_chat_config("-100111111")
        assert config is not None
        assert config.chat_name == "Group 1"
        assert config.priority == 3

