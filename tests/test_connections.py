"""Tests for database and LLM connections."""

import pytest
import asyncio
from src.database.supabase_client import get_supabase_client
from src.analysis.llm_client import get_llm_client
from src.utils.logger import setup_logger


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_supabase_connection():
    """Test Supabase connection."""
    setup_logger(log_level="INFO")
    client = await get_supabase_client()
    
    try:
        is_healthy = await client.health_check()
        assert is_healthy, "Supabase connection failed"
        print("✓ Supabase connection successful")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_proxyapi_connection():
    """Test ProxyAPI connection."""
    setup_logger(log_level="INFO")
    client = await get_llm_client()
    
    try:
        # Test simple chat completion
        messages = [
            {"role": "user", "content": "Привет! Ответь одним словом: работает?"}
        ]
        response = await client.chat_completion(messages, max_tokens=10)
        
        assert "choices" in response
        assert len(response["choices"]) > 0
        print("✓ ProxyAPI connection successful")
        print(f"  Response: {response['choices'][0]['message']['content']}")
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_order_analysis():
    """Test order message analysis."""
    setup_logger(log_level="INFO")
    client = await get_llm_client()
    
    try:
        test_message = """
        Нужен дизайнер для создания логотипа компании.
        Бюджет: 5000 рублей
        Срок: до 15 декабря
        Требования: опыт работы от 2 лет, портфолио с примерами логотипов
        Контакт: @designer_bot
        """
        
        analysis = await client.analyze_order_message(test_message)
        
        assert "is_order" in analysis
        print("✓ Order analysis test completed")
        print(f"  Is order: {analysis.get('is_order')}")
        if analysis.get("is_order"):
            print(f"  Title: {analysis.get('order_title')}")
            print(f"  Price: {analysis.get('price')}")
    finally:
        await client.close()

