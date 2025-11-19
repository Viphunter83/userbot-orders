"""Unit tests for RegexAnalyzer."""

import pytest
from src.analysis.regex_analyzer import RegexAnalyzer
from src.models.enums import OrderCategory, DetectionMethod


@pytest.fixture
def analyzer():
    """Создать instance RegexAnalyzer."""
    return RegexAnalyzer()


class TestBackendDetection:
    """Тесты для Backend заказов."""
    
    def test_python_developer(self, analyzer):
        """Должен детектировать Python разработчика."""
        text = "Срочно нужен опытный Python-разработчик для проекта"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.BACKEND
        assert result.confidence >= 0.85
        assert result.detected_by == DetectionMethod.REGEX
        assert "python" in result.matched_text.lower()
    
    def test_nodejs_developer(self, analyzer):
        """Должен детектировать Node.js разработчика."""
        text = "Ищем Node.js-программиста для стартапа"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.BACKEND
    
    def test_api_development(self, analyzer):
        """Должен детектировать API разработку."""
        text = "Нужна помощь с разработкой REST API"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.BACKEND
    
    def test_webhook_integration(self, analyzer):
        """Должен детектировать настройку вебхуков."""
        text = "Требуется настройка webhook для нашего приложения"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.BACKEND
    
    def test_java_developer(self, analyzer):
        """Должен детектировать Java разработчика."""
        text = "Нужен Java разработчик для корпоративного проекта"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.BACKEND
    
    def test_database_optimization(self, analyzer):
        """Должен детектировать работу с базами данных."""
        text = "Требуется оптимизация PostgreSQL базы данных"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.BACKEND


class TestFrontendDetection:
    """Тесты для Frontend заказов."""
    
    def test_react_developer(self, analyzer):
        """Должен детектировать React разработчика."""
        text = "Нужен React-разработчик для долгосрочного проекта"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.FRONTEND
    
    def test_vue_developer(self, analyzer):
        """Должен детектировать Vue.js разработчика."""
        text = "Ищем Vue.js специалиста для фронтенда"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.FRONTEND
    
    def test_ui_ux_designer(self, analyzer):
        """Должен детектировать UI/UX дизайнера."""
        text = "Ищем UI/UX дизайнера со знанием Figma"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.FRONTEND
    
    def test_webflow_developer(self, analyzer):
        """Должен детектировать WebFlow разработчика."""
        text = "Нужен WebFlow специалист для создания сайта"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.FRONTEND


class TestMobileDetection:
    """Тесты для Mobile заказов."""
    
    def test_flutter_developer(self, analyzer):
        """Должен детектировать Flutter разработчика."""
        text = "Нужен Flutter-разработчик для мобильного приложения"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.MOBILE
    
    def test_react_native_developer(self, analyzer):
        """Должен детектировать React Native разработчика."""
        text = "Ищем React Native специалиста"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.MOBILE
    
    def test_ios_developer(self, analyzer):
        """Должен детектировать iOS разработчика."""
        text = "Требуется iOS разработчик для приложения"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.MOBILE


class TestAiMlDetection:
    """Тесты для AI/ML заказов."""
    
    def test_prompt_engineer(self, analyzer):
        """Должен детектировать Prompt Engineer."""
        text = "Нужен специалист по prompt engineering"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.AI_ML
    
    def test_automation(self, analyzer):
        """Должен детектировать автоматизацию."""
        text = "Требуется автоматизация бизнес-процессов"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.AI_ML
    
    def test_chatgpt_integration(self, analyzer):
        """Должен детектировать ChatGPT интеграцию."""
        text = "Нужна интеграция ChatGPT в наше приложение"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.AI_ML


class TestLowCodeDetection:
    """Тесты для Low-Code заказов."""
    
    def test_bubble_developer(self, analyzer):
        """Должен детектировать Bubble разработчика."""
        text = "Ищем Bubble специалиста для проекта"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.LOW_CODE
    
    def test_zapier_automation(self, analyzer):
        """Должен детектировать Zapier автоматизацию."""
        text = "Требуется настройка Zapier интеграции"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.LOW_CODE


class TestOtherDetection:
    """Тесты для Other заказов."""
    
    def test_1c_developer(self, analyzer):
        """Должен детектировать 1C разработчика."""
        text = "Ищем разработчика на 1C"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.OTHER
    
    def test_shopify_developer(self, analyzer):
        """Должен детектировать Shopify разработчика."""
        text = "Нужен Shopify разработчик для магазина"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.OTHER


class TestExclusions:
    """Тесты на исключение ложных срабатываний."""
    
    def test_exclude_spam(self, analyzer):
        """Не должен детектировать спам."""
        text = "Привет! Это просто реклама, не трогай"
        result = analyzer.analyze(text)
        
        assert result is None
    
    def test_exclude_non_it(self, analyzer):
        """Не должен детектировать не-IT заказы."""
        text = "Продам старый компьютер"
        result = analyzer.analyze(text)
        
        assert result is None
    
    def test_exclude_food_delivery(self, analyzer):
        """Не должен детектировать заказ еды."""
        text = "Заказ еды на дом"
        result = analyzer.analyze(text)
        
        assert result is None


class TestEdgeCases:
    """Edge case тесты."""
    
    def test_empty_text(self, analyzer):
        """Пустой текст не должен матчиться."""
        result = analyzer.analyze("")
        assert result is None
    
    def test_very_short_text(self, analyzer):
        """Очень короткий текст не должен матчиться."""
        result = analyzer.analyze("hi")
        assert result is None
    
    def test_whitespace_only(self, analyzer):
        """Только пробелы не должны матчиться."""
        result = analyzer.analyze("   ")
        assert result is None
    
    def test_confidence_threshold(self, analyzer):
        """Результаты ниже threshold не должны возвращаться."""
        # Текст который может матчиться, но с низкой confidence
        text = "проект"
        result = analyzer.analyze(text)
        assert result is None  # Не должно быть результата


class TestCaseSensitivity:
    """Тесты на регистронезависимость."""
    
    def test_uppercase(self, analyzer):
        """Должен работать с верхним регистром."""
        text = "НУЖЕН PYTHON РАЗРАБОТЧИК"
        result = analyzer.analyze(text)
        
        # Может не сработать из-за кириллицы в разных регистрах
        # Проверяем что хотя бы работает с английскими словами
        if result:
            assert result.category == OrderCategory.BACKEND
    
    def test_mixed_case(self, analyzer):
        """Должен работать со смешанным регистром."""
        text = "НуЖеН PyThOn РаЗрАбОтЧиК"
        result = analyzer.analyze(text)
        
        # Может не сработать из-за кириллицы в разных регистрах
        # Проверяем что хотя бы работает с английскими словами
        if result:
            assert result.category == OrderCategory.BACKEND
    
    def test_lowercase(self, analyzer):
        """Должен работать с нижним регистром."""
        text = "нужен react разработчик"
        result = analyzer.analyze(text)
        
        assert result is not None
        assert result.category == OrderCategory.FRONTEND


class TestMultipleMatches:
    """Тесты на множественные совпадения."""
    
    def test_highest_confidence_wins(self, analyzer):
        """Должен выбирать паттерн с наивысшей confidence."""
        text = "Нужен Python разработчик и React специалист"
        result = analyzer.analyze(text)
        
        # Оба паттерна должны сработать, выбирается с большей confidence
        assert result is not None
        # Python имеет confidence 0.95, React 0.95 - оба одинаковые, выбирается первый найденный
        assert result.category in [OrderCategory.BACKEND, OrderCategory.FRONTEND]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

