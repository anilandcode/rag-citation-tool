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


class VerificationReport(BaseModel):
    total_citations: int
    verified: int
    accuracy: float
    is_refusal: bool = False
    details: list[VerificationDetail]


class QueryResponse(BaseModel):
    answer: str
    citations: list[CitationDetail]
    verification: VerificationReport
    evaluation: dict | None = None


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
