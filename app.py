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
st.set_page_config(page_title="Market Research Agent", page_icon="🔍")

# CSS Styling Injection
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Apply globally */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Clean Title */
    .title-main {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--text-color, #1e293b);
        margin-bottom: 0.5rem;
    }
    
    /* Minimal Card */
    .minimal-card {
        background: rgba(128, 128, 128, 0.04);
        border: 1px solid rgba(128, 128, 128, 0.15);
        border-radius: 8px;
        padding: 1.2rem;
        margin: 0.8rem 0;
    }
    
    /* Custom buttons */
    .stButton>button {
        background-color: #2563eb !important; /* Slate Blue */
        color: white !important;
        border: 1px solid #2563eb !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
    }
    
    /* Subheaders */
    .subheader-custom {
        font-size: 1.4rem;
        font-weight: 600;
        color: var(--text-color, #334155);
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        padding-bottom: 0.3rem;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    /* Source Badge */
    .source-badge {
        display: inline-block;
        background-color: rgba(37, 99, 235, 0.08);
        color: #3b82f6;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        margin-top: 0.5rem;
        border: 1px solid rgba(37, 99, 235, 0.2);
    }
    
    /* Confidence Badges */
    .conf-high {
        color: #10b981;
        font-weight: 600;
        font-size: 0.8rem;
        background: rgba(16, 185, 129, 0.1);
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .conf-medium {
        color: #d97706;
        font-weight: 600;
        font-size: 0.8rem;
        background: rgba(217, 119, 6, 0.1);
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        border: 1px solid rgba(217, 119, 6, 0.2);
    }
    .conf-low {
        color: #dc2626;
        font-weight: 600;
        font-size: 0.8rem;
        background: rgba(220, 38, 38, 0.1);
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        border: 1px solid rgba(220, 38, 38, 0.2);
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
            <div style="background: rgba(128, 128, 128, 0.02); border-left: 3px solid #2563eb; padding: 0.6rem 1rem; border-radius: 0 6px 6px 0; margin-bottom: 0.5rem;">
                <span style="color: #2563eb; font-weight: 600; margin-right: 0.4rem;">Q{q_num}:</span>
                <span style="color: var(--text-color); font-size: 0.95rem;">{q_text}</span>
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
                source_html = f'<div class="source-badge">Source: <a href="{source}" target="_blank" style="color: #2563eb; text-decoration: none;">{display_url} ↗</a></div>'
            
            st.markdown(f"""
            <div class="minimal-card">
                <div style="margin-bottom: 0.5rem;">
                    <span class="{conf_class}">{confidence} Confidence</span>
                </div>
                <div style="font-size: 1rem; color: var(--text-color); line-height: 1.5;">{content}</div>
                {source_html}
            </div>
            """, unsafe_allow_html=True)
            rendered_any = True
        else:
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("*")):
                st.markdown(f"""
                <div class="minimal-card">
                    <div style="font-size: 1rem; color: var(--text-color); line-height: 1.5;">{line}</div>
                </div>
                """, unsafe_allow_html=True)
                rendered_any = True
            else:
                st.write(line)
                
    if not rendered_any:
        st.write(insights_text)

# Main Dashboard Layout
st.markdown('<h1 class="title-main">Market Research & Trend Analysis Agent</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #64748b; font-size: 1.05rem; margin-bottom: 1.5rem;">Enter a topic, competitor, or market niche to generate a cited, fact-checked research dossier.</p>', unsafe_allow_html=True)

topic = st.text_input("Research Topic / competitor / niche", placeholder="e.g. Notion's AI features")

if st.button("Run Research") and topic:
    # 1. Planning
    with st.spinner("Planning research questions..."):
        questions_text = generate_research_questions(topic)
    
    st.markdown('<div class="subheader-custom">Research Plan</div>', unsafe_allow_html=True)
    render_questions(questions_text)

    # 2. Searching
    with st.spinner("Searching the live web..."):
        results = search_questions(questions_text)
    
    st.markdown('<div class="subheader-custom">Sources Retrieved</div>', unsafe_allow_html=True)
    for item in results:
        with st.expander(f"Sources for: {item['question']}"):
            if not item['sources']:
                st.info("No sources retrieved for this sub-question.")
            for source in item['sources']:
                st.markdown(f"""
                <div style="background: rgba(128, 128, 128, 0.02); border: 1px solid rgba(128, 128, 128, 0.1); padding: 0.6rem; border-radius: 6px; margin-bottom: 0.4rem;">
                    <div style="font-weight: 500; font-size: 0.9rem; color: var(--text-color);">{source['title']}</div>
                    <a href="{source['url']}" target="_blank" style="color: #2563eb; font-size: 0.8rem; text-decoration: none;">{source['url'][:80]}...</a>
                </div>
                """, unsafe_allow_html=True)

    # 3. Synthesizing
    with st.spinner("Synthesizing insights..."):
        insights = synthesize_insights(topic, results)

    # 4. Evaluation
    with st.spinner("Fact-checking and evaluating..."):
        evaluated = evaluate_insights(topic, insights, results)

    st.markdown('<div class="subheader-custom">Evaluated Insights</div>', unsafe_allow_html=True)
    render_evaluated_insights(evaluated)

    # 5. Exporting
    filepath = save_report(topic, evaluated, results)
    
    st.markdown('<div class="subheader-custom">Export Intelligence Report</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="minimal-card" style="border-color: rgba(16, 185, 129, 0.3);">
        <h4 style="color: #10b981; margin-top: 0; margin-bottom: 0.5rem; font-weight: 600;">Report Generated Successfully</h4>
        <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 1rem;">The verified dossier has been saved locally as <code>{filepath}</code></p>
    </div>
    """, unsafe_allow_html=True)
    
    with open(filepath, "r", encoding="utf-8") as f:
        st.download_button(
            label="Download Markdown Report",
            data=f.read(),
            file_name=filepath.split("/")[-1],
            mime="text/markdown"
        )
