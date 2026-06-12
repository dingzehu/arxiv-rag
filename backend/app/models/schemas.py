from pydantic import BaseModel, field_validator

class IngestRequest(BaseModel):
    query: str
    max_papers: int = 20

    @field_validator("max_papers")
    @classmethod
    def cap_max_papers(cls, v: int) -> int:
        if v > 100:
            raise ValueError("max_papers cannot exceed 100")
        return v

class SearchRequest(BaseModel):
    question: str
    top_k: int = 5

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Question can not be empty")
        return v.strip()

class EvaluateRequest(BaseModel):
    question: str
    expected_answer: str

class SourceChunk(BaseModel):
    arxiv_id: str
    title: str
    authors: str
    chunk_text: str
    similarity_score: float

class SearchResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    duration_ms: int
    mlflow_run_id: str

class EvaluateResponse(BaseModel):
    question: str
    expected_answer: str
    actual_answer: str
    score: float
    reasoning: str
    sources: list[SourceChunk]
    duration_ms: int
    mlflow_run_id: str

class BatchEvaluateResponse(BaseModel):
    total_questions: int
    average_score: float
    scores_by_difficulty: dict[str, float]
    mlflow_experiment_id: str
    duration_seconds: float

class IngestResponse(BaseModel):
    papers_ingested: int
    chunks_created: int
    duration_seconds: float
    mlflow_run_id: str
