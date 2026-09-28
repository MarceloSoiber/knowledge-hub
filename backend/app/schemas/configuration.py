from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


ConfigOrigin = Literal["environment", "portal"]
LLMProvider = Literal["local", "api"]


class AIConfigurationRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm_provider: LLMProvider
    local_llm_base_url: str
    local_llm_model: str
    api_llm_base_url: str
    api_llm_model: str
    api_key_configured: bool
    embedding_model: str
    vector_dim: int
    origins: dict[str, ConfigOrigin]


class AIConfigurationWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm_provider: LLMProvider
    local_llm_base_url: HttpUrl
    local_llm_model: str = Field(min_length=1, max_length=255)
    api_llm_base_url: HttpUrl
    api_llm_model: str = Field(min_length=1, max_length=255)
    embedding_model: str = Field(min_length=1, max_length=255)
    api_key: str | None = Field(default=None, max_length=4096)
    clear_api_key: bool = False
    vector_dim: int = Field(gt=0, le=65535)

    @model_validator(mode="after")
    def validate_api_key_change(self) -> "AIConfigurationWrite":
        if self.api_key is not None and not self.api_key.strip():
            raise ValueError("API key must not be blank when provided.")
        if self.api_key is not None and self.clear_api_key:
            raise ValueError("API key cannot be replaced and cleared at the same time.")
        return self
