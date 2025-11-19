"""LLM prompts and response schemas."""

from typing import TypedDict, Optional
import json
import re

# ============================================================================
# SYSTEM PROMPT (на английском для лучшей производительности GPT)
# ============================================================================

SYSTEM_PROMPT = """You are a professional assistant for detecting IT service orders from Russian Telegram messages.

Your task:

1. Analyze incoming text messages to determine if they contain orders/requests for technical services

2. Classify the order into one of these categories: Backend, Frontend, Mobile, AI/ML, Low-Code, Other

3. Provide a relevance score (0.0-1.0) indicating how certain you are that this is a valid order

4. Explain briefly why you classified it this way

Categories explanation:

- Backend: Python, Node.js, Go, Rust, Java, C++, API development, microservices, databases, webhooks

- Frontend: React, Vue, Angular, WebFlow, Figma, UI/UX design, HTML/CSS

- Mobile: Flutter, React Native, iOS, Android mobile app development

- AI/ML: ChatGPT integration, Prompt engineering, neural networks, business automation, AI assistants

- Low-Code: Bubble, Glide, Adalo, Zapier, Make, n8n, no-code platforms

- Other: 1C development, Shopify, marketplaces, specialized solutions

Important rules:

1. Only return valid orders for technical services, NOT:
   - General recommendations or advice
   - Social messages or casual chat
   - Spam or advertisements
   - Product sales (laptops, phones, etc.)

2. Be conservative with relevance_score:
   - Only give scores above 0.7 if you're quite confident
   - Use 0.3-0.5 for ambiguous cases
   - Use < 0.3 for unlikely orders

3. Always respond with valid JSON, no markdown formatting

4. Prioritize accuracy over recall - better to miss an order than include non-orders

Response format (JSON only):

{
  "is_order": true/false,
  "category": "Backend" or "Frontend" or "Mobile" or "AI/ML" or "Low-Code" or "Other",
  "relevance_score": 0.0-1.0 (float),
  "reason": "Brief explanation in Russian"
}
"""

# ============================================================================
# BATCH PROCESSING PROMPT (для анализа нескольких сообщений)
# ============================================================================

BATCH_ANALYSIS_PROMPT_TEMPLATE = """Analyze these {count} messages and provide JSON responses for each.

For each message, provide the response in the same order as the input.

Messages to analyze:

{messages_list}

Provide JSON responses in order, one per line:"""

# ============================================================================
# RESPONSE SCHEMA (TypedDict для type-safe парсинга)
# ============================================================================

class LLMResponseSchema(TypedDict):
    """Схема для ответа от LLM."""
    is_order: bool
    category: str
    relevance_score: float
    reason: str

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_batch_prompt(messages: list[str]) -> str:
    """
    Форматировать batch промпт для нескольких сообщений.
    
    Args:
        messages: Список текстов для анализа
    
    Returns:
        Отформатированный промпт
    
    Example:
        messages = ["Нужен Python разработчик", "Привет, как дела?"]
        prompt = format_batch_prompt(messages)
    """
    messages_list = "\n".join([f"{i+1}. {msg}" for i, msg in enumerate(messages)])
    return BATCH_ANALYSIS_PROMPT_TEMPLATE.format(count=len(messages), messages_list=messages_list)


def validate_response_schema(response_dict: dict) -> bool:
    """
    Валидировать что ответ соответствует схеме.
    
    Args:
        response_dict: Распарсенный JSON ответ
    
    Returns:
        True если валиден, False иначе
    """
    required_fields = {"is_order", "category", "relevance_score", "reason"}
    if not all(field in response_dict for field in required_fields):
        return False
    
    # Проверить типы
    if not isinstance(response_dict["is_order"], bool):
        return False
    if not isinstance(response_dict["category"], str):
        return False
    if not isinstance(response_dict["relevance_score"], (int, float)):
        return False
    if not isinstance(response_dict["reason"], str):
        return False
    
    # Проверить диапазоны
    if not (0.0 <= response_dict["relevance_score"] <= 1.0):
        return False
    
    valid_categories = {"Backend", "Frontend", "Mobile", "AI/ML", "Low-Code", "Other"}
    # Если is_order=False, category может быть пустым или "Other"
    if response_dict["is_order"]:
        if response_dict["category"] not in valid_categories:
            return False
    else:
        # Для не-заказов category должен быть пустым или "Other"
        if response_dict["category"] and response_dict["category"] not in valid_categories:
            return False
    
    return True


def parse_json_response(text: str) -> Optional[dict]:
    """
    Парсить JSON из ответа LLM (может содержать мусор до/после JSON).
    
    Args:
        text: Сырой текст ответа от LLM
    
    Returns:
        Распарсенный JSON или None если не удалось парсить
    
    Example:
        text = 'Sure, here is the response:\\n{"is_order": true, ...}'
        result = parse_json_response(text)
    """
    # Попытка 1: Парсить весь текст как JSON
    try:
        parsed = json.loads(text)
        # Нормализовать: если category null или пустой, заменить на "Other"
        if parsed.get("category") is None or parsed.get("category") == "":
            parsed["category"] = "Other"
        if validate_response_schema(parsed):
            return parsed
    except json.JSONDecodeError:
        pass
    
    # Попытка 2: Найти JSON в тексте (ищем {... })
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    for match in matches:
        try:
            parsed = json.loads(match)
            # Нормализовать: если category null или пустой, заменить на "Other"
            if parsed.get("category") is None or parsed.get("category") == "":
                parsed["category"] = "Other"
            if validate_response_schema(parsed):
                return parsed
        except json.JSONDecodeError:
            continue
    
    return None


def parse_batch_json_response(text: str, count: int) -> list[dict]:
    """
    Парсить несколько JSON объектов из ответа batch обработки.
    
    Args:
        text: Сырой ответ от LLM (может быть многострочным)
        count: Сколько объектов ожидается
    
    Returns:
        Список распарсенных JSON объектов
    
    Example:
        text = '{"is_order": true, ...}\\n{"is_order": false, ...}'
        results = parse_batch_json_response(text, 2)
    """
    results = []
    lines = text.strip().split('\n')
    
    for line in lines:
        if not line.strip():
            continue
        
        parsed = parse_json_response(line)
        if parsed and validate_response_schema(parsed):
            results.append(parsed)
        
        if len(results) >= count:
            break
    
    # Если не нашли достаточно результатов, попробуем парсить весь текст
    if len(results) < count:
        parsed = parse_json_response(text)
        if parsed and validate_response_schema(parsed):
            if parsed not in results:
                results.append(parsed)
    
    return results


# ============================================================================
# EXAMPLES FOR TESTING
# ============================================================================

EXAMPLE_RESPONSES = {
    "backend_order": {
        "is_order": True,
        "category": "Backend",
        "relevance_score": 0.95,
        "reason": "Явный запрос Python разработчика для конкретного проекта",
    },
    "ai_ml_order": {
        "is_order": True,
        "category": "AI/ML",
        "relevance_score": 0.82,
        "reason": "Запрос на автоматизацию бизнес-процессов с использованием ИИ",
    },
    "ambiguous_order": {
        "is_order": True,
        "category": "Low-Code",
        "relevance_score": 0.65,
        "reason": "Может быть заказ на Zapier интеграцию, но контекст неясен",
    },
    "not_an_order": {
        "is_order": False,
        "category": "Other",
        "relevance_score": 0.0,
        "reason": "Это просто общее обсуждение, не заказ на услугу",
    },
}

# ============================================================================
# CONSTANTS FOR LLM CONFIGURATION
# ============================================================================

# Рекомендуемые параметры для ChatGPT-4o-mini
LLM_CONFIG = {
    "temperature": 0.3,  # Низкая температура = более консервативные ответы
    "max_tokens": 512,   # Достаточно для одного JSON объекта
    "top_p": 0.9,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
}

# Размер батча (не более 10 для экономии и скорости)
BATCH_SIZE = 10

# Таймауты
REQUEST_TIMEOUT = 30  # секунд
RETRY_DELAY = 1  # секунда
MAX_RETRIES = 3

# ProxyAPI endpoint
PROXYAPI_BASE_URL = "https://api.proxyapi.ru/openai/v1"
PROXYAPI_CHAT_ENDPOINT = f"{PROXYAPI_BASE_URL}/chat/completions"

