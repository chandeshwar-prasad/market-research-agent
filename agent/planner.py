import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_research_questions(topic):
    prompt = f"""You are a market research planner. Given a topic, competitor, or niche, break it down into 3 to 5 focused research sub-questions that together would produce a well-rounded market/trend report.

Topic: {topic}

Return ONLY a numbered list of the sub-questions, nothing else."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating research questions: {e}")
        return f"1. What is the market overview for {topic}?\n2. Who are the key competitors in the {topic} space?\n3. What are the major trends and challenges in {topic}?"