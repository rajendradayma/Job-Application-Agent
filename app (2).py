import streamlit as st
from groq import Groq
import json
import re
from datetime import datetime
from urllib.parse import urlparse

st.set_page_config(
    page_title="Job Application Agent — Rajendra Dayma",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Sora', sans-serif; }

.main { background: #0a0a0f; }
.block-container { padding: 2rem 2.5rem; max-width: 1100px; }

.hero-banner {
    background: linear-gradient(135deg, #0f1923 0%, #0a1628 50%, #0d1f1a 100%);
    border: 1px solid #1e3a5f;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(56,189,248,0.06) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-name { font-size: 1.6rem; font-weight: 600; color: #e2f0ff; margin: 0; }
.hero-role { font-size: 0.95rem; color: #64b5f6; margin: 4px 0 0; font-weight: 400; }
.hero-meta { font-size: 0.8rem; color: #4a7a9b; margin-top: 8px; font-family: 'JetBrains Mono', monospace; }

.section-card {
    background: #0f1923;
    border: 1px solid #1a2d42;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
}
.section-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: #4a7a9b;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 1rem;
}

.step-item {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    padding: 10px 0;
    border-bottom: 1px solid #1a2d42;
}
.step-num {
    width: 24px;
    height: 24px;
    background: #1e3a5f;
    color: #64b5f6;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 600;
    flex-shrink: 0;
    margin-top: 2px;
}
.step-text h4 { font-size: 0.85rem; font-weight: 500; color: #c8dff0; margin: 0 0 2px; }
.step-text p { font-size: 0.8rem; color: #5a8aaa; margin: 0; line-height: 1.5; }

.skill-tag {
    display: inline-block;
    background: #0d1f2d;
    border: 1px solid #1e3a5f;
    color: #64b5f6;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    margin: 3px;
}
.log-entry {
    background: #0a1420;
    border: 1px solid #1a2d42;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.log-url { font-size: 0.78rem; color: #4a7a9b; font-family: 'JetBrains Mono', monospace; }
.log-platform { font-size: 0.72rem; color: #2ecc71; background: #0d2010; border: 1px solid #1a4a20; padding: 2px 8px; border-radius: 10px; }

.cover-output {
    background: #080e16;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 1.5rem;
    font-size: 0.85rem;
    color: #c8dff0;
    line-height: 1.8;
    font-family: 'Sora', sans-serif;
    white-space: pre-wrap;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #080e16 !important;
    border: 1px solid #1e3a5f !important;
    color: #c8dff0 !important;
    border-radius: 8px !important;
    font-family: 'Sora', sans-serif !important;
}
.stButton > button {
    background: #1e3a5f !important;
    color: #64b5f6 !important;
    border: 1px solid #2a5280 !important;
    border-radius: 8px !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #2a5280 !important;
    color: #b3d9ff !important;
}
[data-testid="stSidebar"] {
    background: #080e16 !important;
    border-right: 1px solid #1a2d42 !important;
}
.stSelectbox > div > div {
    background: #080e16 !important;
    border: 1px solid #1e3a5f !important;
    color: #c8dff0 !important;
}
h1, h2, h3 { color: #e2f0ff !important; font-family: 'Sora', sans-serif !important; }
p, li { color: #8aabb8 !important; }
.stTabs [data-baseweb="tab"] { color: #4a7a9b !important; font-family: 'Sora', sans-serif !important; }
.stTabs [aria-selected="true"] { color: #64b5f6 !important; border-bottom-color: #64b5f6 !important; }
</style>
""", unsafe_allow_html=True)

RESUME = {
    "name": "Rajendra Dayma",
    "email": "rajendradayma88@gmail.com",
    "phone": "+917067409386",
    "location": "Bhopal, India",
    "linkedin": "LinkedIn",
    "github": "GitHub",
    "education": "B.Tech Computer Science & Engineering (Data Science), Oriental Institute of Science and Technology, 2020–2024, CGPA: 8.11",
    "current_role": "Data Science Intern at DataNeuron (Oct 2025 – Present)",
    "experience": [
        {
            "title": "Data Science Intern",
            "company": "DataNeuron",
            "duration": "Oct 2025 – Present",
            "highlights": [
                "Developed RAG pipelines for document-based Q&A using LLMs and vector databases",
                "Built AI agents and Multi-Agent Systems (MAS) to automate AI workflows",
                "Integrated Knowledge Graphs for contextual retrieval and semantic understanding",
                "Implemented reranking techniques to improve document retrieval accuracy",
                "Applied Knowledge Distillation and PEFT for efficient LLM fine-tuning",
                "Contributed to RBAC RAG system for secure document access"
            ]
        },
        {
            "title": "Junior AI/ML Engineer",
            "company": "Xapton Solutions",
            "duration": "Jun 2025 – Sep 2025",
            "highlights": [
                "Developed FastAPI microservices to integrate AI agents into Dell GCS Partner onboarding",
                "Built APIs for schema validation, payload testing, and automation workflows",
                "Implemented backend services for document sharing and connectivity validation"
            ]
        },
        {
            "title": "Data Science Intern",
            "company": "Code Clause",
            "duration": "Mar 2023 – Apr 2023",
            "highlights": ["Data collection, preprocessing, visualization, and statistical analysis"]
        },
        {
            "title": "AI Intern",
            "company": "IBM SkillsBuild",
            "duration": "Jan 2023 – Mar 2023",
            "highlights": ["Developed AI-driven Drowsiness Assistant System using facial recognition and ML"]
        }
    ],
    "skills": {
        "languages": ["Python", "C/C++", "Java", "SQL", "R", "Bash"],
        "frameworks": ["LangChain", "LangGraph", "FastAPI", "Flask", "PyTorch", "TensorFlow", "Scikit-learn", "Streamlit", "Hugging Face", "OpenAI API"],
        "tools": ["Docker", "Kubernetes", "Git", "MLflow", "AWS", "Azure", "MongoDB", "ChromaDB", "Neo4j", "pgvector"],
        "domains": ["RAG", "LLMs", "AI Agents", "MAS", "NLP", "MLOps", "Knowledge Graphs", "Data Science", "API Development"]
    },
    "projects": [
        {
            "name": "Role-Based Access Control RAG System",
            "tech": "Python, RAG, LLMs, Vector DB, LangChain, Streamlit, RBAC",
            "desc": "RAG-based document Q&A with RBAC — users access only authorized documents. Includes ingestion pipeline, embeddings, and secure multi-user Streamlit interface."
        },
        {
            "name": "AI Chatbot for Business Automation",
            "tech": "GPT-4, LangChain, FastAPI, MongoDB, Streamlit, Docker",
            "desc": "GPT-4 powered chatbot with RAG for accurate responses from internal knowledge bases, deployed via Docker with FAISS/ChromaDB vector search."
        }
    ],
    "certifications": [
        "IBM Data Science Specialization",
        "Oracle Cloud Infrastructure 2025 Generative AI Professional",
        "Supervised Machine Learning",
        "Getting Started with Data Analytics on AWS",
        "TCS iON Career Edge - Young Professional",
        "AI, Empathy & Ethics",
        "Database and SQL for Data Science with Python"
    ],
    "awards": ["Rank 6 in DataViz Hackathon — IIM Calcutta (Aug 2023)"]
}

PLATFORM_STEPS = {
    "LinkedIn": [
        ("Open the job link", "Navigate to the LinkedIn job URL in your browser."),
        ("Sign in or create account", f"Use {RESUME['email']}. New user → click 'Join now' → fill name, email, password → verify email."),
        ("Click Easy Apply or Apply", "Easy Apply uses your profile. 'Apply' redirects to company site — use your details below."),
        ("Upload resume", "Upload Rajendra_Dayma_FlowCV_Resume_2026-05-28.pdf when prompted."),
        ("Fill the form", "Current title: Data Science Intern. Years of ML/AI experience: 3+. Salary expectation: based on role."),
        ("Add cover note", "Mention RAG pipeline work at DataNeuron, AI agents, and your RBAC project. 2–3 sentences."),
        ("Submit", "Review and click Submit. Log the application in the tracker tab."),
    ],
    "Indeed": [
        ("Open job link", "Navigate to the Indeed job URL."),
        ("Sign in or register", f"Click Sign in → {RESUME['email']}. New user → Create account with your details."),
        ("Click Apply Now", "Some jobs show 'Easily Apply' (quick form); others redirect to the company site."),
        ("Upload resume", "Indeed can parse your PDF resume automatically."),
        ("Answer screening questions", "Years of Python: 3+. AI/ML experience: 3+ years. Open to remote: Yes."),
        ("Submit", "Review answers and submit. Log in tracker."),
    ],
    "Naukri.com": [
        ("Open job link", "Navigate to the Naukri job URL."),
        ("Sign in or register", f"Use {RESUME['email']}. New account → Name: Rajendra Dayma, Location: Bhopal, Experience: 1–2 years."),
        ("Complete your profile", "Add current role (Data Science Intern at DataNeuron), key skills, and education before applying."),
        ("Click Apply", "Click the Apply button on the job page."),
        ("Attach resume", "Upload your PDF resume or use the auto-parsed Naukri profile."),
        ("Submit", "Submit and log your application."),
    ],
    "Internshala": [
        ("Open job link", "Navigate to the Internshala URL."),
        ("Sign in or register", f"New account → Name: Rajendra Dayma, Email: {RESUME['email']}, College: Oriental Institute of Science and Technology, Grad: 2024."),
        ("Complete profile", "Add skills: Python, ML, AI, LangChain, FastAPI. Add internship experience."),
        ("Write cover letter", "Internshala requires a short note — use the AI cover letter generator in Tab 2."),
        ("Submit application", "Click Apply and log it in the tracker."),
    ],
    "Other / Company site": [
        ("Open the job link", "Navigate to the company careers URL."),
        ("Register if needed", f"Use {RESUME['email']} as login. Fill name, phone, and location from the details panel."),
        ("Upload resume", "Upload the PDF resume when prompted."),
        ("Fill experience", "Current: Data Science Intern at DataNeuron (Oct 2025–Present). Previous: Junior AI/ML Engineer at Xapton (Jun–Sep 2025)."),
        ("Fill education", "B.Tech CSE (Data Science), Oriental Institute of Science and Technology, 2020–2024, CGPA 8.11."),
        ("Submit", "Review all fields and submit. Log your application."),
    ]
}

def detect_platform(url):
    if not url:
        return "Other / Company site"
    url = url.lower()
    if "linkedin.com" in url: return "LinkedIn"
    if "indeed.com" in url: return "Indeed"
    if "naukri.com" in url: return "Naukri.com"
    if "internshala.com" in url: return "Internshala"
    return "Other / Company site"

def generate_cover_letter(job_url, job_title, company_name, job_desc, tone):
    client = Groq()
    resume_summary = f"""
Name: {RESUME['name']}
Email: {RESUME['email']}
Current Role: {RESUME['current_role']}
Education: {RESUME['education']}
Key Skills: RAG, LLMs, AI Agents, LangChain, FastAPI, Python, Docker, MLOps, Knowledge Graphs, MAS
Notable Projects: RBAC RAG System, AI Business Automation Chatbot
Recent Experience: Built RAG pipelines, Multi-Agent Systems, FastAPI microservices for AI at DataNeuron and Xapton Solutions
Certifications: IBM Data Science, Oracle Cloud Generative AI Professional, AWS Analytics
Awards: Rank 6, DataViz Hackathon at IIM Calcutta
"""
    prompt = f"""Write a professional cover letter for the following job application.

Resume summary:
{resume_summary}

Job details:
- Job Title: {job_title or 'Not specified'}
- Company: {company_name or 'the company'}
- Job URL: {job_url or 'Not provided'}
- Job Description / Notes: {job_desc or 'Not provided'}

Tone: {tone}

Instructions:
- Write a complete, ready-to-send cover letter (3–4 paragraphs)
- Start with a strong opening that mentions the specific role and company
- Highlight 2–3 most relevant experiences from the resume that match the job
- Mention specific technical skills that are relevant (RAG, LLMs, agents, FastAPI, etc.)
- Close with enthusiasm and a call to action
- Keep it under 300 words
- Do NOT use placeholder text like [Your Name] — use Rajendra Dayma's actual details
- End with: Warm regards, / Rajendra Dayma / rajendradayma88@gmail.com / +917067409386
"""
    with st.spinner("✦ Generating your cover letter with AI..."):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
    return response.choices[0].message.content

if "applications" not in st.session_state:
    st.session_state.applications = []
if "cover_letter" not in st.session_state:
    st.session_state.cover_letter = ""

with st.sidebar:
    st.markdown("""
    <div style='padding: 0.5rem 0 1.5rem;'>
        <div style='font-size:1.1rem; font-weight:600; color:#e2f0ff;'>🎯 Job Agent</div>
        <div style='font-size:0.75rem; color:#4a7a9b; margin-top:4px;'>Rajendra Dayma</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Quick copy — your details**")
    details = {
        "Name": RESUME["name"],
        "Email": RESUME["email"],
        "Phone": RESUME["phone"],
        "Location": RESUME["location"],
        "Current role": "Data Science Intern @ DataNeuron",
        "Education": "B.Tech CSE (DS), CGPA 8.11",
        "Experience": "~3 years AI/ML"
    }
    for label, val in details.items():
        st.code(val, language=None)

    st.markdown("---")
    st.markdown("**Top skills**")
    skills_html = "".join([f"<span class='skill-tag'>{s}</span>" for s in
        ["Python", "RAG", "LLMs", "LangChain", "FastAPI", "Docker", "AI Agents", "MLOps", "AWS", "PyTorch"]])
    st.markdown(f"<div style='line-height:2'>{skills_html}</div>", unsafe_allow_html=True)

st.markdown("""
<div class='hero-banner'>
    <div class='hero-name'>🎯 Job Application Agent</div>
    <div class='hero-role'>Data Science · AI/ML Engineer · LLM & RAG Specialist</div>
    <div class='hero-meta'>rajendradayma88@gmail.com &nbsp;·&nbsp; +917067409386 &nbsp;·&nbsp; Bhopal, India</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📋 Apply to a Job", "✍️ Cover Letter Generator", "📊 Application Tracker"])

with tab1:
    st.markdown("#### Paste a job link to get started")
    col1, col2 = st.columns([3, 1])
    with col1:
        job_url = st.text_input("", placeholder="https://www.linkedin.com/jobs/view/... or any job URL", label_visibility="collapsed")
    with col2:
        analyze = st.button("🔍 Analyze Job", use_container_width=True)

    if analyze and job_url:
        platform = detect_platform(job_url)
        st.success(f"✦ Detected platform: **{platform}**")
        st.session_state["current_url"] = job_url
        st.session_state["current_platform"] = platform

    if "current_platform" in st.session_state:
        platform = st.session_state["current_platform"]
        url = st.session_state.get("current_url", "")

        st.markdown(f"<div class='section-title'>Step-by-step guide — {platform}</div>", unsafe_allow_html=True)
        steps = PLATFORM_STEPS.get(platform, PLATFORM_STEPS["Other / Company site"])
        steps_html = ""
        for i, (title, desc) in enumerate(steps):
            steps_html += f"""
            <div class='step-item'>
                <div class='step-num'>{i+1}</div>
                <div class='step-text'><h4>{title}</h4><p>{desc}</p></div>
            </div>"""
        st.markdown(f"<div class='section-card'>{steps_html}</div>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("✅ Log this application", use_container_width=True):
                st.session_state.applications.append({
                    "url": url,
                    "platform": platform,
                    "date": datetime.now().strftime("%d %b %Y, %H:%M"),
                    "status": "Applied"
                })
                st.success("Logged! Check the Application Tracker tab.")
        with col_b:
            if st.button("✍️ Generate cover letter for this job →", use_container_width=True):
                st.info("Switch to the Cover Letter Generator tab and fill in the job details.")

with tab2:
    st.markdown("#### AI cover letter generator")
    st.markdown("<p style='font-size:0.85rem;'>Powered by Claude — generates a tailored letter using your resume</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        job_title_input = st.text_input("Job title", placeholder="e.g. Senior ML Engineer")
        company_input = st.text_input("Company name", placeholder="e.g. Google DeepMind")
    with col2:
        cl_url = st.text_input("Job URL (optional)", placeholder="https://...")
        tone = st.selectbox("Tone", ["Professional & confident", "Enthusiastic & energetic", "Concise & direct", "Research-focused"])

    job_desc_input = st.text_area("Job description or key requirements (paste here)", height=120,
        placeholder="Paste the job description or list key skills they're looking for...")

    if st.button("✦ Generate cover letter", use_container_width=True):
        if not job_title_input and not company_input and not job_desc_input:
            st.warning("Please fill in at least the job title or company name.")
        else:
            letter = generate_cover_letter(cl_url, job_title_input, company_input, job_desc_input, tone)
            st.session_state.cover_letter = letter

    if st.session_state.cover_letter:
        st.markdown("---")
        st.markdown("**Your cover letter — ready to send**")
        st.markdown(f"<div class='cover-output'>{st.session_state.cover_letter}</div>", unsafe_allow_html=True)
        st.download_button(
            "⬇️ Download as .txt",
            data=st.session_state.cover_letter,
            file_name=f"cover_letter_{company_input or 'job'}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        if st.button("🔄 Regenerate", use_container_width=True):
            st.session_state.cover_letter = ""
            st.rerun()

with tab3:
    st.markdown("#### Application tracker")
    total = len(st.session_state.applications)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total applied", total)
    col2.metric("This session", total)
    col3.metric("Platforms", len(set(a["platform"] for a in st.session_state.applications)) if total else 0)

    if not st.session_state.applications:
        st.info("No applications logged yet. Use the 'Apply to a Job' tab to get started.")
    else:
        for app in reversed(st.session_state.applications):
            log_html = f"""
            <div class='log-entry'>
                <div>
                    <div style='font-size:0.85rem; color:#c8dff0; font-weight:500;'>{app['platform']} &nbsp;·&nbsp; {app['date']}</div>
                    <div class='log-url'>{app['url'][:70]}{'...' if len(app['url']) > 70 else ''}</div>
                </div>
                <span class='log-platform'>{app['status']}</span>
            </div>"""
            st.markdown(log_html, unsafe_allow_html=True)

        if st.button("🗑️ Clear all logs"):
            st.session_state.applications = []
            st.rerun()
