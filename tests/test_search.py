import time
from unittest.mock import patch, MagicMock
import pytest
from agent.schemas import SearchResult, Source
from agent.search import _normalize_url, deduplicate_sources, search_questions

def test_normalize_url():
    # 1. Scheme and host lowercase, keep trailing slash if path is empty/root
    assert _normalize_url("HTTP://Example.COM/") == "http://example.com/"
    assert _normalize_url("https://EXAMPLE.com") == "https://example.com"
    
    # 2. Strip trailing slash on path if path is longer than /
    assert _normalize_url("https://example.com/some/path/") == "https://example.com/some/path"
    
    # 3. Clean tracking query parameters
    url_with_tracking = "https://example.com/page?utm_source=twitter&ref=123&q=query&fbclid=xyz"
    normalized = _normalize_url(url_with_tracking)
    # The tracking params (utm_source, ref, fbclid) should be gone, but 'q' should remain.
    assert "q=query" in normalized
    assert "utm_source" not in normalized
    assert "ref" not in normalized
    assert "fbclid" not in normalized
    
    # 4. Handle other query parameters correctly
    assert _normalize_url("https://example.com?a=1&b=2") == "https://example.com?a=1&b=2"

def test_deduplicate_sources():
    # Create mock SearchResult instances
    res1 = SearchResult(
        question="Q1",
        sources=[
            Source(title="Source 1", url="https://example.com/one", content="Content 1"),
            Source(title="Source 2", url="https://example.com/two/", content="Content 2") # trailing slash normalizes to same as next
        ]
    )
    res2 = SearchResult(
        question="Q2",
        sources=[
            Source(title="Source 2 Dup", url="https://example.com/two", content="Content 2 Dup"), # Should be removed (duplicate of res1 source 2)
            Source(title="Source 3", url="https://example.com/three?utm_medium=email", content="Content 3")
        ]
    )
    
    deduped = deduplicate_sources([res1, res2])
    
    # Check res1 sources (both should remain)
    assert len(deduped[0].sources) == 2
    assert deduped[0].sources[0].url == "https://example.com/one"
    assert deduped[0].sources[1].url == "https://example.com/two/"
    
    # Check res2 sources: "Source 2 Dup" should be removed, "Source 3" remains
    assert len(deduped[1].sources) == 1
    assert deduped[1].sources[0].title == "Source 3"
    assert deduped[1].sources[0].url == "https://example.com/three?utm_medium=email"

def test_search_questions_preserves_order():
    # Mock client.search to introduce out-of-order execution times
    def mock_tavily_search(query, max_results=3):
        if "slow" in query:
            time.sleep(0.15)  # Make first query slow
        else:
            time.sleep(0.01)  # Make second query fast
        return {
            "results": [
                {
                    "title": f"Title for {query}",
                    "url": f"https://example.com/{query}",
                    "content": f"Content for {query}"
                }
            ]
        }
        
    with patch("agent.search.client.search", side_effect=mock_tavily_search):
        questions = ["slow query", "fast query"]
        results = search_questions(questions)
        
        # Assert that even though the first query was slow and the second completed first,
        # the returned list matches the input order.
        assert len(results) == 2
        assert results[0].question == "slow query"
        assert results[0].sources[0].title == "Title for slow query"
        assert results[1].question == "fast query"
        assert results[1].sources[0].title == "Title for fast query"
