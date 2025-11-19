"""Unit tests for LLM Classifier."""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

from src.analysis.llm_classifier import LLMClassifier
from src.models.llm_response import LLMClassificationResult
from src.analysis.prompts import EXAMPLE_RESPONSES


@pytest.fixture
def classifier():
    """Создать LLMClassifier для тестов."""
    return LLMClassifier()


@pytest.fixture
def mock_llm_response():
    """Mock ответ от ProxyAPI."""
    return {
        "choices": [
            {
                "message": {
                    "content": '{"is_order": true, "category": "Backend", "relevance_score": 0.95, "reason": "Test reason"}'
                }
            }
        ],
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
    }


# ============================================================================
# SINGLE CLASSIFICATION TESTS
# ============================================================================

class TestSingleClassification:
    """Тесты для одиночной классификации."""
    
    @pytest.mark.asyncio
    async def test_classify_valid_order(self, classifier):
        """Должен классифицировать валидный заказ."""
        with patch("src.analysis.llm_classifier.httpx.AsyncClient") as mock_client_class:
            # Mock успешный ответ
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": '{"is_order": true, "category": "Backend", "relevance_score": 0.95, "reason": "Явный заказ"}'
                        }
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            }
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await classifier.classify("Нужен Python разработчик")
            
            assert result is not None
            assert result.is_order is True
            assert result.category == "Backend"
            assert result.relevance_score == 0.95
    
    @pytest.mark.asyncio
    async def test_classify_not_an_order(self, classifier):
        """Должен определить что это не заказ."""
        with patch("src.analysis.llm_classifier.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": '{"is_order": false, "category": "Other", "relevance_score": 0.1, "reason": "Это просто чат"}'
                        }
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            }
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await classifier.classify("Привет, как дела?")
            
            assert result is not None
            assert result.is_order is False
    
    @pytest.mark.asyncio
    async def test_classify_empty_text(self, classifier):
        """Должен вернуть None для пустого текста."""
        result = await classifier.classify("")
        assert result is None
        
        result = await classifier.classify("  ")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_classify_ambiguous(self, classifier):
        """Должен обработать ambiguous кейс."""
        with patch("src.analysis.llm_classifier.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": '{"is_order": true, "category": "AI/ML", "relevance_score": 0.65, "reason": "Возможно заказ на автоматизацию"}'
                        }
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            }
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await classifier.classify("Нужна помощь с автоматизацией")
            
            assert result is not None
            assert 0.5 < result.relevance_score < 0.8


# ============================================================================
# BATCH CLASSIFICATION TESTS
# ============================================================================

class TestBatchClassification:
    """Тесты для batch классификации."""
    
    @pytest.mark.asyncio
    async def test_classify_batch_success(self, classifier):
        """Должен классифицировать батч сообщений."""
        with patch("src.analysis.llm_classifier.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"is_order": true, "category": "Backend", "relevance_score": 0.95, "reason": "Python dev"}\n'
                                '{"is_order": true, "category": "Frontend", "relevance_score": 0.92, "reason": "React dev"}'
                            )
                        }
                    }
                ],
                "usage": {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300},
            }
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            texts = ["Нужен Python разработчик", "Ищем React специалиста"]
            results = await classifier.classify_batch(texts)
            
            assert len(results) == 2
            assert results[0] is not None
            assert results[0].category == "Backend"
            assert results[1] is not None
            assert results[1].category == "Frontend"
    
    @pytest.mark.asyncio
    async def test_classify_batch_empty(self, classifier):
        """Должен обработать пустой batch."""
        results = await classifier.classify_batch([])
        assert results == []
    
    @pytest.mark.asyncio
    async def test_classify_batch_with_empty_texts(self, classifier):
        """Должен обработать batch с пустыми текстами."""
        texts = ["Нужен Python разработчик", "", "  ", "Ищем React специалиста"]
        with patch("src.analysis.llm_classifier.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"is_order": true, "category": "Backend", "relevance_score": 0.95, "reason": "Python"}\n'
                                '{"is_order": true, "category": "Frontend", "relevance_score": 0.92, "reason": "React"}'
                            )
                        }
                    }
                ],
                "usage": {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300},
            }
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            results = await classifier.classify_batch(texts)
            
            assert len(results) == 4
            assert results[0] is not None
            assert results[1] is None  # Пустой текст
            assert results[2] is None  # Пустой текст
            assert results[3] is not None


# ============================================================================
# CACHING TESTS
# ============================================================================

class TestCaching:
    """Тесты для кеширования."""
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, classifier):
        """Должен вернуть результат из кеша."""
        if not classifier.cache:
            pytest.skip("Caching disabled")
        
        text = "Нужен Python разработчик"
        expected_result = LLMClassificationResult(
            is_order=True,
            category="Backend",
            relevance_score=0.95,
            reason="Test"
        )
        
        # Сохранить в кеш
        classifier.cache.set(text, expected_result)
        
        # Должен вернуть из кеша без API вызова
        with patch("src.analysis.llm_classifier.httpx.AsyncClient") as mock_client:
            result = await classifier.classify(text)
            
            # API не должен быть вызван
            mock_client.assert_not_called()
            assert result == expected_result


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Тесты обработки ошибок."""
    
    @pytest.mark.asyncio
    async def test_network_error_retry(self, classifier):
        """Должен retry при сетевой ошибке."""
        with patch("src.analysis.llm_classifier.httpx.AsyncClient") as mock_client_class:
            # Первые 2 попытки fail, третья успешна
            success_response = AsyncMock()
            success_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": '{"is_order": true, "category": "Backend", "relevance_score": 0.9, "reason": "Success"}'
                        }
                    }
                ],
                "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            }
            success_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            
            # Первые 2 вызова fail, третий успешен
            mock_client.post = AsyncMock(side_effect=[
                httpx.ConnectError("Connection failed"),
                httpx.ConnectError("Connection failed"),
                success_response,
            ])
            mock_client_class.return_value = mock_client
            
            result = await classifier.classify("Test")
            
            # Должен быть результат после retry
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, classifier):
        """Должен вернуть None если все попытки неудачны."""
        with patch("src.analysis.llm_classifier.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
            mock_client_class.return_value = mock_client
            
            result = await classifier.classify("Test")
            
            # Должен вернуть None
            assert result is None


# ============================================================================
# METRICS TESTS
# ============================================================================

class TestMetrics:
    """Тесты для метрик."""
    
    def test_get_metrics(self, classifier):
        """Должен вернуть текущие метрики."""
        # Имитировать некоторые запросы
        classifier.total_requests = 5
        classifier.total_tokens_used = 750
        classifier.total_cost_usd = 0.11
        
        metrics = classifier.get_metrics()
        
        assert metrics["total_requests"] == 5
        assert metrics["total_tokens_used"] == 750
        assert metrics["total_cost_usd"] == pytest.approx(0.11)
        assert "daily_budget_usd" in metrics
        assert "budget_remaining_usd" in metrics
    
    @pytest.mark.asyncio
    async def test_budget_check(self, classifier):
        """Должен проверить остаток бюджета."""
        # Установить стоимость близко к лимиту
        classifier.total_cost_usd = 9.99
        
        # Должен вернуть True (бюджет остался)
        can_continue = await classifier.check_budget()
        assert can_continue is True
        
        # Установить стоимость выше лимита
        classifier.total_cost_usd = 10.01
        
        # Должен вернуть False (бюджет исчерпан)
        can_continue = await classifier.check_budget()
        assert can_continue is False
    
    def test_reset_daily_metrics(self, classifier):
        """Должен сбросить суточные метрики."""
        classifier.total_requests = 100
        classifier.total_tokens_used = 10000
        classifier.total_cost_usd = 1.50
        
        classifier.reset_daily_metrics()
        
        assert classifier.total_requests == 0
        assert classifier.total_tokens_used == 0
        assert classifier.total_cost_usd == 0.0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Integration тесты."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_ambiguous_to_order(self, classifier):
        """Полный workflow: ambiguous сообщение → обнаружен заказ."""
        text = "Нужна помощь с настройкой автоматизации для нашего бизнеса"
        
        with patch("src.analysis.llm_classifier.httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": '{"is_order": true, "category": "AI/ML", "relevance_score": 0.82, "reason": "Автоматизация = AI/ML"}'
                        }
                    }
                ],
                "usage": {"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
            }
            mock_response.raise_for_status = MagicMock()
            
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            result = await classifier.classify(text)
            
            # Проверить результат
            assert result is not None
            assert result.is_order is True
            assert result.category == "AI/ML"
            assert result.relevance_score >= 0.8
            
            # Проверить метрики обновились
            assert classifier.total_requests > 0
            assert classifier.total_cost_usd > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

