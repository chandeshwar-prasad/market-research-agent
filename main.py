from dotenv import load_dotenv
load_dotenv()

from agent.report import save_report
from agent.planner import generate_research_questions
from agent.search import search_questions
from agent.synthesize import synthesize_insights
from agent.evaluate import evaluate_insights

topic = input("Enter a topic, competitor, or niche to research: ")
questions_text = generate_research_questions(topic)
print("=== QUESTIONS ===")
print(questions_text)

results = search_questions(questions_text)
print("\n=== SEARCH RESULTS ===")
for item in results:
    print(f"\nQ: {item['question']}")
    for source in item['sources']:
        print(f"  - {source['title']} ({source['url']})")

insights = synthesize_insights(topic, results)
print("\n=== INSIGHTS ===")
print(insights)

evaluated = evaluate_insights(topic, insights, results)
print("\n=== EVALUATED INSIGHTS ===")
print(evaluated)

filepath = save_report(topic, evaluated, results)
print(f"\n=== REPORT SAVED ===\n{filepath}")