from pydantic import BaseModel, Field
from typing import Literal

class ResearchQuestions(BaseModel):
    questions: list[str] = Field(..., min_length=1, max_length=5)

class Source(BaseModel):
    title: str
    url: str
    content: str = ""

class SearchResult(BaseModel):
    question: str
    sources: list[Source]

class Insight(BaseModel):
    text: str
    cited_url: str | None = None

class SynthesisResult(BaseModel):
    insights: list[Insight]

class EvaluatedInsight(BaseModel):
    text: str
    cited_url: str | None
    verdict: Literal["Supported", "Partially supported", "Unsupported", "Contradicted", "No citation found"]
    decision: Literal["KEEP", "KEEP WITH DOWNGRADE", "REMOVE"]
    confidence: Literal["High", "Medium", "Low"]

class EvaluationResult(BaseModel):
    kept_insights: list[EvaluatedInsight]
    evidence_gaps: list[str] = Field(default_factory=list)

class QAAnswer(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)

