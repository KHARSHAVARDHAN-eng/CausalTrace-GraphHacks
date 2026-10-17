import abc
from typing import Optional
from app.core.config import settings
from app.schemas.health import LLMHealth


class BaseLLMProvider(abc.ABC):
    """Abstract interface for LLM analysis providers."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        pass

    @property
    @abc.abstractmethod
    def model(self) -> str:
        """Model identifier."""
        pass

    @abc.abstractmethod
    def check_health(self) -> LLMHealth:
        """Probe LLM readiness and configuration."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or settings.LLM_API_KEY
        self._model = model or settings.LLM_MODEL or "gpt-4o-mini"

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    def check_health(self) -> LLMHealth:
        has_key = bool(self._api_key and len(self._api_key.strip()) > 0)
        return LLMHealth(
            provider=self.name,
            model=self.model,
            has_api_key=has_key,
            status="ready" if has_key else "unconfigured",
            message="OpenAI provider configured with active key." if has_key
            else "OpenAI API key missing. Configure LLM_API_KEY in .env to enable AI root-cause analysis.",
        )


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or settings.LLM_API_KEY
        self._model = model or settings.LLM_MODEL or "claude-3-5-sonnet-20241022"

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model(self) -> str:
        return self._model

    def check_health(self) -> LLMHealth:
        has_key = bool(self._api_key and len(self._api_key.strip()) > 0)
        return LLMHealth(
            provider=self.name,
            model=self.model,
            has_api_key=has_key,
            status="ready" if has_key else "unconfigured",
            message="Anthropic provider configured with active key." if has_key
            else "Anthropic API key missing. Configure LLM_API_KEY in .env to enable AI root-cause analysis.",
        )


class StubProvider(BaseLLMProvider):
    """Explicit offline test provider (no fake live analysis)."""

    def __init__(self, model: str = "offline-stub"):
        self._model = model

    @property
    def name(self) -> str:
        return "stub"

    @property
    def model(self) -> str:
        return self._model

    def check_health(self) -> LLMHealth:
        return LLMHealth(
            provider=self.name,
            model=self.model,
            has_api_key=False,
            status="stub",
            message="Offline stub provider active (no external API calls).",
        )


def get_llm_provider() -> BaseLLMProvider:
    """Factory creating configured LLM provider according to environment settings."""
    provider_name = (settings.LLM_PROVIDER or "openai").lower().strip()
    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "anthropic":
        return AnthropicProvider()
    elif provider_name == "stub":
        return StubProvider()
    else:
        # Default fallback
        return OpenAIProvider()
