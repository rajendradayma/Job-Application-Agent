# 🎯 Workday Job Application Agent — Rajendra Dayma

Automates Workday job applications. You log in manually — the agent fills and submits everything else.

---

## ⚡ Quick Start

### 1. Install
```bash
bash setup.sh
```

### 2. Add your resume
Place your resume PDF in this folder and rename it to:
```
resume.pdf
```

### 3. Run
```bash
streamlit run app.py
```

---

## How It Works

1. Paste a Workday job URL in the dashboard (e.g. `https://amazon.wd5.myworkdayjobs.com/...`)
2. Enter the company name and click **Launch Agent**
3. A browser window opens — **you log in** (or create an account)
4. Switch to the terminal and press **Enter**
5. The agent automatically:
   - Fills your name, email, phone, address
   - Fills experience and education fields
   - Uploads your resume PDF
   - Clicks through all steps (Next → Next → Submit)
   - Pauses if a CAPTCHA appears so you can solve it
   - Logs the application to your tracker

---

## Files

```
workday_agent/
├── app.py                  # Streamlit dashboard (UI)
├── agent.py                # Playwright automation agent
├── requirements.txt        # Dependencies
├── setup.sh                # One-command installer
├── resume.pdf              # ← Place YOUR resume here
└── applications_log.json   # Auto-created — tracks all applications
```

---

## Supported Workday Fields

| Category | Fields auto-filled |
|---|---|
| Personal | First/last name, email, phone, address, city, state, zip, country |
| Links | LinkedIn, GitHub |
| Experience | Current company, job title, years of experience |
| Education | University, degree, major, GPA, graduation year |
| Work auth | Authorized to work, require sponsorship, willing to relocate |
| Resume | PDF upload |

---

## Notes

- Works on **any company's Workday instance** (Amazon, Microsoft, Salesforce, etc.)
- You must **log in manually** — the agent does not store passwords
- If a CAPTCHA appears, the agent pauses and waits for you to solve it
- The agent handles multi-step forms automatically
- All applications are logged to `applications_log.json`
