import os

# Set mock API keys so module-level client instantiation does not raise initialization errors
os.environ["GROQ_API_KEY"] = "mock-groq-api-key"
os.environ["TAVILY_API_KEY"] = "mock-tavily-api-key"

import pytest
from unittest.mock import Mock
from agent.schemas import SearchResult, Source

@pytest.fixture
def sample_search_results():
    return [
        SearchResult(
            question="AI trends",
            sources=[
                Source(title="AI Trends 2026", url="https://trends.ai", content="AI is growing fast in 2026."),
                Source(title="AI Computing", url="https://compute.ai", content="GPUs are the key infrastructure.")
            ]
        ),
        SearchResult(
            question="AI hardware",
            sources=[
                Source(title="AI Computing Duplicate", url="https://compute.ai", content="GPUs are the key infrastructure (dup)."),
                Source(title="Custom Silicon", url="https://silicon.ai/custom/", content="TPUs and custom ASICs are rising.")
            ]
        )
    ]

@pytest.fixture
def mock_groq_response():
    def _factory(json_content: str):
        mock_choice = Mock()
        mock_choice.message.content = json_content
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        return mock_response
    return _factory
