from unittest.mock import patch, MagicMock
import pytest
from agent.schemas import (
    Source,
    SearchResult,
    Insight,
    SynthesisResult,
    EvaluatedInsight,
    EvaluationResult
)
from agent.evaluate import (
    _extract_relevant_passage,
    _extract_citations,
    evaluate_insights,
    _classify_one
)

def test_extract_relevant_passage_short():
    short_content = "This is a short text under 1500 characters."
    claim = "short text"
    passage = _extract_relevant_passage(short_content, claim)
    assert passage == short_content

def test_extract_relevant_passage_long_with_overlap():
    # Construct a long text where only a chunk far down the text contains overlap
    filler_chunk = "This is some filler content that has no overlapping keywords. " * 30  # ~1800 chars
    relevant_chunk = "SpecialKeywordX is the key trend in 2026."
    long_content = filler_chunk + relevant_chunk
    
    claim = "What is SpecialKeywordX?"
    passage = _extract_relevant_passage(long_content, claim)
    
    # Verify that the relevant chunk containing "SpecialKeywordX" was selected
    assert "SpecialKeywordX" in passage

def test_extract_relevant_passage_fallback():
    # If no keyword overlap exists, it should fallback to the first 1500 chars of the content.
    long_content = "Abc " * 500  # 2000 chars
    claim = "xyz"
    passage = _extract_relevant_passage(long_content, claim)
    
    assert len(passage) <= 1500
    assert passage.startswith("Abc")

def test_extract_citations():
    insights_text = """
    1. AI chips are in high demand (Source: https://chips.com/report)
    2. Nvidia dominates GPU market
    3. Quantum computing is far (Source: https://quantum.org)
    """
    citations = _extract_citations(insights_text)
    
    assert len(citations) == 3
    
    # 1. Has source
    assert citations[0]["text"] == "AI chips are in high demand"
    assert citations[0]["cited_url"] == "https://chips.com/report"
    
    # 2. No source
    assert citations[1]["text"] == "Nvidia dominates GPU market"
    assert citations[1]["cited_url"] is None
    
    # 3. Has source
    assert citations[2]["text"] == "Quantum computing is far"
    assert citations[2]["cited_url"] == "https://quantum.org"

def test_evaluate_insights_integration(mock_groq_response):
    # Setup test input
    insights_input = SynthesisResult(
        insights=[
            Insight(text="AI chips are hot", cited_url="https://chips.com"),
            Insight(text="Quantum is cold", cited_url="https://quantum.com")
        ]
    )
    
    results = [
        SearchResult(
            question="chip trend",
            sources=[Source(title="Chips", url="https://chips.com", content="AI chips are hot now.")]
        ),
        SearchResult(
            question="quantum trend",
            sources=[Source(title="Quantum", url="https://quantum.com", content="Quantum is cold now.")]
        )
    ]
    
    # We will mock the two calls to _call_groq_completions:
    # First call: return Supported/KEEP
    # Second call: return Unsupported/REMOVE
    res_keep = mock_groq_response('{"verdict": "Supported", "decision": "KEEP", "confidence": "High"}')
    res_remove = mock_groq_response('{"verdict": "Unsupported", "decision": "REMOVE", "confidence": "Low"}')
    
    with patch("agent.evaluate._call_groq_completions", side_effect=[res_keep, res_remove]) as mock_call:
        eval_result = evaluate_insights("AI trends", insights_input, results)
        
        # Verify call counts and structure
        assert mock_call.call_count == 2
        
        # Verify REMOVE decision drops the insight and logs it as an evidence gap
        assert len(eval_result.kept_insights) == 1
        assert eval_result.kept_insights[0].text == "AI chips are hot"
        assert eval_result.kept_insights[0].decision == "KEEP"
        
        assert len(eval_result.evidence_gaps) == 1
        assert "Quantum is cold" in eval_result.evidence_gaps[0]

def test_evaluate_insights_raw_string_input(mock_groq_response):
    # Test evaluation when input is a raw string instead of SynthesisResult
    insights_input = "1. AI chips are hot (Source: https://chips.com)"
    results = [
        SearchResult(
            question="chip trend",
            sources=[Source(title="Chips", url="https://chips.com", content="AI chips are hot now.")]
        )
    ]
    
    res_keep = mock_groq_response('{"verdict": "Supported", "decision": "KEEP", "confidence": "High"}')
    
    with patch("agent.evaluate._call_groq_completions", return_value=res_keep) as mock_call:
        eval_result = evaluate_insights("AI trends", insights_input, results)
        
        assert mock_call.call_count == 1
        assert len(eval_result.kept_insights) == 1
        assert eval_result.kept_insights[0].text == "AI chips are hot"
        assert eval_result.kept_insights[0].cited_url == "https://chips.com"
        assert eval_result.kept_insights[0].decision == "KEEP"
