from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReindexFilters(BaseModel):
    source_ids: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    batch_size: int = Field(default=50, ge=1, le=1000)


class ReindexReasonCount(BaseModel):
    reason: str
    count: int


class ReindexRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    dry_run: bool
    status: str
    target_config: dict[str, Any]
    sources_total: int
    chunks_total: int
    chunks_reindexed: int = 0
    chunks_reused: int = 0
    chunks_failed: int = 0
    reasons: dict[str, int] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
