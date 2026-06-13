from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="MCP Knowledge Hub")
    environment: str = Field(default="development")
    frontend_origin: str = Field(default="http://localhost:5173")

    postgres_dsn: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/knowledge_hub"
    )

    llm_provider: str = Field(default="local")
    local_llm_base_url: str = Field(default="http://127.0.0.1:1234")
    local_llm_model: str = Field(default="gemma-4-12b")
    api_llm_base_url: str = Field(default="https://api.openai.com/v1")
    api_llm_model: str = Field(default="gpt-4.1-mini")
    api_key: str = Field(default="")

    embedding_model: str = Field(default="text-embedding-3-small")
    vector_dim: int = Field(default=1536)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
