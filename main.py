from dotenv import load_dotenv
load_dotenv()

import agent.orchestrator

topic = input("Enter a topic, competitor, or niche to research: ")

filepath = agent.orchestrator.run(topic)
print(f"\n=== REPORT SAVED ===\n{filepath}")