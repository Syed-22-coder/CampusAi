from typing import Any, Dict, List, Optional

import httpx
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.llms import LLM

from config import settings
from app.utils.exceptions import LLMError
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _build_v1_url(base_url: str, path: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        return f"{normalized}{path}"
    return f"{normalized}/v1{path}"


def _extract_message_content(payload: Dict[str, Any]) -> str:
    choices = payload.get("choices", [])
    if not choices:
        raise LLMError("Ollama returned no choices.")

    message = choices[0].get("message", {})
    content = message.get("content", "")
    if not isinstance(content, str) or not content.strip():
        raise LLMError("Ollama returned an empty message.")
    return content.strip()


class OllamaOpenAICompatibleLLM(LLM):
    """LangChain-compatible wrapper around Ollama's OpenAI-style chat endpoint."""

    base_url: str
    model: str
    timeout_seconds: float = 60.0
    default_temperature: float = 0.2
    default_max_tokens: int = 500

    @property
    def _llm_type(self) -> str:
        return "ollama-openai-compatible"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
        }

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.default_temperature),
            "max_tokens": kwargs.get("max_tokens", self.default_max_tokens),
        }
        if stop:
            payload["stop"] = stop

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(_build_v1_url(self.base_url, "/chat/completions"), json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc

        return _extract_message_content(response.json())


class LLMService:
    """Service for LLM operations via Ollama"""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout_seconds = settings.OLLAMA_TIMEOUT_SECONDS
        self.logger = logger

    async def generate_response(
        self,
        prompt: str,
        temperature: float = settings.OLLAMA_TEMPERATURE,
        max_tokens: int = settings.OLLAMA_MAX_TOKENS,
    ) -> str:
        try:
            return await self.generate_chat_response(
                [{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            self.logger.error(f"LLM generation error: {str(exc)}")
            raise

    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = settings.OLLAMA_TEMPERATURE,
        max_tokens: int = settings.OLLAMA_MAX_TOKENS,
    ) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        self.logger.info(
            "LLM inference requested",
            extra={"extra_data": {"model": self.model, "message_count": len(messages)}},
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(_build_v1_url(self.base_url, "/chat/completions"), json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc

        return _extract_message_content(response.json())

    async def is_available(self) -> bool:
        """Check if LLM service is available"""
        try:
            async with httpx.AsyncClient(timeout=min(self.timeout_seconds, 10.0)) as client:
                response = await client.get(_build_v1_url(self.base_url, "/models"))
                response.raise_for_status()

            models = response.json().get("data", [])
            if not isinstance(models, list):
                return False
            available_models = {model.get("id") for model in models if isinstance(model, dict)}
            return self.model in available_models or not available_models
        except httpx.HTTPError as exc:
            self.logger.warning(f"LLM unavailable: {str(exc)}")
            return False

    def format_prompt(self, query: str, context: str) -> str:
        """Format prompt with context"""
        return f"""You are a helpful assistant for Centennial College students.

Context:
{context}

Question: {query}

Please provide a helpful and accurate answer based on the provided context."""

    def get_langchain_llm(
        self,
        temperature: float = settings.OLLAMA_TEMPERATURE,
        max_tokens: int = settings.OLLAMA_MAX_TOKENS,
    ) -> OllamaOpenAICompatibleLLM:
        return OllamaOpenAICompatibleLLM(
            base_url=self.base_url,
            model=self.model,
            timeout_seconds=self.timeout_seconds,
            default_temperature=temperature,
            default_max_tokens=max_tokens,
        )
