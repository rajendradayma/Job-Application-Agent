"""
Workday Agent — Streamlit Dashboard
Run: streamlit run app.py
Then use the UI to launch the agent in a local browser window.
"""

import streamlit as st
import subprocess
import json
import sys
import os
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Workday Agent — Rajendra Dayma",
    page_icon="🎯",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif; }
.hero { background: linear-gradient(135deg, #0f1923, #0a1628);
    border: 1px solid #1e3a5f; border-radius: 14px;
    padding: 1.5rem 2rem; margin-bottom: 1.5rem; }
.hero h1 { font-size: 1.4rem; color: #e2f0ff; margin: 0; }
.hero p { font-size: 0.85rem; color: #4a7a9b; margin: 4px 0 0; }
.step-card { background: #0f1923; border: 1px solid #1a2d42;
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.8rem; }
.step-num { background: #1e3a5f; color: #64b5f6; border-radius: 50%;
    width: 24px; height: 24px; display: inline-flex; align-items: center;
    justify-content: center; font-size: 0.7rem; font-weight: 600; margin-right: 8px; }
.log-row { background: #0a1420; border: 1px solid #1a2d42;
    border-radius: 8px; padding: 10px 14px; margin-bottom: 6px; }
.badge-ok { background: #0d2010; color: #2ecc71; border: 1px solid #1a4a20;
    padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; }
.badge-partial { background: #1a1200; color: #f39c12; border: 1px solid #3a2800;
    padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; }
.stButton > button { background: #1e3a5f !important; color: #64b5f6 !important;
    border: 1px solid #2a5280 !important; border-radius: 8px !important;
    font-family: 'Sora', sans-serif !important; font-weight: 500 !important; }
.stButton > button:hover { background: #2a5280 !important; }
.stTextInput > div > div > input {
    background: #080e16 !important; border: 1px solid #1e3a5f !important;
    color: #c8dff0 !important; border-radius: 8px !important; }
[data-testid="stSidebar"] { background: #080e16 !important; border-right: 1px solid #1a2d42 !important; }
h1,h2,h3 { color: #e2f0ff !important; font-family: 'Sora', sans-serif !important; }
p, li { color: #8aabb8 !important; }
.stTabs [data-baseweb="tab"] { color: #4a7a9b !important; }
.stTabs [aria-selected="true"] { color: #64b5f6 !important; border-bottom-color: #64b5f6 !important; }
</style>
""", unsafe_allow_html=True)

LOG_FILE = Path("applications_log.json")
PROFILE_FILE = Path("profile.json")

DEFAULT_PROFILE = {
    "first_name": "Rajendra",
    "last_name": "Dayma",
    "email": "rajendradayma88@gmail.com",
    "phone": "7067409386",
    "city": "Bhopal",
    "state": "Madhya Pradesh",
    "country": "India",
    "zip": "462001",
    "linkedin": "https://linkedin.com/in/rajendradayma",
    "github": "https://github.com/rajendradayma",
    "current_company": "DataNeuron",
    "current_title": "Data Science Intern",
    "years_experience": "2",
    "education_school": "Oriental Institute of Science and Technology",
    "education_degree": "Bachelor of Technology",
    "education_major": "Computer Science and Engineering",
    "education_gpa": "8.11",
    "education_grad_year": "2024",
}

def load_log():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text())
    return []

def load_profile():
    if PROFILE_FILE.exists():
        return json.loads(PROFILE_FILE.read_text())
    return DEFAULT_PROFILE

def save_profile(p):
    PROFILE_FILE.write_text(json.dumps(p, indent=2))

# ── Sidebar ──────────────────────────────────
with st.sidebar:
    st.markdown("<div style='font-size:1.1rem;font-weight:600;color:#e2f0ff;padding:0.5rem 0 1rem;'>🎯 Workday Agent</div>", unsafe_allow_html=True)
    st.markdown("**Rajendra Dayma**")
    st.markdown("<p style='font-size:0.78rem;color:#4a7a9b;'>rajendradayma88@gmail.com</p>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**How it works**")
    for i, step in enumerate(["Paste Workday job URL", "Click Launch Agent", "Browser opens — log in manually", "Press Enter → agent fills & submits"], 1):
        st.markdown(f"<div style='font-size:0.8rem;color:#8aabb8;padding:3px 0;'><span style='color:#64b5f6;font-weight:600;'>{i}.</span> {step}</div>", unsafe_allow_html=True)
    st.markdown("---")
    apps = load_log()
    st.metric("Total applied", len(apps))
    submitted = sum(1 for a in apps if "Submitted" in a.get("status",""))
    st.metric("Submitted", submitted)

# ── Main ─────────────────────────────────────
st.markdown("""
<div class='hero'>
    <h1>🎯 Workday Job Application Agent</h1>
    <p>Paste a Workday URL → agent opens browser → you log in → agent fills & submits everything</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🚀 Launch Agent", "👤 My Profile", "📊 Application Log"])

# ── Tab 1: Launch ────────────────────────────
with tab1:
    st.markdown("#### Start a new application")

    col1, col2 = st.columns([3, 1])
    with col1:
        job_url = st.text_input("Workday job URL", placeholder="https://company.wd5.myworkdayjobs.com/en-US/careers/job/...")
    with col2:
        company = st.text_input("Company name", placeholder="e.g. Microsoft")

    github_resume_url = st.text_input(
        "GitHub resume URL",
        value="https://github.com/rajendradayma/Job-Application-Agent/blob/main/Rajendra_Dayma_FlowCV_Resume_2026-05-28.pdf",
        help="Your resume PDF link from GitHub (blob URL — agent converts it to raw automatically)"
    )

    st.markdown("---")
    st.markdown("#### What the agent will do automatically")

    steps = [
        ("Open the job URL", "Navigates to the Workday job page and clicks Apply"),
        ("Wait for your login", "Pauses — you log in or create account in the browser"),
        ("Fill personal details", "Name, email, phone, address — all from your profile"),
        ("Fill experience & education", "Current role, company, degree, GPA, grad year"),
        ("Upload your resume", "Attaches your PDF resume to the form"),
        ("Handle CAPTCHA", "If detected, pauses and asks you to solve it"),
        ("Click through steps", "Navigates Next → Next → Submit across all form pages"),
        ("Submit & log", "Submits the application and logs it to your tracker"),
    ]
    for title, desc in steps:
        st.markdown(f"""
        <div class='step-card'>
            <span class='step-num'>✓</span>
            <strong style='color:#c8dff0; font-size:0.88rem;'>{title}</strong>
            <span style='color:#4a7a9b; font-size:0.82rem;'> — {desc}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Step 1: Launch ──
    if "agent_launched" not in st.session_state:
        st.session_state.agent_launched = False
    if "agent_proc" not in st.session_state:
        st.session_state.agent_proc = None

    col_a, col_b = st.columns(2)
    with col_a:
        launch = st.button("🚀 Step 1 — Launch Agent", use_container_width=True)
    with col_b:
        st.info("💡 Agent opens a headless browser. After launching, log in on your phone/PC and paste the URL below.")

    if launch:
        if not job_url or not job_url.startswith("http"):
            st.error("Please enter a valid Workday job URL.")
        elif not company:
            st.error("Please enter the company name.")
        else:
            env = os.environ.copy()
            env["GITHUB_RESUME_URL"] = github_resume_url
            env.pop("RESUME_PATH", None)
            proc = subprocess.Popen(
                [sys.executable, "agent.py", job_url, company],
                env=env, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True
            )
            st.session_state.agent_proc = proc
            st.session_state.agent_launched = True
            st.session_state.agent_company = company
            st.success(f"✅ Agent launched for **{company}**!")

    # ── Step 2: Paste post-login URL ──
    if st.session_state.agent_launched:
        st.markdown("---")
        st.markdown("""
        <div style='background:#0d1520;border:1px solid #1e3a5f;border-radius:10px;padding:1.2rem;margin-bottom:1rem;'>
            <p style='color:#64b5f6;font-size:0.9rem;font-weight:500;margin:0 0 8px;'>📋 Step 2 — Log in and share the URL</p>
            <p style='color:#4a7a9b;font-size:0.82rem;margin:0;line-height:1.7;'>
            1. Open the job URL in <strong style='color:#c8dff0;'>your phone or browser</strong><br>
            2. Click <strong style='color:#c8dff0;'>Apply</strong> on the job page<br>
            3. <strong style='color:#c8dff0;'>Log in</strong> to your Workday account<br>
            4. Once you reach the <strong style='color:#c8dff0;'>application form</strong>, copy the URL<br>
            5. Paste it below and click <strong style='color:#c8dff0;'>Send to Agent</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        post_login_url = st.text_input(
            "Paste your post-login application form URL here",
            placeholder="https://wd3.myworkdaysite.com/recruiting/company/job/..."
        )

        if st.button("✅ Step 2 — Send URL to Agent & Start Filling", use_container_width=True):
            if not post_login_url or not post_login_url.startswith("http"):
                st.error("Please paste a valid URL from your browser after logging in.")
            else:
                proc = st.session_state.agent_proc
                if proc and proc.poll() is None:
                    try:
                        proc.stdin.write(post_login_url + "\n")
                        proc.stdin.flush()
                        st.success("✅ URL sent! Groq is now filling the form automatically.")
                        st.info("Check the application log tab to track progress.")
                        st.session_state.agent_launched = False
                    except Exception as e:
                        st.error(f"Could not send URL to agent: {e}")
                else:
                    st.warning("Agent process is not running. Please launch it again.")

# ── Tab 2: Profile ───────────────────────────
with tab2:
    st.markdown("#### Your details — used to auto-fill every Workday form")
    profile = load_profile()

    col1, col2 = st.columns(2)
    with col1:
        profile["first_name"] = st.text_input("First name", profile["first_name"])
        profile["email"] = st.text_input("Email", profile["email"])
        profile["city"] = st.text_input("City", profile["city"])
        profile["country"] = st.text_input("Country", profile["country"])
        profile["current_company"] = st.text_input("Current company", profile["current_company"])
        profile["years_experience"] = st.text_input("Years of experience", profile["years_experience"])
        profile["education_school"] = st.text_input("University", profile["education_school"])
        profile["education_degree"] = st.text_input("Degree", profile["education_degree"])
    with col2:
        profile["last_name"] = st.text_input("Last name", profile["last_name"])
        profile["phone"] = st.text_input("Phone", profile["phone"])
        profile["state"] = st.text_input("State", profile["state"])
        profile["zip"] = st.text_input("ZIP / Postal code", profile["zip"])
        profile["current_title"] = st.text_input("Current job title", profile["current_title"])
        profile["linkedin"] = st.text_input("LinkedIn URL", profile["linkedin"])
        profile["education_major"] = st.text_input("Major / Field of study", profile["education_major"])
        profile["education_gpa"] = st.text_input("GPA", profile["education_gpa"])

    if st.button("💾 Save profile", use_container_width=True):
        save_profile(profile)
        st.success("Profile saved! Agent will use these details.")

# ── Tab 3: Log ───────────────────────────────
with tab3:
    st.markdown("#### Application tracker")
    apps = load_log()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total", len(apps))
    c2.metric("Submitted", sum(1 for a in apps if "Submitted" in a.get("status","")))
    c3.metric("Incomplete", sum(1 for a in apps if "Submitted" not in a.get("status","")))

    if not apps:
        st.info("No applications yet. Launch the agent from Tab 1 to get started.")
    else:
        for app in reversed(apps):
            badge = "badge-ok" if "Submitted" in app.get("status","") else "badge-partial"
            date = app.get("timestamp","")[:16].replace("T", " ")
            st.markdown(f"""
            <div class='log-row'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <div>
                        <span style='font-size:0.88rem;color:#c8dff0;font-weight:500;'>{app.get('company','Unknown')}</span>
                        <span style='color:#4a7a9b;font-size:0.78rem;'> · {date}</span>
                    </div>
                    <span class='{badge}'>{app.get('status','Unknown')}</span>
                </div>
                <div style='font-size:0.75rem;color:#2a4a5f;font-family:JetBrains Mono,monospace;margin-top:4px;
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:90%;'>
                    {app.get('url','')}
                </div>
                {f"<div style='font-size:0.78rem;color:#4a7a9b;margin-top:4px;'>{app.get('notes','')}</div>" if app.get('notes') else ''}
            </div>""", unsafe_allow_html=True)

        if st.button("🗑️ Clear log"):
            LOG_FILE.write_text("[]")
            st.rerun()
