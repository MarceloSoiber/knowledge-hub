from dataclasses import dataclass

from ..core.settings import Settings, get_settings


@dataclass(slots=True)
class LLMClientConfig:
    provider: str
    base_url: str
    model: str
    api_key: str | None = None


def build_llm_client_config(settings: Settings | None = None) -> LLMClientConfig:
    current_settings = settings or get_settings()

    if current_settings.llm_provider == "api":
        return LLMClientConfig(
            provider="api",
            base_url=current_settings.api_llm_base_url,
            model=current_settings.api_llm_model,
            api_key=current_settings.api_key or None,
        )

    return LLMClientConfig(
        provider="local",
        base_url=current_settings.local_llm_base_url,
        model=current_settings.local_llm_model,
    )


def describe_llm_configuration(settings: Settings | None = None) -> dict[str, str | None]:
    client_config = build_llm_client_config(settings)
    return {
        "provider": client_config.provider,
        "base_url": client_config.base_url,
        "model": client_config.model,
        "api_key_configured": str(bool(client_config.api_key)),
    }