from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    doc_collection: str = "default"


class CitationDetail(BaseModel):
    source: str
    page: str
    claim: str


class VerificationDetail(BaseModel):
    citation: CitationDetail
    supported: bool
    source_text: str
    # Calibrated support probability from the decision model (Jev); null when
    # the verdict came from the LLM or heuristic fallback path.
    confidence: float | None = None


class VerificationReport(BaseModel):
    total_citations: int
    verified: int
    accuracy: float
    is_refusal: bool = False
    details: list[VerificationDetail]
    # "jev" = batched typed decisions (System One), "llm" = frontier model per
    # claim, "heuristic" = deterministic fallback.
    engine: str = "llm"
    decision_cost: float | None = None
    decision_id: str = ""
    # "typesafe" = first-party API, "gateway" = OpenRouter/other reseller.
    decision_route: str = ""
    min_confidence: float | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[CitationDetail]
    verification: VerificationReport
    evaluation: dict | None = None
    # System One gate telemetry: what Jev decided about the query before
    # generation (answerability, retrieval route, complexity). Null when the
    # decision layer is disabled or unavailable.
    gate: dict | None = None


class IngestResponse(BaseModel):
    status: str
    documents_indexed: int
    chunks_created: int


class AuditReportResponse(BaseModel):
    collection: str
    baseline_metrics: dict
    optimized_metrics: dict
    improvements: list[str]
    sample_questions: list[dict] = []
    summary: str
