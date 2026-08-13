import pytest
from pydantic import ValidationError
from agent.schemas import (
    ResearchQuestions,
    Source,
    SearchResult,
    Insight,
    SynthesisResult,
    EvaluatedInsight,
    EvaluationResult
)

def test_research_questions_validation():
    # Valid configurations
    rq = ResearchQuestions(questions=["What is the size of the AI market?"])
    assert len(rq.questions) == 1
    
    rq5 = ResearchQuestions(questions=["q1", "q2", "q3", "q4", "q5"])
    assert len(rq5.questions) == 5

    # Invalid: empty questions list
    with pytest.raises(ValidationError):
        ResearchQuestions(questions=[])

    # Invalid: too many questions
    with pytest.raises(ValidationError):
        ResearchQuestions(questions=["1", "2", "3", "4", "5", "6"])

def test_source_validation():
    # Valid
    src = Source(title="Market Size", url="https://example.com/data")
    assert src.title == "Market Size"
    assert src.url == "https://example.com/data"
    assert src.content == ""  # default value

    # Custom content
    src_custom = Source(title="Market Size", url="https://example.com/data", content="Custom body")
    assert src_custom.content == "Custom body"

def test_search_result_validation():
    # Valid
    src = Source(title="Title", url="https://example.com")
    res = SearchResult(question="What is X?", sources=[src])
    assert res.question == "What is X?"
    assert res.sources[0].url == "https://example.com"

def test_insight_validation():
    # Valid
    ins = Insight(text="Insight text", cited_url="https://example.com")
    assert ins.text == "Insight text"
    assert ins.cited_url == "https://example.com"

    # Valid with cited_url as None
    ins_no_url = Insight(text="Insight text", cited_url=None)
    assert ins_no_url.cited_url is None

def test_synthesis_result_validation():
    ins = Insight(text="Insight text", cited_url="https://example.com")
    syn = SynthesisResult(insights=[ins])
    assert len(syn.insights) == 1
    assert syn.insights[0].text == "Insight text"

def test_evaluated_insight_validation():
    # Valid
    ei = EvaluatedInsight(
        text="A test insight",
        cited_url="https://example.com",
        verdict="Supported",
        decision="KEEP",
        confidence="High"
    )
    assert ei.verdict == "Supported"
    assert ei.decision == "KEEP"
    assert ei.confidence == "High"

    # Invalid verdict
    with pytest.raises(ValidationError):
        EvaluatedInsight(
            text="A test insight",
            cited_url="https://example.com",
            verdict="Invalid Verdict",
            decision="KEEP",
            confidence="High"
        )

    # Invalid decision
    with pytest.raises(ValidationError):
        EvaluatedInsight(
            text="A test insight",
            cited_url="https://example.com",
            verdict="Supported",
            decision="DELETE_THIS",
            confidence="High"
        )

    # Invalid confidence
    with pytest.raises(ValidationError):
        EvaluatedInsight(
            text="A test insight",
            cited_url="https://example.com",
            verdict="Supported",
            decision="KEEP",
            confidence="VeryHigh"
        )

def test_evaluation_result_validation():
    ei = EvaluatedInsight(
        text="A test insight",
        cited_url="https://example.com",
        verdict="Supported",
        decision="KEEP",
        confidence="High"
    )
    ev = EvaluationResult(kept_insights=[ei])
    assert len(ev.kept_insights) == 1
    assert ev.evidence_gaps == []  # default value
