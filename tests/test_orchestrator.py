import os
from unittest.mock import patch, MagicMock
import pytest
from agent.schemas import (
    ResearchQuestions,
    SearchResult,
    Source,
    Insight,
    SynthesisResult,
    EvaluatedInsight,
    EvaluationResult
)
import agent.orchestrator

def test_orchestrator_cache_hit():
    # Setup cache mock to return a path
    mock_cached = {"report_path": "outputs/report_cached.md", "insight_count": 5}
    
    with patch("agent.orchestrator.get_cached", return_value=mock_cached) as mock_get, \
         patch("os.path.exists", return_value=True):
         
        filepath = agent.orchestrator.run("AI trends", force_fresh=False)
        assert filepath == "outputs/report_cached.md"
        mock_get.assert_called_once_with("AI trends", force_fresh=False)

def test_orchestrator_iteration_1_success():
    # Setup mocks for planning, search, synthesis, evaluation, and reporting
    questions = ResearchQuestions(questions=["Q1", "Q2"])
    results = [SearchResult(question="Q1", sources=[])]
    insights = SynthesisResult(insights=[Insight(text="Insight 1")])
    
    # 4 kept insights (reaches threshold of MIN_ACCEPTABLE_INSIGHTS)
    evaluated = EvaluationResult(
        kept_insights=[
            EvaluatedInsight(text="I1", cited_url="url", verdict="Supported", decision="KEEP", confidence="High"),
            EvaluatedInsight(text="I2", cited_url="url", verdict="Supported", decision="KEEP", confidence="High"),
            EvaluatedInsight(text="I3", cited_url="url", verdict="Supported", decision="KEEP", confidence="High"),
            EvaluatedInsight(text="I4", cited_url="url", verdict="Supported", decision="KEEP", confidence="High"),
        ],
        evidence_gaps=[]
    )
    
    with patch("agent.orchestrator.get_cached", return_value=None), \
         patch("agent.orchestrator.generate_research_questions", return_value=questions) as mock_plan, \
         patch("agent.orchestrator.search_questions", return_value=results) as mock_search, \
         patch("agent.orchestrator.synthesize_insights", return_value=insights), \
         patch("agent.orchestrator.evaluate_insights", return_value=evaluated) as mock_eval, \
         patch("agent.orchestrator.save_report", return_value="outputs/report.md") as mock_save, \
         patch("agent.orchestrator.set_cached") as mock_set:
         
        filepath = agent.orchestrator.run("AI trends")
        
        assert filepath == "outputs/report.md"
        # Since it met threshold of 4, it should break after 1 iteration
        mock_plan.assert_called_once_with("AI trends")
        assert mock_search.call_count == 1
        assert mock_eval.call_count == 1
        mock_save.assert_called_once()
        mock_set.assert_called_once()
        called_args = mock_set.call_args[0]
        assert called_args[0] == "AI trends"
        payload = called_args[1]
        assert payload["report_path"] == "outputs/report.md"
        assert payload["insight_count"] == 4
        assert "questions" in payload
        assert "results" in payload
        assert "evaluation" in payload

def test_orchestrator_iteration_2_fallback():
    # Setup mocks:
    # Iteration 1 returns 2 insights (under threshold)
    # Iteration 2 returns 2 insights, leading to total of 4
    questions1 = ResearchQuestions(questions=["Q1"])
    questions2 = ResearchQuestions(questions=["Q2"])
    
    results = [SearchResult(question="Q1", sources=[])]
    insights = SynthesisResult(insights=[Insight(text="I")])
    
    evaluated1 = EvaluationResult(
        kept_insights=[
            EvaluatedInsight(text="I1", cited_url="url", verdict="Supported", decision="KEEP", confidence="High"),
            EvaluatedInsight(text="I2", cited_url="url", verdict="Supported", decision="KEEP", confidence="High"),
        ],
        evidence_gaps=[]
    )
    evaluated2 = EvaluationResult(
        kept_insights=[
            EvaluatedInsight(text="I3", cited_url="url", verdict="Supported", decision="KEEP", confidence="High"),
            EvaluatedInsight(text="I4", cited_url="url", verdict="Supported", decision="KEEP", confidence="High"),
        ],
        evidence_gaps=[]
    )
    
    with patch("agent.orchestrator.get_cached", return_value=None), \
         patch("agent.orchestrator.generate_research_questions", side_effect=[questions1, questions2]) as mock_plan, \
         patch("agent.orchestrator.search_questions", return_value=results) as mock_search, \
         patch("agent.orchestrator.synthesize_insights", return_value=insights), \
         patch("agent.orchestrator.evaluate_insights", side_effect=[evaluated1, evaluated2]) as mock_eval, \
         patch("agent.orchestrator.save_report", return_value="outputs/report_two.md") as mock_save, \
         patch("agent.orchestrator.set_cached") as mock_set:
         
        filepath = agent.orchestrator.run("AI trends")
        
        assert filepath == "outputs/report_two.md"
        assert mock_plan.call_count == 2
        # Check topic augmentation for second planning call
        mock_plan.assert_any_call("AI trends")
        mock_plan.assert_any_call(
            "AI trends\n\nContext: Previous research found only 2 well-supported insights. "
            "Focus on different angles not yet covered."
        )
        assert mock_search.call_count == 2
        assert mock_eval.call_count == 2
        
        # Verify that accumulated result passed to save_report contains 4 insights
        called_eval = mock_save.call_args[0][1]
        assert len(called_eval.kept_insights) == 4
        assert [ei.text for ei in called_eval.kept_insights] == ["I1", "I2", "I3", "I4"]

def test_orchestrator_search_budget_enforcement():
    # Set MAX_TOTAL_SEARCHES temporarily to 8 for this test
    # Iteration 1 generates 5 questions (budget remaining: 3)
    # Iteration 2 generates 5 questions (trimmed to 3)
    questions1 = ResearchQuestions(questions=["Q1", "Q2", "Q3", "Q4", "Q5"])
    questions2 = ResearchQuestions(questions=["Q6", "Q7", "Q8", "Q9", "Q10"])
    
    results = [SearchResult(question="Q", sources=[])]
    insights = SynthesisResult(insights=[])
    
    # We return fewer than 4 insights on Iteration 1 so it continues to Iteration 2
    evaluated1 = EvaluationResult(kept_insights=[], evidence_gaps=[])
    evaluated2 = EvaluationResult(kept_insights=[], evidence_gaps=[])
    
    with patch("agent.orchestrator.MAX_TOTAL_SEARCHES", 8), \
         patch("agent.orchestrator.get_cached", return_value=None), \
         patch("agent.orchestrator.generate_research_questions", side_effect=[questions1, questions2]), \
         patch("agent.orchestrator.search_questions", return_value=results) as mock_search, \
         patch("agent.orchestrator.synthesize_insights", return_value=insights), \
         patch("agent.orchestrator.evaluate_insights", side_effect=[evaluated1, evaluated2]), \
         patch("agent.orchestrator.save_report", return_value="outputs/report.md"):
         
        agent.orchestrator.run("AI trends")
        
        # Iteration 1: search_questions called with all 5 questions
        first_call = mock_search.call_args_list[0][0][0]
        assert len(first_call.questions) == 5
        
        # Iteration 2: search_questions called with only 3 questions (trimmed from 5 to fit remaining budget)
        second_call = mock_search.call_args_list[1][0][0]
        assert len(second_call.questions) == 3
        assert second_call.questions == ["Q6", "Q7", "Q8"]
