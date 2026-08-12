import time
from unittest.mock import patch
from agent.schemas import ResearchQuestions
from agent.search import search_questions

# We mock client.search to introduce artificial delays based on the query to cause out-of-order completions.
# The first question takes the longest, but should still finish and be positioned at index 0.
def mock_search_impl(query, max_results=3):
    if "first" in query:
        time.sleep(0.5)  # long delay
    elif "second" in query:
        time.sleep(0.1)  # short delay
    else:
        time.sleep(0.01) # very short delay
    return {"results": [{"title": f"Title for {query}", "url": f"https://x.com/{query}", "content": "mocked"}]}

@patch('agent.search.client.search', side_effect=mock_search_impl)
def test_parallel_ordering(mock_search):
    questions_input = ResearchQuestions(questions=["first question", "second question", "third question"])
    
    start_time = time.time()
    results = search_questions(questions_input)
    elapsed = time.time() - start_time
    
    print(f"Elapsed: {elapsed:.2f}s")
    print(f"Question order returned:")
    for idx, r in enumerate(results):
        print(f"  Result {idx}: {r.question}")
        
    assert results[0].question == "first question"
    assert results[1].question == "second question"
    assert results[2].question == "third question"
    print("\n[SUCCESS] Parallel order preservation tests passed successfully!")

if __name__ == "__main__":
    test_parallel_ordering()
