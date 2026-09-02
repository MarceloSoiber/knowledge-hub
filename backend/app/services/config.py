from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from ..db.models import AppConfig
from ..core.settings import Settings, get_settings
from ..schemas.configuration import AIConfigurationRead, AIConfigurationWrite


AUTH_TOKEN_KEY = "auth_token"
LLM_PROVIDER_KEY = "llm_provider"
LOCAL_LLM_BASE_URL_KEY = "local_llm_base_url"
LOCAL_LLM_MODEL_KEY = "local_llm_model"
API_LLM_BASE_URL_KEY = "api_llm_base_url"
API_LLM_MODEL_KEY = "api_llm_model"
API_KEY_KEY = "api_key_encrypted"
EMBEDDING_MODEL_KEY = "embedding_model"
VECTOR_DIM_KEY = "vector_dim"

AI_CONFIG_KEYS = (
    LLM_PROVIDER_KEY,
    LOCAL_LLM_BASE_URL_KEY,
    LOCAL_LLM_MODEL_KEY,
    API_LLM_BASE_URL_KEY,
    API_LLM_MODEL_KEY,
    EMBEDDING_MODEL_KEY,
    VECTOR_DIM_KEY,
)


class ConfigurationError(ValueError):
    pass


class VectorDimensionChangeRequired(ConfigurationError):
    pass


async def get_config_value(session: AsyncSession, key: str) -> str | None:
    value = await session.scalar(select(AppConfig.value).where(AppConfig.key == key))
    return value.strip() if value else None


async def get_auth_token(session: AsyncSession) -> str:
    token = await get_config_value(session, AUTH_TOKEN_KEY)
    return token or ""


async def set_config_value(session: AsyncSession, key: str, value: str) -> None:
    statement = (
        insert(AppConfig)
        .values(key=key, value=value)
        .on_conflict_do_update(
            index_elements=[AppConfig.key],
            set_={"value": value, "updated_at": func.now()},
        )
    )
    await session.execute(statement)
    await session.commit()


async def get_config_values(session: AsyncSession, keys: tuple[str, ...]) -> dict[str, str]:
    rows = await session.execute(select(AppConfig.key, AppConfig.value).where(AppConfig.key.in_(keys)))
    return {key: value.strip() for key, value in rows.all() if value.strip()}


async def set_config_values(session: AsyncSession, values: dict[str, str]) -> None:
    try:
        for key, value in values.items():
            statement = (
                insert(AppConfig)
                .values(key=key, value=value)
                .on_conflict_do_update(
                    index_elements=[AppConfig.key],
                    set_={"value": value, "updated_at": func.now()},
                )
            )
            await session.execute(statement)
        await session.commit()
    except Exception:
        await session.rollback()
        raise


def _fernet(settings: Settings) -> Fernet:
    if not settings.config_encryption_key:
        raise ConfigurationError(
            "CONFIG_ENCRYPTION_KEY is required to save an API key through the portal."
        )
    try:
        return Fernet(settings.config_encryption_key.encode())
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("CONFIG_ENCRYPTION_KEY is invalid.") from exc


def _decrypt_api_key(value: str, settings: Settings) -> str:
    try:
        return _fernet(settings).decrypt(value.encode()).decode()
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise ConfigurationError("The saved API key could not be decrypted.") from exc


async def get_effective_ai_configuration(
    session: AsyncSession, settings: Settings | None = None
) -> AIConfigurationRead:
    resolved = settings or get_settings()
    values = await get_config_values(session, AI_CONFIG_KEYS + (API_KEY_KEY,))
    defaults = {
        LLM_PROVIDER_KEY: resolved.llm_provider,
        LOCAL_LLM_BASE_URL_KEY: resolved.local_llm_base_url,
        LOCAL_LLM_MODEL_KEY: resolved.local_llm_model,
        API_LLM_BASE_URL_KEY: resolved.api_llm_base_url,
        API_LLM_MODEL_KEY: resolved.api_llm_model,
        EMBEDDING_MODEL_KEY: resolved.embedding_model,
        VECTOR_DIM_KEY: str(resolved.vector_dim),
    }
    effective = {key: values.get(key, default) for key, default in defaults.items()}
    api_key_configured = bool(values.get(API_KEY_KEY) or resolved.api_key)
    return AIConfigurationRead(
        llm_provider=effective[LLM_PROVIDER_KEY].lower(),
        local_llm_base_url=effective[LOCAL_LLM_BASE_URL_KEY],
        local_llm_model=effective[LOCAL_LLM_MODEL_KEY],
        api_llm_base_url=effective[API_LLM_BASE_URL_KEY],
        api_llm_model=effective[API_LLM_MODEL_KEY],
        api_key_configured=api_key_configured,
        embedding_model=effective[EMBEDDING_MODEL_KEY],
        vector_dim=int(effective[VECTOR_DIM_KEY]),
        origins={key: "portal" if key in values else "environment" for key in defaults},
    )


async def resolve_ai_settings(session: AsyncSession, settings: Settings | None = None) -> Settings:
    resolved = settings or get_settings()
    values = await get_config_values(session, AI_CONFIG_KEYS + (API_KEY_KEY,))
    api_key = resolved.api_key
    if encrypted_key := values.get(API_KEY_KEY):
        api_key = _decrypt_api_key(encrypted_key, resolved)
    updates: dict[str, str | int] = {
        key: values[key] for key in AI_CONFIG_KEYS if key in values
    }
    if LLM_PROVIDER_KEY in updates:
        updates[LLM_PROVIDER_KEY] = str(updates[LLM_PROVIDER_KEY]).lower()
    if VECTOR_DIM_KEY in updates:
        updates[VECTOR_DIM_KEY] = int(str(updates[VECTOR_DIM_KEY]))
    updates["api_key"] = api_key
    return resolved.model_copy(update=updates)


async def update_ai_configuration(
    session: AsyncSession,
    payload: AIConfigurationWrite,
    settings: Settings | None = None,
) -> AIConfigurationRead:
    resolved = settings or get_settings()
    current = await get_effective_ai_configuration(session, resolved)
    if payload.vector_dim != current.vector_dim:
        raise VectorDimensionChangeRequired(
            "VECTOR_DIM requires a pgvector migration and reindexation; it cannot be changed here."
        )

    api_key_configured = current.api_key_configured
    updates = {
        LLM_PROVIDER_KEY: payload.llm_provider,
        LOCAL_LLM_BASE_URL_KEY: str(payload.local_llm_base_url).rstrip("/"),
        LOCAL_LLM_MODEL_KEY: payload.local_llm_model.strip(),
        API_LLM_BASE_URL_KEY: str(payload.api_llm_base_url).rstrip("/"),
        API_LLM_MODEL_KEY: payload.api_llm_model.strip(),
        EMBEDDING_MODEL_KEY: payload.embedding_model.strip(),
        VECTOR_DIM_KEY: str(payload.vector_dim),
    }
    if payload.clear_api_key:
        updates[API_KEY_KEY] = ""
        api_key_configured = False
    elif payload.api_key is not None:
        updates[API_KEY_KEY] = _fernet(resolved).encrypt(payload.api_key.strip().encode()).decode()
        api_key_configured = True

    if payload.llm_provider == "api" and not api_key_configured:
        raise ConfigurationError("An API key is required when the API provider is selected.")

    await set_config_values(session, updates)
    return await get_effective_ai_configuration(session, resolved)
