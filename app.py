import streamlit as st
import re
from dotenv import load_dotenv

load_dotenv()

import agent.orchestrator
from agent.planner import generate_research_questions
from agent.search import search_questions
from agent.synthesize import synthesize_insights
from agent.evaluate import evaluate_insights
from agent.report import save_report
from agent.schemas import (
    ResearchQuestions,
    SearchResult,
    Source,
    SynthesisResult,
    EvaluatedInsight,
    EvaluationResult
)

# Page Config
st.set_page_config(page_title="Market Research Agent", page_icon="🔍")

# CSS Styling Injection
st.markdown("""
<style>
    /* Import modern typography */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Elegant Title with Gradient Clip */
    .title-main {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 50%, #db2777 100%);
        -webkit-background-clip: text;
        -webkit-background-color: transparent;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
    }
    
    .subtitle-main {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 2rem;
    }
    
    /* Premium Glassmorphic Card Layout */
    .minimal-card {
        background: rgba(128, 128, 128, 0.03);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(128, 128, 128, 0.12);
        border-radius: 12px;
        padding: 1.4rem;
        margin: 0.8rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.2s;
    }
    
    .minimal-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 20px -3px rgba(37, 99, 235, 0.06), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
        border-color: rgba(37, 99, 235, 0.25);
    }
    
    /* Questions Plan Stepper Style */
    .plan-question-box {
        background: rgba(37, 99, 235, 0.02);
        border-left: 4px solid #2563eb;
        padding: 0.8rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.6rem;
        transition: background-color 0.2s;
    }
    
    .plan-question-box:hover {
        background: rgba(37, 99, 235, 0.05);
    }
    
    /* Subheaders with border line */
    .subheader-custom {
        font-size: 1.35rem;
        font-weight: 700;
        color: var(--text-color, #1e293b);
        border-bottom: 1px solid rgba(128, 128, 128, 0.15);
        padding-bottom: 0.4rem;
        margin-top: 2.2rem;
        margin-bottom: 1rem;
        letter-spacing: -0.01em;
    }
    
    /* Source Badge Pill */
    .source-badge {
        display: inline-block;
        background-color: rgba(37, 99, 235, 0.06);
        color: #2563eb;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 0.6rem;
        border: 1px solid rgba(37, 99, 235, 0.15);
        transition: all 0.2s;
    }
    
    .source-badge:hover {
        background-color: rgba(37, 99, 235, 0.12);
        border-color: rgba(37, 99, 235, 0.3);
    }
    
    /* Buttons Custom CSS styling */
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 1.8rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        box-shadow: 0 6px 12px -1px rgba(37, 99, 235, 0.35) !important;
        transform: translateY(-1px) !important;
    }
    
    .stDownloadButton>button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 1.8rem !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    
    .stDownloadButton>button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        box-shadow: 0 6px 12px -1px rgba(16, 185, 129, 0.35) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Confidence Badge pills */
    .conf-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .conf-high {
        color: #10b981;
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .conf-medium {
        color: #d97706;
        background: rgba(217, 119, 6, 0.08);
        border: 1px solid rgba(217, 119, 6, 0.2);
    }
    .conf-low {
        color: #dc2626;
        background: rgba(220, 38, 38, 0.08);
        border: 1px solid rgba(220, 38, 38, 0.2);
    }
    
    /* Dropped Claim Card */
    .dropped-card {
        background: rgba(220, 38, 38, 0.01);
        border: 1px dashed rgba(220, 38, 38, 0.25);
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        box-shadow: inset 0 0 4px rgba(220, 38, 38, 0.01);
    }
</style>
""", unsafe_allow_html=True)

# Helper functions to render structured layouts
def render_questions(questions_input):
    if isinstance(questions_input, ResearchQuestions):
        questions = questions_input.questions
    else:
        questions = []
        for line in questions_input.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line and line[0].isdigit():
                try:
                    parts = line.split(".", 1)
                    questions.append(parts[1].strip())
                except IndexError:
                    pass
            else:
                questions.append(line)

    for i, q_text in enumerate(questions, 1):
        st.markdown(f"""
        <div class="plan-question-box">
            <span style="color: #2563eb; font-weight: 700; margin-right: 0.5rem; font-size: 0.95rem;">Q{i}:</span>
            <span style="color: var(--text-color); font-size: 0.95rem; font-weight: 500;">{q_text}</span>
        </div>
        """, unsafe_allow_html=True)

def render_evaluated_insights(evaluation_input):
    if isinstance(evaluation_input, EvaluationResult):
        insights = evaluation_input.kept_insights
    else:
        insights = []
        lines = evaluation_input.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            match = re.match(r"^\d+\.\s+\[(High|Medium|Low)\]\s+(.*?)(?:\s+\(Source:\s*(.*?)\))?$", line, re.IGNORECASE)
            if match:
                insights.append(EvaluatedInsight(
                    text=match.group(2),
                    cited_url=match.group(3),
                    verdict="Supported",
                    decision="KEEP",
                    confidence=match.group(1)
                ))
            else:
                if line and (line[0].isdigit() or line.startswith("-") or line.startswith("*")):
                    insights.append(EvaluatedInsight(
                        text=line,
                        cited_url=None,
                        verdict="Supported",
                        decision="KEEP",
                        confidence="Medium"
                    ))
                
    if not insights:
        if isinstance(evaluation_input, str):
            st.write(evaluation_input)
        else:
            st.write("No insights found.")
        return

    for ins in insights:
        confidence = ins.confidence
        content = ins.text
        source = ins.cited_url
        
        conf_class = f"conf-{confidence.lower()}"
        
        source_html = ""
        if source and source != "N/A":
            display_url = source.replace("https://", "").replace("http://", "").split("/")[0]
            source_html = f'<div class="source-badge">Source: <a href="{source}" target="_blank" style="color: #2563eb; text-decoration: none; font-weight: 500;">{display_url} ↗</a></div>'
        
        st.markdown(f"""
        <div class="minimal-card">
            <div style="margin-bottom: 0.6rem;">
                <span class="conf-badge {conf_class}">{confidence} Confidence</span>
            </div>
            <div style="font-size: 1rem; color: var(--text-color); line-height: 1.55; font-weight: 400;">{content}</div>
            {source_html}
        </div>
        """, unsafe_allow_html=True)

def render_evidence_gaps(evaluation_input):
    if not isinstance(evaluation_input, EvaluationResult):
        return
        
    gaps = evaluation_input.evidence_gaps
    if not gaps:
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.02); border: 1px solid rgba(16, 185, 129, 0.15); border-radius: 8px; padding: 1rem; margin: 1rem 0;">
            <span style="color: #10b981; font-weight: 600; font-size: 0.95rem;">✓ All synthesized claims were verified as fully supported by web evidence.</span>
        </div>
        """, unsafe_allow_html=True)
        return

    for gap in gaps:
        cleaned_gap = gap.replace("Claim lack of evidence or contradiction:", "").strip()
        st.markdown(f"""
        <div class="dropped-card">
            <div style="margin-bottom: 0.4rem;">
                <span style="color: #dc2626; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; background: rgba(220, 38, 38, 0.08); padding: 0.2rem 0.5rem; border-radius: 4px; border: 1px solid rgba(220, 38, 38, 0.15);">Dropped Claim</span>
            </div>
            <div style="font-size: 0.95rem; color: var(--text-color); line-height: 1.5; font-style: italic;">"{cleaned_gap}"</div>
        </div>
        """, unsafe_allow_html=True)

# Main Dashboard Layout
st.markdown('<div class="title-main">Market Research & Trend Analysis Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-main">Enter a topic, competitor, or market niche to generate a cited, fact-checked research dossier.</div>', unsafe_allow_html=True)

topic = st.text_input("Research Topic / competitor / niche", placeholder="e.g. Notion's AI features")

force_fresh = st.checkbox("Force fresh research (skip cache)", value=False)

if st.button("Run Research") and topic:
    with st.spinner("Running agentic research pipeline (planning, search, synthesis, and evaluation)..."):
        filepath = agent.orchestrator.run(topic, force_fresh=force_fresh)
    
    # Retrieve cached execution data from cache on disk
    from agent.cache import get_cached
    cached_data = get_cached(topic, force_fresh=False)
    
    # If cached data contains the full structured details, render them in premium format!
    if cached_data and isinstance(cached_data, dict) and "evaluation" in cached_data:
        try:
            questions_obj = ResearchQuestions(**cached_data["questions"]) if cached_data.get("questions") else None
            results_list = [SearchResult(**r) for r in cached_data.get("results", [])]
            evaluation_obj = EvaluationResult(**cached_data["evaluation"])
            
            if questions_obj:
                st.markdown('<div class="subheader-custom">Research Plan</div>', unsafe_allow_html=True)
                render_questions(questions_obj)
                
            if results_list:
                st.markdown('<div class="subheader-custom">Sources Retrieved</div>', unsafe_allow_html=True)
                for item in results_list:
                    question = item.question
                    sources = item.sources
                    with st.expander(f"Sources for: {question}"):
                        if not sources:
                            st.info("No sources retrieved for this sub-question.")
                        for source in sources:
                            title = source.title
                            url = source.url
                            st.markdown(f"""
                            <div style="background: rgba(128, 128, 128, 0.02); border: 1px solid rgba(128, 128, 128, 0.1); padding: 0.6rem; border-radius: 6px; margin-bottom: 0.4rem;">
                                <div style="font-weight: 500; font-size: 0.9rem; color: var(--text-color);">{title}</div>
                                <a href="{url}" target="_blank" style="color: #2563eb; font-size: 0.8rem; text-decoration: none;">{url[:80]}...</a>
                            </div>
                            """, unsafe_allow_html=True)
            
            st.markdown('<div class="subheader-custom">Evaluated Insights</div>', unsafe_allow_html=True)
            render_evaluated_insights(evaluation_obj)
            
            st.markdown('<div class="subheader-custom">Fact-Checking Audit Trail</div>', unsafe_allow_html=True)
            render_evidence_gaps(evaluation_obj)
            
        except Exception as e:
            # Fallback to direct markdown rendering if parsing fails
            st.error(f"Error rendering premium UI: {e}")
            st.markdown('<div class="subheader-custom">Research Dossier</div>', unsafe_allow_html=True)
            with open(filepath, "r", encoding="utf-8") as f:
                st.markdown(f.read())
    else:
        # Fallback to direct markdown rendering if cached data is not fully structured
        st.markdown('<div class="subheader-custom">Research Dossier</div>', unsafe_allow_html=True)
        with open(filepath, "r", encoding="utf-8") as f:
            st.markdown(f.read())
            
    with open(filepath, "r", encoding="utf-8") as f:
        report_md = f.read()
            
    st.markdown('<div class="subheader-custom">Export Intelligence Report</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="minimal-card" style="border-color: rgba(16, 185, 129, 0.3);">
        <h4 style="color: #10b981; margin-top: 0; margin-bottom: 0.5rem; font-weight: 600;">Report Generated / Loaded Successfully</h4>
        <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 1rem;">The verified dossier has been saved locally as <code>{filepath}</code></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.download_button(
        label="Download Markdown Report",
        data=report_md,
        file_name=filepath.split("/")[-1],
        mime="text/markdown"
    )
