from dotenv import load_dotenv
load_dotenv()

import agent.orchestrator
from agent.cache import get_cached
from agent.qa import answer_question

topic = input("Enter a topic, competitor, or niche to research: ")

filepath = agent.orchestrator.run(topic)
print(f"\n=== REPORT SAVED ===\n{filepath}")

# Retrieve cached execution data
cached_data = get_cached(topic)
if cached_data and "results" in cached_data:
    results = cached_data["results"]
    print("\n=== Phase 3: Interactive Follow-up Q&A ===")
    while True:
        question = input("\nAsk a follow-up question (or press enter to exit): ").strip()
        if not question:
            print("Exiting Q&A session. Goodbye!")
            break
        print("Answering question...")
        qa_answer = answer_question(topic, question, results)
        print("\n--- Answer ---")
        print(qa_answer.answer)
        if qa_answer.citations:
            print("\n--- Citations ---")
            for citation in qa_answer.citations:
                print(f"- {citation}")