import os
import json
from groq import Groq
from dotenv import load_dotenv
from agent.schemas import ResearchQuestions

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_research_questions(topic: str) -> ResearchQuestions:
    prompt = f"""You are a market research planner. Given a topic, competitor, or niche, break it down into 3 to 5 focused research sub-questions that together would produce a well-rounded market/trend report.

Topic: {topic}

You must return your response as a JSON object matching this schema:
{{
  "questions": ["question 1", "question 2", ...]
}}
Return ONLY valid JSON, nothing else."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=500,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )
        data = json.loads(response.choices[0].message.content)
        return ResearchQuestions.model_validate(data)
    except Exception as e:
        print(f"Error generating research questions: {e}")
        # Keep existing fallback logic, but return Pydantic object
        return ResearchQuestions(questions=[
            f"What is the market overview for {topic}?",
            f"Who are the key competitors in the {topic} space?",
            f"What are the major trends and challenges in {topic}?"
        ])