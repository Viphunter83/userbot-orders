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
        "pattern": r"(?:ищу|ищем|нужен|требуется|в\s+поиск[еи]|в\s+поисках|на\s+проект\s+требуется|на\s+проект\s+компании\s+требуется)\s+(?:опытн[ый]*\s+)?(?:junior\s+)?(?:python|питон)[.-]?\s*(?:разработчик|программист|специалист|developer|engineer|спец)|(?:junior\s+)?(?:python|питон)[.-]?\s*(?:разработчик|программист)|на\s+проект\s+компании\s+требуется\s+python",
        "confidence": 0.95,
        "description": "Python разработчик (явное указание)"
        # Examples: "Ищем Python-разработчика", "Junior Python-разработчик", "на проект компании требуется Python"
    },
    
    "junior_programmer": {
        "pattern": r"(?:junior\s+программист|junior\s+разработчик)",
        "confidence": 0.88,
        "description": "Junior программист / разработчик"
        # Examples: "Junior Программист"
        # Note: confidence 0.88 >= 0.80, будет сохранен
    },
    
    "backend_dev": {
        "pattern": r"(?:разработка\s+бэкенда|разработчик\s+на\s+бэк|специалист\s+на\s+python|бэкенд\s+разработчик|backend[-\s]?разработчик|backend[-\s]?developer)",
        "confidence": 0.92,
        "description": "Backend разработка"
        # Examples: "разработка бэкенда", "разработчик на бэк", "backend-разработчик"
    },
    
    "junior_backend": {
        "pattern": r"(?:junior\s+backend[-\s]?разработчик|junior\s+backend[-\s]?developer|junior\s+бэкенд[-\s]?разработчик)",
        "confidence": 0.90,
        "description": "Junior Backend разработчик"
        # Examples: "Junior backend-разработчик", "Junior backend developer"
    },
    
    "fullstack_dev": {
        "pattern": r"(?:в\s+поисках|ищем|нужен|требуется)\s+full[-\s]?stack\s+разработчик",
        "confidence": 0.94,
        "description": "Full-stack разработчик"
        # Examples: "в поисках Full-stack разработчика"
    },
    
    "webhook_setup": {
        "pattern": r"(?:настройка\s+вебхуков|вебхук|webhook)",
        "confidence": 0.90,
        "description": "Настройка вебхуков"
        # Examples: "настройка вебхуков"
    },
    
    "messenger_integration": {
        "pattern": r"(?:интеграция\s+с\s+мессенджерами|интеграция\s+api)",
        "confidence": 0.91,
        "description": "Интеграция с мессенджерами и API"
        # Examples: "интеграция с мессенджерами", "интеграция API"
    },
    
    "prototype_creation": {
        "pattern": r"(?:создание\s+прототипа\s+продукта|нужен\s+mvp|создание\s+mvp)",
        "confidence": 0.88,
        "description": "Создание прототипа / MVP"
        # Examples: "создание прототипа продукта", "нужен MVP"
    },
    
    "crm_automation": {
        "pattern": r"(?:автоматизация\s+crm[-\s]?системы|автоматизация\s+crm)",
        "confidence": 0.89,
        "description": "Автоматизация CRM"
        # Examples: "автоматизация CRM-системы"
    },
    
    "email_automation": {
        "pattern": r"(?:автоматизация\s+email\s+рассылок|email\s+рассылки)",
        "confidence": 0.88,
        "description": "Автоматизация email рассылок"
        # Examples: "автоматизация email рассылок"
    },
    
    "general_developer": {
        "pattern": r"(?:ищу\s+разработчика|нужен\s+разработчик|требуется\s+разработчик)",
        "confidence": 0.80,
        "description": "Разработчик (общий запрос)"
        # Examples: "ищу разработчика"
        # Note: confidence 0.80 = порог, будет отправлено в LLM для уточнения
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
        "pattern": r"(?:webflow|webflowflow)[-\s/]?(?:разработчик|специалист|спец|tilda|тильда)|(?:ищем|нужен|требуется|в\s+поисках)\s+(?:разработчик|специалист)\s+на\s+(?:webflow|tilda)|(?:разработка|проект)\s+на\s+(?:webflow|tilda)|webflow\s*/\s*tilda\s+спец",
        "confidence": 0.93,
        "description": "WebFlow / Tilda разработчик"
        # Examples: "Webflow разработчик", "Webflow / Tilda спец", "проект на Webflow"
    },
    
    "tilda_dev": {
        "pattern": r"(?:ищем\s+разработчика\s+на\s+tilda|в\s+поисках\s+tilda[-\s]?разработчика|требуется\s+tilda\s+specialist|нужен\s+дизайнер\s+tilda|tilda[-\s]?разработчик)",
        "confidence": 0.92,
        "description": "Tilda разработчик / дизайнер"
        # Examples: "Ищем разработчика на Tilda", "Требуется Tilda specialist"
    },
    
    "figma_designer": {
        "pattern": r"(?:специалист\s+figma|дизайнер\s+на\s+figma|ищем\s+специалиста\s+на\s+figma|figma\s+дизайнер)",
        "confidence": 0.91,
        "description": "Figma дизайнер"
        # Examples: "Специалист figma", "Дизайнер на figma"
    },
    
    "ux_ui_dev": {
        "pattern": r"(?:ux/ui\s+разработчик|ux/ui\s+специалист|нужен\s+ux/ui|ux\s+ui\s+разработчик)",
        "confidence": 0.92,
        "description": "UX/UI разработчик / специалист"
        # Examples: "UX/UI разработчик", "Нужен UX/UI"
    },
    
    "website_dev": {
        "pattern": r"(?:разработчик\s+сайтов|нужен\s+специалист\s+для\s+создания\s+сайта|ищу\s+спеца\s+по\s+сайтам)",
        "confidence": 0.90,
        "description": "Разработчик сайтов"
        # Examples: "разработчик сайтов", "нужен специалист для создания сайта"
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
        "pattern": r"(?:разработчик\s+для\s+создания|нужен|ищ[уемся]*|требуется|нужно\s+создать|ищу\s+спец[ау]\s+по\s+мобилке|ищу\s+спец[ау]\s+по\s+мобилк[еи]).*?(?:мобильного\s+приложения|mobile\s+app|мобильное\s+приложение|мобилк[аи]).*?(?:на\s+)?(?:flutter|react\s*native|ios|android)?",
        "confidence": 0.90,
        "description": "Мобильное приложение (общее)"
        # Examples: "нужен разработчик для мобильного приложения", "ищу спеца по мобилке"
    },
    
    "mobile_specialist": {
        "pattern": r"(?:ищу\s+спец[ау]\s+по\s+мобилк[еи]|спец\s+по\s+мобилк[еи])",
        "confidence": 0.88,
        "description": "Специалист по мобильным приложениям"
        # Examples: "ищу спеца по мобилке"
    },
    
    "flutter_dev_extended": {
        "pattern": r"(?:flutter\s*/?\s*flutterflow\s+разработка|flutterflow)",
        "confidence": 0.94,
        "description": "Flutter / FlutterFlow разработка"
        # Examples: "Flutter / FlutterFlow разработка"
    },
}


# ============================================================================
# AI/ML & AUTOMATION TRIGGERS
# ============================================================================
# Включает: Prompt Engineering, ChatGPT, нейросети, автоматизация

AI_ML_PATTERNS: dict[str, TriggerPattern] = {
    "ai_engineer": {
        "pattern": r"(?:ищу|ищем|нужен|требуется|на\s+проект\s+требуется|порекомендуйте|в\s+поиск[еи]|в\s+поисках)\s+(?:ai|ии|искусственный\s+интеллект)[-\s]?(?:инженер|engineer|специалист|specialist)|консультант\s+по\s+ai|консультант\s+по\s+ии",
        "confidence": 0.93,
        "description": "AI инженер / специалист / консультант"
        # Examples: "ищу AI инженера", "нужен AI специалист", "консультант по AI"
    },
    
    "prompt_engineer": {
        "pattern": r"(?:требуется|ищем|нужен|ищу|в\s+поиск[еи]|в\s+поисках)\s+(?:prompt\s+engineer|промпт[-\s]?инженер|промптовик|специалист\s+по\s+промпт|специалиста\s+по\s+промпт|ai\s+prompt|промпт[-\s]?специалист|промпт[-\s]?инженер)",
        "confidence": 0.92,
        "description": "Prompt Engineer / промпт-инженер"
        # Examples: "Требуется Prompt Engineer", "Ищем промптовика", "В поиске специалиста по промпт"
    },
    
    "prompt_services": {
        "pattern": r"(?:промпт\s+для|написать\s+промпт|оптимизация\s+промптов|промпт\s+для\s+(?:создания|маркетинга|seo|копирайтинга|анализа\s+данных|генерации\s+изображений|обучения\s+модели|автоматизации|чат[-\s]?бота|аналитики|генерации\s+сценариев|соцсетей))",
        "confidence": 0.88,
        "description": "Услуги по промптам"
        # Examples: "промпт для создания чат-бота", "написать промпт", "промпт для маркетинга"
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
        "pattern": r"(?:нужна\s+автоматизация|ищем\s+автоматизатора|нужно\s+автоматизировать|специалист\s+по\s+автоматизации|автоматизация\s+(?:бизнес[-\s]?процессов|бизнеса|продаж|обработки\s+заявок|поддержки\s+клиентов|email\s+рассылок|crm[-\s]?системы|маркетинговых\s+кампаний|отчетов))",
        "confidence": 0.90,
        "description": "Автоматизация бизнес-процессов"
        # Examples: "нужна автоматизация", "автоматизация продаж", "автоматизация обработки заявок"
    },
    
    "neural_network": {
        "pattern": r"(?:специалист\s+по\s+нейросетям|ищу\s+специалиста\s+по\s+нейросетям|обучить\s+нейросеть|обучить\s+chatgpt|обучить\s+gpt|обучить\s+chatgpt|обучить\s+ии|обучить\s+ai|нейросеть|neural\s+network|machine\s+learning|ml).*?(?:обучение|training|создание|development)?",
        "confidence": 0.89,
        "description": "Нейросети и обучение моделей"
        # Examples: "Специалист по нейросетям", "обучить нейросеть", "Обучить GPT"
    },
    
    "ai_assistant_creation": {
        "pattern": r"(?:создать|создание)\s+(?:ai[-\s]?ассистента|ai[-\s]?агента|ии[-\s]?ассистента|ии[-\s]?агента|ии[-\s]?помощника|ai[-\s]?помощника)",
        "confidence": 0.91,
        "description": "Создание AI ассистентов"
        # Examples: "Создать AI-ассистента", "Создать ИИ-агента"
    },
    
    "ai_chatbot": {
        "pattern": r"(?:нужен\s+чат[-\s]?бот\s+с\s+ии|нужен\s+telegram[-\s]?бот\s+с\s+ии|чат[-\s]?бот\s+с\s+ai|ai[-\s]?бот|ии[-\s]?бот|телеграм\s+бот|бот\s+для\s+маркетплейса)",
        "confidence": 0.90,
        "description": "AI чат-боты и боты"
        # Examples: "Нужен чат-бот с ИИ", "AI-бот", "телеграм бот"
    },
    
    "ai_generation": {
        "pattern": r"(?:генерация\s+(?:видео|изображения|изображений)|генерация\s+изображений\s+по\s+промпту|ai[-\s]?услуги|ии[-\s]?сервис)",
        "confidence": 0.87,
        "description": "Генерация контента с помощью AI"
        # Examples: "Генерация видео", "Генерация изображения", "AI-услуги"
    },
    
    "openai_integration": {
        "pattern": r"(?:openai|подключить\s+gpt|интеграция\s+с\s+ии|интеграция\s+с\s+ai)",
        "confidence": 0.89,
        "description": "OpenAI интеграция"
        # Examples: "OpenAI", "Подключить GPT", "интеграция с ИИ"
    },
}


# ============================================================================
# LOW-CODE / NO-CODE TRIGGERS
# ============================================================================
# Включает: Bubble, Glide, Adalo, Zapier, Make, n8n, Airtable

LOW_CODE_PATTERNS: dict[str, TriggerPattern] = {
    "bubble_dev": {
        "pattern": r"(?:нужен\s+специалист\s+по\s+bubble|нужен\s+специалист\s+bubble|разработка\s+на\s+bubble|проект\s+на\s+bubble|ищу\s+разработчика\s+на\s+bubble|bubble|bubble\.io).*?(?:разработчик|developer|specialist|специалист)?",
        "confidence": 0.94,
        "description": "Bubble.io разработчик"
        # Examples: "нужен специалист по Bubble", "разработка на Bubble", "ищу разработчика на Bubble"
    },
    
    "zapier_automation": {
        "pattern": r"(?:проект\s+на\s+zapier|разработка\s+на\s+zapier|настройка\s+zapier\s+интеграции|zapier|make|n8n|zapier\s+интеграции)",
        "confidence": 0.92,
        "description": "Zapier / Make / n8n автоматизация"
        # Examples: "проект на Zapier", "настройка Zapier интеграции"
    },
    
    "make_automation": {
        "pattern": r"(?:проект\s+на\s+make|разработка\s+на\s+make)",
        "confidence": 0.91,
        "description": "Make автоматизация"
        # Examples: "проект на Make", "разработка на Make"
    },
    
    "n8n_automation": {
        "pattern": r"(?:проект\s+на\s+n8n|разработка\s+на\s+n8n|ищу\s+разработчика\s+на\s+n8n|нужен\s+специалист\s+n8n)",
        "confidence": 0.91,
        "description": "n8n автоматизация"
        # Examples: "проект на n8n", "ищу разработчика на n8n"
    },
    
    "airtable_glide": {
        "pattern": r"(?:проект\s+на\s+(?:airtable|glide|adalo)|разработка\s+на\s+(?:airtable|glide|adalo)|airtable|glide|adalo).*?(?:разработка|development|приложение|app)?",
        "confidence": 0.91,
        "description": "Airtable / Glide / Adalo разработка"
        # Examples: "проект на Glide", "разработка на Airtable", "проект на Adalo"
    },
    
    "google_sheets_automation": {
        "pattern": r"(?:автоматизация\s+отчетов\s+в\s+google\s+sheets|google\s+sheets\s+автоматизация)",
        "confidence": 0.88,
        "description": "Автоматизация Google Sheets"
        # Examples: "автоматизация отчетов в Google Sheets"
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
        "pattern": r"(?:нужен\s+специалист\s+shopify|нужен\s+специалист\s+shopify|ищу\s+разработчика\s+на\s+shopify|проект\s+на\s+shopify|разработка\s+на\s+shopify|shopify).*?(?:разработчик|developer|specialist|theme|plugin)?",
        "confidence": 0.93,
        "description": "Shopify разработчик"
        # Examples: "нужен специалист shopify", "проект на shopify"
    },
    
    "1c_dev_extended": {
        "pattern": r"(?:разработчик\s+1c|программист\s+1c|1c\s+разработчик)",
        "confidence": 0.93,
        "description": "1C разработчик / программист"
        # Examples: "разработчик 1C", "программист 1C"
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

