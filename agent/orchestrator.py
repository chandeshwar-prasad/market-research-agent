import os
import json
from agent.planner import generate_research_questions
from agent.search import search_questions
from agent.synthesize import synthesize_insights
from agent.evaluate import evaluate_insights
from agent.report import save_report
from agent.cache import get_cached, set_cached
from agent.schemas import EvaluationResult, SearchResult

# STAGE 1 HEURISTIC — insight count is a proxy for evidence sufficiency, not the real signal. 
# A future Stage 2 should replace this with evidence_gaps-driven logic once the evaluator emits explicit gap information.
MIN_ACCEPTABLE_INSIGHTS = 4
MAX_RESEARCH_ITERATIONS = 2
MAX_TOTAL_SEARCHES = 10

def run(topic: str, force_fresh: bool = False) -> str:
    # 1. Check cache first
    cached_data = get_cached(topic, force_fresh=force_fresh)
    if cached_data and isinstance(cached_data, dict):
        report_path = cached_data.get("report_path")
        if report_path and os.path.exists(report_path):
            print(f"Cache hit! Returning existing report: {report_path}")
            return report_path

    # Initialize loop state
    all_kept_insights = []
    all_evidence_gaps = []
    all_search_results = []
    all_questions_list = []
    cumulative_searches = 0

    # 2. Iteration Loop
    for iteration in range(1, MAX_RESEARCH_ITERATIONS + 1):
        print(f"\n--- Research Iteration {iteration}/{MAX_RESEARCH_ITERATIONS} ---")
        
        # Formulate topic with gap context on subsequent iterations
        if iteration == 1:
            current_topic = topic
        else:
            current_topic = (
                topic + 
                f"\n\nContext: Previous research found only {len(all_kept_insights)} "
                "well-supported insights. Focus on different angles not yet covered."
            )

        # Planning
        print("Planning research questions...")
        questions = generate_research_questions(current_topic)
        print("=== QUESTIONS ===")
        print(questions.model_dump_json(indent=2))

        # Enforce search budget limit
        num_questions = len(questions.questions)
        if cumulative_searches >= MAX_TOTAL_SEARCHES:
            print(f"Search budget exhausted ({cumulative_searches}/{MAX_TOTAL_SEARCHES}). Breaking.")
            break
        if cumulative_searches + num_questions > MAX_TOTAL_SEARCHES:
            allowed = MAX_TOTAL_SEARCHES - cumulative_searches
            print(f"Trimming questions from {num_questions} to {allowed} to respect search budget.")
            questions.questions = questions.questions[:allowed]
            num_questions = allowed
            if not questions.questions:
                break

        # Searching
        print(f"Searching the live web ({num_questions} queries)...")
        results = search_questions(questions)
        cumulative_searches += num_questions
        all_search_results.extend(results)
        all_questions_list.extend(questions.questions)

        # Synthesizing
        print("Synthesizing insights...")
        insights = synthesize_insights(topic, results)
        print("=== INSIGHTS ===")
        print(insights.model_dump_json(indent=2))

        # Evaluating
        print("Fact-checking and evaluating...")
        evaluated = evaluate_insights(topic, insights, results)
        print("=== EVALUATED INSIGHTS (THIS ITERATION) ===")
        print(evaluated.model_dump_json(indent=2))

        # Accumulating insights and gaps
        all_kept_insights.extend(evaluated.kept_insights)
        all_evidence_gaps.extend(evaluated.evidence_gaps)

        # Check early breakout condition
        print(f"Iteration {iteration} done. Total well-supported insights: {len(all_kept_insights)}/{MIN_ACCEPTABLE_INSIGHTS}")
        if len(all_kept_insights) >= MIN_ACCEPTABLE_INSIGHTS:
            print(f"Success criteria met ({len(all_kept_insights)} >= {MIN_ACCEPTABLE_INSIGHTS}). Breaking loop early.")
            break

    # 3. Save report and Cache results
    final_evaluation = EvaluationResult(
        kept_insights=all_kept_insights,
        evidence_gaps=all_evidence_gaps
    )
    filepath = save_report(topic, final_evaluation, all_search_results)
    
    set_cached(topic, {
        "report_path": filepath,
        "insight_count": len(all_kept_insights),
        "questions": {"questions": all_questions_list},
        "results": [r.model_dump() for r in all_search_results],
        "evaluation": final_evaluation.model_dump()
    })

    return filepath
