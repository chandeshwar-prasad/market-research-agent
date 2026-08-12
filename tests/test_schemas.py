import pytest
from pydantic import ValidationError
from agent.schemas import ResearchQuestions, EvaluatedInsight

def test_research_questions_rejects_empty():
    with pytest.raises(ValidationError):
        ResearchQuestions(questions=[])

def test_research_questions_rejects_too_many():
    with pytest.raises(ValidationError):
        ResearchQuestions(questions=["1", "2", "3", "4", "5", "6"])

def test_evaluated_insight_rejects_bad_confidence():
    with pytest.raises(ValidationError):
        EvaluatedInsight(
            text="x",
            cited_url=None,
            verdict="Supported",
            decision="KEEP",
            confidence="VeryHigh"
        )

def test_evaluated_insight_accepts_good_confidence():
    insight = EvaluatedInsight(
        text="x",
        cited_url=None,
        verdict="Supported",
        decision="KEEP",
        confidence="High"
    )
    assert insight.confidence == "High"
