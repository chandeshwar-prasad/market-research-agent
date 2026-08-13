from unittest.mock import patch
import pytest
from agent.schemas import SearchResult, Source, QAAnswer
from agent.qa import answer_question

def test_answer_question_no_results():
    res = answer_question("AI trends", "What's new?", [])
    assert isinstance(res, QAAnswer)
    assert "No research results or source documents are available" in res.answer
    assert res.citations == []

def test_answer_question_no_content():
    results = [
        SearchResult(
            question="AI trends",
            sources=[Source(title="AI Trends 2026", url="https://trends.ai", content="")]
        )
    ]
    res = answer_question("AI trends", "What's new?", results)
    assert isinstance(res, QAAnswer)
    assert "No source text content is available" in res.answer
    assert res.citations == []

def test_answer_question_with_results(mock_groq_response):
    results = [
        SearchResult(
            question="AI trends",
            sources=[
                Source(title="AI Trends 2026", url="https://trends.ai", content="AI is growing fast in 2026.")
            ]
        )
    ]
    
    mock_res = mock_groq_response('{"answer": "AI is growing rapidly in 2026.", "citations": ["https://trends.ai"]}')
    
    with patch("agent.qa._call_groq_completions", return_value=mock_res) as mock_call:
        res = answer_question("AI trends", "What is the speed of AI growth?", results)
        
        assert mock_call.call_count == 1
        assert isinstance(res, QAAnswer)
        assert res.answer == "AI is growing rapidly in 2026."
        assert res.citations == ["https://trends.ai"]

def test_answer_question_error_handling():
    results = [
        SearchResult(
            question="AI trends",
            sources=[
                Source(title="AI Trends 2026", url="https://trends.ai", content="AI is growing fast in 2026.")
            ]
        )
    ]
    
    with patch("agent.qa._call_groq_completions", side_effect=Exception("API limit exceeded")) as mock_call:
        res = answer_question("AI trends", "Is AI growing?", results)
        
        assert mock_call.call_count == 1
        assert isinstance(res, QAAnswer)
        assert "Error: Unable to generate answer" in res.answer
        assert "API limit exceeded" in res.answer
        assert res.citations == []
