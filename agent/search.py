import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def search_questions(questions_text):
    questions = []
    for line in questions_text.split("\n"):
        line = line.strip()
        if line and line[0].isdigit():
            question = line.split(".", 1)[1].strip()
            questions.append(question)

    results = []
    for i, question in enumerate(questions, 1):
        print(f"Searching ({i}/{len(questions)}): {question[:60]}...")
        try:
            response = client.search(query=question, max_results=3)
            sources = response.get("results", [])
        except Exception as e:
            print(f"Error searching for '{question[:60]}': {e}")
            sources = []
            
        results.append({
            "question": question,
            "sources": sources
        })

    return results