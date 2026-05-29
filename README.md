# 🎯 Job Application Agent — Rajendra Dayma

An AI-powered job application assistant built with Streamlit and Groq (LLaMA 3.3 70B).

## Features
- **Job link analyzer** — paste any job URL, get platform-specific step-by-step apply guide
- **AI cover letter generator** — LLaMA 3.3 70B writes a tailored cover letter from your resume
- **Application tracker** — log and track every job you apply to
- Supports LinkedIn, Indeed, Naukri.com, Internshala, and any company site

---

## 🚀 Deploy on Streamlit Community Cloud (Free)

### Step 1 — Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/job-application-agent.git
git push -u origin main
```

### Step 2 — Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click **New app**
4. Select your repo → branch: `main` → file: `app.py`
5. Click **Advanced settings** → add secret:
   ```
   GROQ_API_KEY = "gsk_your-key-here"
   ```
6. Click **Deploy**

---

## 💻 Run Locally

```bash
pip install -r requirements.txt

export GROQ_API_KEY="gsk_your-key-here"   # Mac/Linux
set GROQ_API_KEY=gsk_your-key-here        # Windows

streamlit run app.py
```

Open http://localhost:8501

---

## Get a FREE Groq API Key
1. Go to https://console.groq.com
2. Sign up (free — no credit card needed)
3. Go to **API Keys** → **Create API Key**
4. Copy and use above

---

## Project Structure
```
job_agent/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies (streamlit + groq)
└── README.md           # This file
```
