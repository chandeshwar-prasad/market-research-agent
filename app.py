import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent.planner import generate_research_questions
from agent.search import search_questions
from agent.synthesize import synthesize_insights
from agent.evaluate import evaluate_insights
from agent.report import save_report

st.set_page_config(page_title="Market Research Agent", page_icon="🔍")

st.title("🔍 Market Research & Trend Analysis Agent")
st.write("Enter a topic, competitor, or market niche to get a cited, fact-checked research report.")

topic = st.text_input("Topic, competitor, or niche")

if st.button("Research") and topic:
    with st.spinner("Planning research questions..."):
        questions_text = generate_research_questions(topic)
    st.subheader("Research Questions")
    st.write(questions_text)

    with st.spinner("Searching the web..."):
        results = search_questions(questions_text)

    with st.spinner("Synthesizing insights..."):
        insights = synthesize_insights(topic, results)

    with st.spinner("Fact-checking and evaluating..."):
        evaluated = evaluate_insights(topic, insights, results)

    st.subheader("Evaluated Insights")
    st.write(evaluated)

    filepath = save_report(topic, evaluated, results)
    st.success(f"Report saved: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        st.download_button("Download Report", f.read(), file_name=filepath.split("/")[-1])
