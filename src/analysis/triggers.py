"""Триггер-паттерны для детекции IT-заказов по категориям."""

import re
from typing import TypedDict


class TriggerPattern(TypedDict):
    """Структура триггер-паттерна."""
    pattern: str  # Сырая строка regex
    confidence: float  # 0.0-1.0
    description: str  # Что ловит


# ============================================================================
# BACKEND TRIGGERS
# ============================================================================
# Включает: Python, Node.js, Java, Go, Rust, C++, PHP, ASP.NET и т.д.
# API, микросервисы, вебхуки, интеграции, базы данных

BACKEND_PATTERNS: dict[str, TriggerPattern] = {
    "python_dev": {
        "pattern": r"(?:нужен|ищ[уемся]*|требуется|в поиск[еи])\s+(?:опытн[ый]*\s+)?(?:python|питон)[.-]?\s*(?:разработчик|программист|специалист|developer|engineer)",
        "confidence": 0.95,
        "description": "Python разработчик (явное указание)"
        # Examples: "нужен Python разработчик", "ищем питон-программиста", "требуется опытный Python-специалист"
    },
    
    "nodejs_dev": {
        "pattern": r"(?:нужен|ищ[уемся]*|требуется)\s+(?:node\.?js|javascript|js)[.-]?(?:разработчик|программист|engineer)",
        "confidence": 0.94,
        "description": "Node.js / JavaScript разработчик"
        # Examples: "нужен Node.js разработчик", "ищем javascript-специалиста"
    },
    
    "api_backend": {
        "pattern": r"(?:разработка|разработать|создание|интеграция|помощь\s+с\s+разработкой)\s+(?:.*?\s+)?(?:api|rest|graphql|микросервис|backend|бэкенд)",
        "confidence": 0.92,
        "description": "API / Backend разработка"
        # Examples: "разработка REST API", "интеграция микросервисов", "нужна помощь с backend"
    },
    
    "webhook_integration": {
        "pattern": r"(?:вебхук|webhook|настройка\s+webhook).*?(?:для|с|интеграция|integration)",
        "confidence": 0.90,
        "description": "Настройка вебхуков и интеграций"
        # Examples: "настройка вебхуков", "интеграция с API", "webhook для нашего сервиса"
    },
    
    "chatbot_dev": {
        "pattern": r"(?:чат[-\s]?бот|chatbot|chat\s*bot|телеграм[-\s]?бот|telegram\s*bot|бот[-\s]?для|разработка\s+бота|создание\s+бота)",
        "confidence": 0.92,
        "description": "Разработка чат-ботов"
        # Examples: "нужен разработчик чат-бота", "создание Telegram бота", "#чатбот"
    },
    
    "getcourse_integration": {
        "pattern": r"(?:getcourse|get\s*course|геткурс|интеграция\s+getcourse|getcourse\s+разработка)",
        "confidence": 0.91,
        "description": "GetCourse интеграция и разработка"
        # Examples: "нужна интеграция GetCourse", "#getcourse", "разработка на GetCourse"
    },
    
    "technical_specialist": {
        "pattern": r"(?:технический\s+специалист|техспец|тех\s+специалист|тех\s+спец)",
        "confidence": 0.85,
        "description": "Технический специалист (общий)"
        # Examples: "ищем технического специалиста", "#техспец", "нужен тех спец"
        # Note: confidence 0.85 < 0.80 threshold, будет отправлено в LLM для уточнения
    },
    
    "database_dev": {
        "pattern": r"(?:база\s*данных|database|postgresql|mysql|mongodb|redis|оптимизация\s+postgresql|postgresql\s+базы)",
        "confidence": 0.85,
        "description": "Работа с базами данных"
        # Examples: "оптимизация PostgreSQL", "настройка MongoDB"
    },
    
    "java_dev": {
        "pattern": r"(?:нужен|ищ[уемся]*|требуется)\s+(?:java)\s*(?:разработчик|программист|developer|engineer)",
        "confidence": 0.93,
        "description": "Java разработчик"
        # Examples: "нужен Java разработчик"
    },
    
    "go_dev": {
        "pattern": r"(?:нужен|ищ[уемся]*|требуется)\s+(?:go|golang)[.-]?(?:разработчик|программист|developer)",
        "confidence": 0.92,
        "description": "Go разработчик"
        # Examples: "ищем Go-разработчика"
    },
}


# ============================================================================
# FRONTEND TRIGGERS
# ============================================================================
# Включает: React, Vue, Angular, Svelte, WebFlow, Tilda, Figma, UX/UI

FRONTEND_PATTERNS: dict[str, TriggerPattern] = {
    "react_dev": {
        "pattern": r"(?:(?:нужен|ищ[уемся]*|требуется)\s+)?(?:react|reactjs)[.-]?\s*(?:разработчик|программист|developer|engineer|specialist|специалист)",
        "confidence": 0.95,
        "description": "React разработчик"
        # Examples: "нужен React-разработчик", "ищем reactjs специалиста", "React специалист"
    },
    
    "vue_dev": {
        "pattern": r"(?:нужен|ищ[уемся]*|требуется)\s+(?:vue|vuejs|vue\.?js)\s*(?:разработчик|programmer|specialist|специалиста)",
        "confidence": 0.94,
        "description": "Vue.js разработчик"
        # Examples: "нужен Vue разработчик"
    },
    
    "angular_dev": {
        "pattern": r"(?:нужен|ищ[уемся]*|требуется)\s+(?:angular)[.-]?(?:разработчик|developer|specialist)",
        "confidence": 0.93,
        "description": "Angular разработчик"
        # Examples: "ищем Angular специалиста"
    },
    
    "frontend_dev": {
        "pattern": r"(?:фронтенд|frontend)[.-]?(?:разработчик|programmer|developer|engineer)",
        "confidence": 0.92,
        "description": "Frontend разработчик (общий)"
        # Examples: "ищем frontend-разработчика", "нужен frontend специалист"
    },
    
    "webflow_dev": {
        "pattern": r"(?:webflow|webflow\s+design|webflow\s+developer).*?(?:разработчик|specialist|developer|специалист)",
        "confidence": 0.93,
        "description": "WebFlow разработчик"
        # Examples: "нужен WebFlow специалист"
    },
    
    "ui_ux_design": {
        "pattern": r"(?:ui|ux|ui/ux|дизайн)\s*/?\s*(?:дизайнер|designer|специалист).*?(?:figma|ui|ux)",
        "confidence": 0.91,
        "description": "UX/UI дизайнер (Figma и т.д.)"
        # Examples: "нужен UI/UX дизайнер", "ищем специалиста на Figma"
    },
}


# ============================================================================
# MOBILE TRIGGERS
# ============================================================================
# Включает: Flutter, React Native, iOS, Android

MOBILE_PATTERNS: dict[str, TriggerPattern] = {
    "flutter_dev": {
        "pattern": r"(?:нужен|ищ[уемся]*|требуется|разработчик\s+для\s+создания).*?(?:flutter|flutter\s+dev).*?(?:разработчик|developer|programmer|specialist|приложения|app)",
        "confidence": 0.95,
        "description": "Flutter разработчик"
        # Examples: "нужен Flutter-разработчик", "разработчик для создания мобильного приложения на Flutter"
    },
    
    "react_native_dev": {
        "pattern": r"(?:react\s*native|rn\s+dev).*?(?:разработчик|developer|специалиста)",
        "confidence": 0.94,
        "description": "React Native разработчик"
        # Examples: "ищем React Native специалиста"
    },
    
    "ios_dev": {
        "pattern": r"(?:ios|swift|apple).*?(?:разработчик|developer|programmer)",
        "confidence": 0.93,
        "description": "iOS разработчик"
        # Examples: "нужен iOS разработчик", "ищем Swift специалиста"
    },
    
    "android_dev": {
        "pattern": r"(?:android|kotlin).*?(?:разработчик|developer|programmer)",
        "confidence": 0.93,
        "description": "Android разработчик"
        # Examples: "нужен Android разработчик"
    },
    
    "mobile_app": {
        "pattern": r"(?:разработчик\s+для\s+создания|нужен|ищ[уемся]*|требуется).*?(?:мобильного\s+приложения|mobile\s+app|мобильное\s+приложение).*?(?:на\s+)?(?:flutter|react\s*native|ios|android)?",
        "confidence": 0.90,
        "description": "Мобильное приложение (общее)"
        # Examples: "нужна разработка мобильного приложения", "разработчик для создания мобильного приложения на Flutter"
    },
}


# ============================================================================
# AI/ML & AUTOMATION TRIGGERS
# ============================================================================
# Включает: Prompt Engineering, ChatGPT, нейросети, автоматизация

AI_ML_PATTERNS: dict[str, TriggerPattern] = {
    "ai_engineer": {
        "pattern": r"(?:ai|ии|искусственный\s+интеллект).*?(?:инженер|engineer|specialist|специалист)",
        "confidence": 0.93,
        "description": "AI инженер"
        # Examples: "ищем AI инженера", "нужен специалист по ИИ"
    },
    
    "prompt_engineer": {
        "pattern": r"(?:prompt|промпт).*?(?:engineer|инженер|specialist|специалист)",
        "confidence": 0.92,
        "description": "Prompt Engineer"
        # Examples: "ищем Prompt Engineer", "нужен специалист по промптам"
    },
    
    "chatgpt_integration": {
        "pattern": r"(?:нужна\s+помощь\s+с|помощь\s+с|интеграция|integration|подключение|create|создание|в\s+наш).*?(?:chatgpt|gpt-?4|openai|chat\s*bot)",
        "confidence": 0.90,
        "description": "ChatGPT / OpenAI интеграция"
        # Examples: "интеграция ChatGPT", "нужна помощь с интеграцией ChatGPT в наш проект"
    },
    
    "chatbot_ai": {
        "pattern": r"(?:чат[-\s]?бот|chatbot|chat\s*bot).*?(?:на\s+базе|с\s+использованием|с\s+помощью|на|для).*?(?:ai|ии|chatgpt|gpt|нейросеть)",
        "confidence": 0.89,
        "description": "AI чат-боты"
        # Examples: "чат-бот на базе ChatGPT", "создание AI бота"
    },
    
    "automation_business": {
        "pattern": r"(?:автоматизация|automation).*?(?:бизнес|business|процесс|process|workflow)",
        "confidence": 0.88,
        "description": "Автоматизация бизнес-процессов"
        # Examples: "автоматизация бизнес-процессов", "нужна автоматизация workflow"
    },
    
    "neural_network": {
        "pattern": r"(?:нейросеть|neural\s+network|machine\s+learning|ml).*?(?:обучение|training|создание|development)",
        "confidence": 0.89,
        "description": "Нейросети и обучение моделей"
        # Examples: "обучение нейросети", "разработка ML модели"
    },
}


# ============================================================================
# LOW-CODE / NO-CODE TRIGGERS
# ============================================================================
# Включает: Bubble, Glide, Adalo, Zapier, Make, n8n, Airtable

LOW_CODE_PATTERNS: dict[str, TriggerPattern] = {
    "bubble_dev": {
        "pattern": r"(?:bubble|bubble\.io).*?(?:разработчик|developer|specialist|специалист)",
        "confidence": 0.94,
        "description": "Bubble.io разработчик"
        # Examples: "ищем Bubble специалиста", "нужен разработчик на Bubble"
    },
    
    "zapier_automation": {
        "pattern": r"(?:zapier|make|n8n|настройка\s+zapier|zapier\s+интеграции)",
        "confidence": 0.92,
        "description": "Zapier / Make / n8n автоматизация"
        # Examples: "настройка Zapier интеграции", "автоматизация через Make"
    },
    
    "airtable_glide": {
        "pattern": r"(?:airtable|glide|adalo).*?(?:разработка|development|приложение|app)",
        "confidence": 0.91,
        "description": "Airtable / Glide / Adalo разработка"
        # Examples: "разработка на Airtable", "создание приложения на Glide"
    },
}


# ============================================================================
# OTHER TRIGGERS
# ============================================================================
# 1C, Shopify, маркетплейсы, специализированные решения

OTHER_PATTERNS: dict[str, TriggerPattern] = {
    "1c_dev": {
        "pattern": r"(?:1[сc]|1c|на\s+1[сc]|разработчика\s+на\s+1[сc])",
        "confidence": 0.93,
        "description": "1C разработчик"
        # Examples: "ищем разработчика на 1C", "нужен программист 1C"
    },
    
    "shopify_dev": {
        "pattern": r"(?:shopify).*?(?:разработчик|developer|specialist|theme|plugin)",
        "confidence": 0.93,
        "description": "Shopify разработчик"
        # Examples: "нужен Shopify разработчик", "разработка темы для Shopify"
    },
    
    "marketplace_dev": {
        "pattern": r"(?:маркетплейс|marketplace|яндекс\s*маркет|ozon|wildberries).*?(?:интеграция|разработка|api)",
        "confidence": 0.90,
        "description": "Разработка для маркетплейсов"
        # Examples: "интеграция с Яндекс.Маркет", "разработка под Ozon"
    },
}


# ============================================================================
# ВТОРИЧНЫЕ ПАТТЕРНЫ (для повышения точности)
# ============================================================================

CONTEXT_PATTERNS: dict[str, TriggerPattern] = {
    "hiring_context": {
        "pattern": r"(?:ищ[уемся]*|нужн[ыа]|требуется|в поиск[еи]|подходил|ищите|срочно\s+нужен)",
        "confidence": 0.30,  # Низкий, это просто контекст найма
        "description": "Контекст найма (вспомогательный)"
        # Examples: "ищем", "нужен", "требуется"
    },
    
    "project_context": {
        "pattern": r"(?:проект|для.*?(?:компаний|бизнес|app|приложение))",
        "confidence": 0.20,  # Очень низкий, просто контекст
        "description": "Контекст проекта (вспомогательный)"
        # Examples: "для проекта", "под проект компании"
    },
}


# ============================================================================
# ИСКЛЮЧАЮЩИЕ ПАТТЕРНЫ (negative lookahead)
# ============================================================================
# Если сообщение матчит эти, то это точно НЕ заказ

EXCLUDE_PATTERNS: list[str] = [
    r"(?:продам|куплю|продаю|куплю)",  # Торговля, а не разработка
    r"(?:услуга по уборке|заказ еды|доставка)",  # Совсем не IT
    r"(?:spam|спам|реклама|объявление о вакансии для себя)",  # Явный spam
    r"(?:смешная картинка|мем|баян|давай поговорим о жизни)",  # Не серьезное сообщение
]


# ============================================================================
# ОБЪЕДИНИТЬ ВСЕ ПАТТЕРНЫ
# ============================================================================

ALL_PATTERNS: dict[str, dict[str, TriggerPattern]] = {
    "Backend": BACKEND_PATTERNS,
    "Frontend": FRONTEND_PATTERNS,
    "Mobile": MOBILE_PATTERNS,
    "AI/ML": AI_ML_PATTERNS,
    "Low-Code": LOW_CODE_PATTERNS,
    "Other": OTHER_PATTERNS,
}

