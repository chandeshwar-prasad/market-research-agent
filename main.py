import json
from dotenv import load_dotenv
load_dotenv()

from agent.report import save_report
from agent.planner import generate_research_questions
from agent.search import search_questions
from agent.synthesize import synthesize_insights
from agent.evaluate import evaluate_insights

topic = input("Enter a topic, competitor, or niche to research: ")

questions = generate_research_questions(topic)
print("=== QUESTIONS ===")
print(questions.model_dump_json(indent=2))

results = search_questions(questions)
print("\n=== SEARCH RESULTS ===")
print(json.dumps([r.model_dump() for r in results], indent=2))

insights = synthesize_insights(topic, results)
print("\n=== INSIGHTS ===")
print(insights.model_dump_json(indent=2))

evaluated = evaluate_insights(topic, insights, results)
print("\n=== EVALUATED INSIGHTS ===")
print(evaluated.model_dump_json(indent=2))

filepath = save_report(topic, evaluated, results)
print(f"\n=== REPORT SAVED ===\n{filepath}")