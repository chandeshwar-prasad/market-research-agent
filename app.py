import streamlit as st
import re
from dotenv import load_dotenv

load_dotenv()

from agent.planner import generate_research_questions
from agent.search import search_questions
from agent.synthesize import synthesize_insights
from agent.evaluate import evaluate_insights
from agent.report import save_report

# Page Config
st.set_page_config(page_title="Market Research Agent", page_icon="🔍", layout="wide")

# CSS Styling Injection
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    /* Apply globally */
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Title with gradient */
    .title-gradient {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    /* Cards */
    .premium-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 10px 30px -10px rgba(0,0,0,0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .premium-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 0 15px 35px -5px rgba(99, 102, 241, 0.15);
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        border-radius: 50px !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
        transition: all 0.3s ease !important;
        width: 100%;
        margin-top: 1rem;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    }
    
    /* Subheaders */
    .subheader-custom {
        font-size: 1.5rem;
        font-weight: 600;
        color: #f3f4f6;
        border-bottom: 2px solid #4f46e5;
        padding-bottom: 0.3rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Badges */
    .source-badge {
        display: inline-block;
        background-color: rgba(99, 102, 241, 0.1);
        color: #a5b4fc;
        padding: 0.2rem 0.6rem;
        border-radius: 50px;
        font-size: 0.8rem;
        margin-top: 0.5rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }
    
    /* Confidence Classes */
    .conf-high {
        color: #10b981;
        font-weight: 700;
        font-size: 0.85rem;
        background: rgba(16, 185, 129, 0.1);
        padding: 0.2rem 0.6rem;
        border-radius: 50px;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .conf-medium {
        color: #f59e0b;
        font-weight: 700;
        font-size: 0.85rem;
        background: rgba(245, 158, 11, 0.1);
        padding: 0.2rem 0.6rem;
        border-radius: 50px;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }
    .conf-low {
        color: #ef4444;
        font-weight: 700;
        font-size: 0.85rem;
        background: rgba(239, 68, 68, 0.1);
        padding: 0.2rem 0.6rem;
        border-radius: 50px;
        border: 1px solid rgba(239, 68, 68, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Helper functions to render structured layouts
def render_questions(questions_text):
    lines = questions_text.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line and line[0].isdigit():
            parts = line.split(".", 1)
            q_num = parts[0].strip()
            q_text = parts[1].strip()
            st.markdown(f"""
            <div style="background: rgba(99, 102, 241, 0.04); border-left: 4px solid #6366f1; padding: 0.8rem 1.2rem; border-radius: 0 12px 12px 0; margin-bottom: 0.6rem; border-top: 1px solid rgba(255,255,255,0.01); border-right: 1px solid rgba(255,255,255,0.01); border-bottom: 1px solid rgba(255,255,255,0.01);">
                <span style="color: #818cf8; font-weight: 700; margin-right: 0.5rem;">Q{q_num}:</span>
                <span style="color: #e5e7eb; font-size: 1rem; font-weight: 400;">{q_text}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.write(line)

def render_evaluated_insights(insights_text):
    lines = insights_text.split("\n")
    rendered_any = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Match standard evaluation format: 1. [Medium] Content... (Source: URL)
        match = re.match(r"^\d+\.\s+\[(High|Medium|Low)\]\s+(.*?)(?:\s+\(Source:\s*(.*?)\))?$", line, re.IGNORECASE)
        if match:
            confidence = match.group(1)
            content = match.group(2)
            source = match.group(3) if match.group(3) else None
            
            conf_class = f"conf-{confidence.lower()}"
            
            source_html = ""
            if source:
                display_url = source.replace("https://", "").replace("http://", "").split("/")[0]
                source_html = f'<div class="source-badge">Source: <a href="{source}" target="_blank" style="color: #a5b4fc; text-decoration: none; font-weight: 500;">{display_url} ↗</a></div>'
            
            st.markdown(f"""
            <div class="premium-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                    <span class="{conf_class}">{confidence} Confidence</span>
                </div>
                <div style="font-size: 1.05rem; color: #e5e7eb; line-height: 1.6; margin-bottom: 0.25rem;">{content}</div>
                {source_html}
            </div>
            """, unsafe_allow_html=True)
            rendered_any = True
        else:
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("*")):
                st.markdown(f"""
                <div class="premium-card">
                    <div style="font-size: 1.05rem; color: #e5e7eb; line-height: 1.6;">{line}</div>
                </div>
                """, unsafe_allow_html=True)
                rendered_any = True
            else:
                st.markdown(f"<div style='margin-bottom: 0.5rem;'>{line}</div>", unsafe_allow_html=True)
                
    if not rendered_any:
        st.write(insights_text)

# Sidebar Info Panel
with st.sidebar:
    st.markdown('<h2 style="font-weight: 800; color: #818cf8; margin-bottom: 0.2rem;">🔍 Info Panel</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: #9ca3af; font-size: 0.9rem;">Sequential Market Intelligence Agent</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 1rem; margin-top: 1rem;">
        <h4 style="margin-top:0; color:#e5e7eb; font-size: 0.95rem; font-weight: 600;">🛠️ Tech Stack</h4>
        <ul style="color:#9ca3af; font-size:0.85rem; padding-left: 1.2rem; margin-bottom: 0;">
            <li><b>LLM Orchestrator:</b> Groq (Llama 3.3 70B)</li>
            <li><b>Search Utility:</b> Tavily Live Web Search</li>
            <li><b>Orchestration:</b> Python Pipeline (Sequential)</li>
            <li><b>Fact Verification:</b> Self-Evaluation Step</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 1rem; margin-top: 1rem;">
        <h4 style="margin-top:0; color:#e5e7eb; font-size: 0.95rem; font-weight: 600;">💡 Example Topics</h4>
        <span style="font-size: 0.8rem; background: rgba(99,102,241,0.15); color: #a5b4fc; padding: 0.2rem 0.5rem; border-radius: 4px; display: inline-block; margin: 2px;">Notion's AI features</span>
        <span style="font-size: 0.8rem; background: rgba(99,102,241,0.15); color: #a5b4fc; padding: 0.2rem 0.5rem; border-radius: 4px; display: inline-block; margin: 2px;">ClickUp AI features</span>
        <span style="font-size: 0.8rem; background: rgba(99,102,241,0.15); color: #a5b4fc; padding: 0.2rem 0.5rem; border-radius: 4px; display: inline-block; margin: 2px;">AI search engines market 2026</span>
    </div>
    """, unsafe_allow_html=True)

# Main Dashboard Layout
st.markdown('<h1 class="title-gradient">🔍 Market Research & Trend Analysis Agent</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #9ca3af; font-size: 1.15rem; margin-bottom: 2rem;">Plans research, scans the live web, extracts relevant data, synthesizes ranked insights, and verifies evidence autonomously.</p>', unsafe_allow_html=True)

# Input container
st.markdown('<div class="premium-card">', unsafe_allow_html=True)
topic = st.text_input("What topic, competitor, or market niche would you like to research?", placeholder="e.g. Perplexity AI's business model")
st.markdown('</div>', unsafe_allow_html=True)

if st.button("Generate Intelligence Report") and topic:
    # 1. Planning
    with st.spinner("🧠 Formulating research questions..."):
        questions_text = generate_research_questions(topic)
    
    st.markdown('<div class="subheader-custom">📋 Research Plan</div>', unsafe_allow_html=True)
    render_questions(questions_text)

    # 2. Searching
    with st.spinner("🌐 Searching the live web via Tavily..."):
        results = search_questions(questions_text)
    
    st.markdown('<div class="subheader-custom">🌐 Sources Crawled</div>', unsafe_allow_html=True)
    for item in results:
        with st.expander(f"Sources for: {item['question']}"):
            if not item['sources']:
                st.info("No sources retrieved for this sub-question.")
            for source in item['sources']:
                st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.01); border: 1px solid rgba(255, 255, 255, 0.04); padding: 0.8rem; border-radius: 8px; margin-bottom: 0.5rem;">
                    <div style="font-weight: 500; color: #e5e7eb; margin-bottom: 0.25rem; font-size: 0.95rem;">{source['title']}</div>
                    <a href="{source['url']}" target="_blank" style="color: #818cf8; font-size: 0.85rem; text-decoration: none; font-weight: 500;">🔗 {source['url'][:80]}...</a>
                </div>
                """, unsafe_allow_html=True)

    # 3. Synthesizing
    with st.spinner("✍️ Synthesizing findings into ranked insights..."):
        insights = synthesize_insights(topic, results)

    # 4. Evaluation
    with st.spinner("🛡️ Verifying evidence and fact-checking citations..."):
        evaluated = evaluate_insights(topic, insights, results)

    st.markdown('<div class="subheader-custom">🎯 Verified Insights & Evidence Dossier</div>', unsafe_allow_html=True)
    render_evaluated_insights(evaluated)

    # 5. Exporting
    filepath = save_report(topic, evaluated, results)
    
    st.markdown('<div class="subheader-custom">📥 Export Report</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="premium-card" style="text-align: center; border-color: rgba(16, 185, 129, 0.25); background: rgba(16, 185, 129, 0.02);">
        <h4 style="color: #10b981; margin-top: 0; margin-bottom: 0.5rem; font-weight: 700;">✨ Market Report Prepared Successfully</h4>
        <p style="color: #9ca3af; font-size: 0.9rem; margin-bottom: 1.5rem;">Dossier saved locally to <code style="color: #a7f3d0; font-size: 0.85rem;">{filepath}</code></p>
    </div>
    """, unsafe_allow_html=True)
    
    with open(filepath, "r", encoding="utf-8") as f:
        st.download_button(
            label="Download Complete Markdown Report",
            data=f.read(),
            file_name=filepath.split("/")[-1],
            mime="text/markdown"
        )
