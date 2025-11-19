"""LLM client for ProxyAPI integration."""

import httpx
from typing import Optional, List, Dict, Any
from loguru import logger

from src.config.settings import get_settings


class ProxyAPIClient:
    """Client for ProxyAPI OpenAI-compatible API."""
    
    BASE_URL = "https://api.proxyapi.ru/openai/v1"
    
    def __init__(self):
        """Initialize ProxyAPI client."""
        settings = get_settings()
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model
        self.provider = settings.llm_provider
        
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        logger.info(f"ProxyAPI client initialized with model: {self.model}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text using Chat Completions API.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: Model name (defaults to configured model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Response dict with 'choices' and other metadata
            
        Example:
            messages = [
                {"role": "user", "content": "Привет!"}
            ]
            response = await client.chat_completion(messages)
        """
        model = model or self.model
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        payload.update(kwargs)
        
        try:
            logger.debug(f"Sending request to ProxyAPI: model={model}, messages={len(messages)}")
            response = await self.client.post(
                "/chat/completions",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"ProxyAPI response received: {len(result.get('choices', []))} choices")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"ProxyAPI HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"ProxyAPI request failed: {e}")
            raise
    
    async def analyze_order_message(
        self,
        message_text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze Telegram message to extract order information.
        
        Args:
            message_text: Text of the Telegram message
            context: Optional context about the channel or previous messages
            
        Returns:
            Dict with extracted order information
        """
        system_prompt = """Ты помощник для анализа сообщений из Telegram каналов с заказами.
Твоя задача - извлечь структурированную информацию о заказе из текста сообщения.

Верни ответ в формате JSON со следующими полями:
- "is_order": boolean - является ли сообщение заказом
- "order_title": string - название/заголовок заказа
- "description": string - описание заказа
- "price": string или null - цена заказа (если указана)
- "deadline": string или null - срок выполнения (если указан)
- "requirements": array of strings - требования к исполнителю
- "contact": string или null - контактная информация
- "category": string или null - категория заказа
- "confidence": float (0-1) - уверенность в извлечении данных

Если сообщение не является заказом, верни is_order: false."""
        
        user_content = f"Проанализируй следующее сообщение:\n\n{message_text}"
        if context:
            user_content += f"\n\nКонтекст: {context}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        try:
            response = await self.chat_completion(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=1000
            )
            
            # Extract content from response
            if response.get("choices") and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                
                # Try to parse JSON from response
                import json
                try:
                    # Remove markdown code blocks if present
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from LLM response: {content}")
                    return {
                        "is_order": False,
                        "error": "Failed to parse LLM response",
                        "raw_content": content
                    }
            else:
                logger.warning("No choices in LLM response")
                return {"is_order": False, "error": "No response from LLM"}
                
        except Exception as e:
            logger.error(f"Error analyzing order message: {e}")
            return {
                "is_order": False,
                "error": str(e)
            }
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Singleton instance
_client: Optional[ProxyAPIClient] = None


async def get_llm_client() -> ProxyAPIClient:
    """Get or create ProxyAPI client instance."""
    global _client
    if _client is None:
        _client = ProxyAPIClient()
    return _client

