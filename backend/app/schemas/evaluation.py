from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from typing_extensions import Annotated


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
CaseKind = Literal["known_answer", "unanswered", "exact_term", "semantic"]
RunMode = Literal["baseline", "candidate", "search_only"]
Decision = Literal["passed", "failed", "inconclusive"]


class EvaluationFilters(BaseModel):
    category_ids: list[int] | None = None
    tag_ids: list[int] | None = None
    project_ids: list[int] | None = None


class EvaluationDefaults(BaseModel):
    limit: int = Field(default=5, ge=1, le=50)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    filters: EvaluationFilters = Field(default_factory=EvaluationFilters)


class ExpectedChunkRef(BaseModel):
    source_public_id: NonEmptyStr | None = None
    source_title: NonEmptyStr | None = None
    chunk_index: int | None = Field(default=None, ge=0)
    page: int | None = Field(default=None, ge=1)
    section: NonEmptyStr | None = None
    content_hash: NonEmptyStr | None = None
    snippet: NonEmptyStr | None = None

    @model_validator(mode="after")
    def require_locator(self) -> "ExpectedChunkRef":
        if (
            self.source_public_id is None
            and self.source_title is None
            and self.content_hash is None
        ):
            raise ValueError("expected chunk needs source_public_id, source_title or content_hash")
        return self


class EvaluationCase(BaseModel):
    id: NonEmptyStr
    question: NonEmptyStr
    kind: CaseKind
    limit: int | None = Field(default=None, ge=1, le=50)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    filters: EvaluationFilters = Field(default_factory=EvaluationFilters)
    expected_chunks: list[ExpectedChunkRef] = Field(default_factory=list)
    expected_category: NonEmptyStr | None = None
    expected_project: NonEmptyStr | None = None
    expected_answer_points: list[NonEmptyStr] = Field(default_factory=list)
    expected_refusal: bool | None = None
    tags: list[NonEmptyStr] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_expectations(self) -> "EvaluationCase":
        if self.kind == "unanswered":
            if self.expected_chunks or self.expected_answer_points:
                raise ValueError("unanswered cases cannot require chunks or answer points")
            if self.expected_refusal is False:
                raise ValueError("unanswered cases must expect a refusal")
            self.expected_refusal = True
        elif not self.expected_chunks and not self.expected_answer_points:
            raise ValueError(f"{self.kind} cases need expected_chunks or expected_answer_points")
        return self


class EvaluationDataset(BaseModel):
    dataset_version: NonEmptyStr
    description: str | None = None
    defaults: EvaluationDefaults = Field(default_factory=EvaluationDefaults)
    cases: list[EvaluationCase] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_cases(self) -> "EvaluationDataset":
        identifiers = [case.id for case in self.cases]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("evaluation case ids must be unique")
        if not any(case.kind == "unanswered" for case in self.cases):
            raise ValueError("evaluation dataset must include an unanswered case")
        return self


class RetrievedChunkRef(BaseModel):
    source_public_id: str
    source_title: str
    chunk_index: int
    page: int | None = None
    section: str | None = None
    content_hash: str
    score: float | None = None


class LatencyMetrics(BaseModel):
    embedding_ms: float = Field(default=0.0, ge=0.0)
    search_ms: float = Field(default=0.0, ge=0.0)
    answer_ms: float = Field(default=0.0, ge=0.0)
    total_ms: float = Field(default=0.0, ge=0.0)


class EvaluationCaseResult(BaseModel):
    case_id: str
    retrieved_chunks: list[RetrievedChunkRef] = Field(default_factory=list)
    answer: str | None = None
    citations: list[str] = Field(default_factory=list)
    recall_at_k: float | None = None
    reciprocal_rank: float | None = None
    answer_correct: bool | None = None
    refusal_correct: bool | None = None
    citations_correct: bool | None = None
    supported_by_sources: bool | None = None
    missing_answer_points: list[str] = Field(default_factory=list)
    citation_mismatches: list[str] = Field(default_factory=list)
    latency_ms: LatencyMetrics = Field(default_factory=LatencyMetrics)
    errors: list[str] = Field(default_factory=list)


class EvaluationRunConfig(BaseModel):
    dataset_version: str
    dataset_hash: str
    git_revision: str | None = None
    retrieval_limit: int
    min_score: float | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None
    embedding_version: str | None = None
    embedding_config_hash: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    mode: RunMode


class ThresholdConfig(BaseModel):
    min_recall_at_k: float | None = Field(default=None, ge=0.0, le=1.0)
    min_mrr: float | None = Field(default=None, ge=0.0, le=1.0)
    min_answer_correct_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    min_refusal_correct_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    min_citation_correct_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    max_embedding_latency_p95_ms: float | None = Field(default=None, gt=0.0)
    max_search_latency_p95_ms: float | None = Field(default=None, gt=0.0)
    max_answer_latency_p95_ms: float | None = Field(default=None, gt=0.0)


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_version: str = "1"
    created_at: datetime
    run_config: EvaluationRunConfig
    case_results: list[EvaluationCaseResult]
    metrics: dict[str, float | None]
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)
    decision: Decision = "inconclusive"
    failures: list[str] = Field(default_factory=list)
