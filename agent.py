"""
Workday Job Application Agent — Rajendra Dayma
Powered by Groq LLaMA 3.3 70B for intelligent field filling
----------------------------------------------
How it works:
1. You paste a Workday job URL
2. Browser opens — you log in manually
3. Press Enter — Groq LLM reads each form field and decides the best answer
4. Agent fills, navigates, and submits
5. CAPTCHA? It pauses for you to solve
"""

import asyncio
import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path
from groq import Groq
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import urllib.request
import tempfile

# ─────────────────────────────────────────────
#  GITHUB RESUME DOWNLOADER
# ─────────────────────────────────────────────
GITHUB_RESUME_URL = "https://github.com/rajendradayma/Job-Application-Agent/blob/main/Rajendra_Dayma_FlowCV_Resume_2026-05-28.pdf"

def get_raw_github_url(github_url: str) -> str:
    """Convert GitHub blob URL to raw download URL."""
    raw = github_url.replace("github.com", "raw.githubusercontent.com")
    raw = raw.replace("/blob/", "/")
    return raw

def download_resume_from_github(github_url: str = GITHUB_RESUME_URL) -> str:
    """Download resume PDF from GitHub and return local temp path."""
    raw_url = get_raw_github_url(github_url)
    local_path = Path(__file__).parent / "resume_downloaded.pdf"
    print(f"  📥 Downloading resume from GitHub...")
    print(f"     {raw_url}")
    try:
        urllib.request.urlretrieve(raw_url, local_path)
        print(f"  ✓ Resume downloaded: {local_path.name} ({local_path.stat().st_size // 1024} KB)")
        return str(local_path)
    except Exception as e:
        print(f"  ⚠ Download failed: {e}")
        return ""


# ─────────────────────────────────────────────
#  GROQ CLIENT
# ─────────────────────────────────────────────
GROQ_API_KEY = "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"
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ─────────────────────────────────────────────
#  RESUME CONTEXT — fed to Groq for every field
# ─────────────────────────────────────────────
RESUME_CONTEXT = """
You are a job application assistant filling out a Workday form on behalf of Rajendra Dayma.
Here is his complete resume information:

PERSONAL:
- Full name: Rajendra Dayma
- First name: Rajendra
- Last name: Dayma
- Email: rajendradayma88@gmail.com
- Phone: 7067409386 (country: India, +91)
- Address: Bhopal, Madhya Pradesh, India
- City: Bhopal
- State: Madhya Pradesh
- Country: India
- ZIP/Postal code: 462001
- LinkedIn: https://linkedin.com/in/rajendradayma
- GitHub: https://github.com/rajendradayma
- Website: https://github.com/rajendradayma

CURRENT EXPERIENCE:
- Current company: DataNeuron
- Current job title: Data Science Intern
- Start date: October 2025
- Still working: Yes
- Key work: RAG pipelines, LLMs, AI agents, Multi-Agent Systems, Knowledge Graphs, PEFT, RBAC RAG system

PREVIOUS EXPERIENCE:
- Company: Xapton Solutions, Title: Junior AI/ML Engineer, Jun 2025 – Sep 2025
  Work: FastAPI microservices, AI agent integration, Dell GCS Partner onboarding, schema validation
- Company: Code Clause, Title: Data Science Intern, Mar 2023 – Apr 2023
  Work: Data collection, preprocessing, visualization, statistical analysis
- Company: IBM SkillsBuild, Title: AI Intern, Jan 2023 – Mar 2023
  Work: AI Drowsiness Assistant System using facial recognition and ML

TOTAL EXPERIENCE: 2 years in AI/ML/Data Science

EDUCATION:
- Degree: Bachelor of Technology (B.Tech)
- Field of study / Major: Computer Science and Engineering (specialization in Data Science)
- University: Oriental Institute of Science and Technology
- Location: Bhopal, India
- GPA/CGPA: 8.11 out of 10
- Graduation year: 2024
- Start year: 2020

SKILLS:
- Languages: Python, C/C++, Java, SQL, R, Bash
- Frameworks: LangChain, LangGraph, FastAPI, Flask, PyTorch, TensorFlow, Scikit-learn, Streamlit, Hugging Face, OpenAI API
- Tools: Docker, Kubernetes, Git, MLflow, AWS, Azure, MongoDB, ChromaDB, Neo4j, pgvector
- Domains: RAG, LLMs, AI Agents, MAS, NLP, MLOps, Knowledge Graphs, Data Science, API Development

PROJECTS:
1. Role-Based Access Control RAG System (Feb 2026–Present)
   Tech: Python, RAG, LLMs, Vector DB, LangChain, Streamlit, RBAC
   - Document Q&A with RBAC, ingestion pipeline, embeddings, secure multi-user interface

2. AI Chatbot for Business Automation
   Tech: GPT-4, LangChain, FastAPI, MongoDB, Streamlit, Docker
   - GPT-4 chatbot with RAG, FAISS/ChromaDB vector search, Docker deployment

CERTIFICATIONS:
- IBM Data Science Specialization
- Oracle Cloud Infrastructure 2025 Generative AI Professional
- Supervised Machine Learning
- Getting Started with Data Analytics on AWS
- TCS iON Career Edge - Young Professional
- AI, Empathy & Ethics
- Database and SQL for Data Science with Python

AWARDS:
- Rank 6 in DataViz Hackathon — IIM Calcutta (Aug 2023)

WORK AUTHORIZATION:
- Authorized to work in India: Yes
- Requires visa sponsorship: No
- Willing to relocate: Yes
- Open to remote work: Yes
"""

RESUME_PATH = str(Path(__file__).parent / "resume.pdf")
GITHUB_RESUME = "https://github.com/rajendradayma/Job-Application-Agent/blob/main/Rajendra_Dayma_FlowCV_Resume_2026-05-28.pdf"
LOG_FILE = Path(__file__).parent / "applications_log.json"


# ─────────────────────────────────────────────
#  GROQ: ASK LLM TO FILL A FIELD
# ─────────────────────────────────────────────
def ask_groq_for_field(field_label: str, field_type: str, options: list = None, context: str = "") -> str:
    """Ask Groq LLaMA to determine the best answer for a form field."""
    options_text = ""
    if options:
        options_text = f"\nAvailable options to choose from: {options}\nReturn ONLY one of these options exactly as written."

    prompt = f"""
{RESUME_CONTEXT}

TASK:
A Workday job application form has a field. Determine the correct value to fill in based on the resume above.

Field label: "{field_label}"
Field type: {field_type}
Additional context on the page: "{context}"{options_text}

Rules:
- Return ONLY the value to fill in — no explanation, no extra text, no quotes
- If it's a Yes/No question, return exactly "Yes" or "No"
- If it's a dropdown and options are given, return exactly one of the options
- If you cannot determine the answer from the resume, return: SKIP
- For date fields return format: MM/YYYY or YYYY as appropriate
- Keep answers concise and professional
- For "how did you hear about us" type questions, answer: "Job Board"
- For salary/compensation questions, return: SKIP (leave blank)

Answer:"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=100,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content.strip()
        # Clean up common LLM artifacts
        answer = answer.strip('"\'').strip()
        return answer
    except Exception as e:
        print(f"    ⚠ Groq error for field '{field_label}': {e}")
        return "SKIP"


def ask_groq_for_textarea(field_label: str, context: str = "") -> str:
    """Ask Groq to write a longer answer for textarea fields."""
    prompt = f"""
{RESUME_CONTEXT}

TASK:
A Workday job application has a text area field that requires a longer answer.

Field label: "{field_label}"
Page context: "{context}"

Write a professional, concise answer (2-4 sentences max) based on Rajendra's resume.
Return ONLY the answer text, no explanation.

Answer:"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=300,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"    ⚠ Groq error for textarea '{field_label}': {e}")
        return ""


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def load_log():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text())
    return []

def save_log(entries):
    LOG_FILE.write_text(json.dumps(entries, indent=2))

def log_application(url, company, status, notes=""):
    entries = load_log()
    entries.append({
        "url": url, "company": company,
        "status": status, "notes": notes,
        "timestamp": datetime.now().isoformat()
    })
    save_log(entries)
    print(f"\n✅ Logged: {company} — {status}")

def print_log():
    entries = load_log()
    if not entries:
        print("No applications logged yet.")
        return
    print(f"\n{'─'*65}")
    print(f"{'COMPANY':<25} {'STATUS':<20} {'DATE'}")
    print(f"{'─'*65}")
    for e in entries:
        print(f"{e['company']:<25} {e['status']:<20} {e['timestamp'][:10]}")
    print(f"{'─'*65}\n")

async def wait_for_user(msg):
    print(f"\n⏸  {msg}")
    print("   Press ENTER to continue...")
    await asyncio.get_event_loop().run_in_executor(None, input)

async def detect_captcha(page):
    selectors = [
        "iframe[src*='recaptcha']", "iframe[src*='hcaptcha']",
        ".g-recaptcha", "#captcha", "[data-sitekey]",
        "iframe[title*='challenge']", "iframe[title*='CAPTCHA']"
    ]
    for sel in selectors:
        try:
            if await page.locator(sel).count() > 0:
                return True
        except Exception:
            pass
    return False


# ─────────────────────────────────────────────
#  SMART FIELD EXTRACTION FROM PAGE
# ─────────────────────────────────────────────
async def get_all_form_fields(page):
    """Extract all visible form fields with their labels from the page."""
    fields = await page.evaluate("""
    () => {
        const results = [];
        const inputs = document.querySelectorAll(
            'input:not([type="hidden"]):not([type="file"]):not([type="submit"]):not([type="checkbox"]):not([type="radio"]), textarea, select'
        );

        inputs.forEach(input => {
            if (!input.offsetParent) return; // skip hidden

            let label = '';
            // Try aria-label
            if (input.getAttribute('aria-label')) {
                label = input.getAttribute('aria-label');
            }
            // Try associated label tag
            else if (input.id) {
                const lbl = document.querySelector(`label[for="${input.id}"]`);
                if (lbl) label = lbl.innerText.trim();
            }
            // Try closest label parent
            else {
                const parent = input.closest('label');
                if (parent) label = parent.innerText.trim();
            }
            // Try aria-labelledby
            if (!label && input.getAttribute('aria-labelledby')) {
                const lblEl = document.getElementById(input.getAttribute('aria-labelledby'));
                if (lblEl) label = lblEl.innerText.trim();
            }
            // Try placeholder as fallback
            if (!label && input.placeholder) {
                label = input.placeholder;
            }

            // Get select options
            let options = [];
            if (input.tagName === 'SELECT') {
                options = Array.from(input.options).map(o => o.text).filter(t => t && t !== '-- Select --' && t !== 'Select...');
            }

            if (label) {
                results.push({
                    label: label.replace(/\\*/g, '').trim(),
                    type: input.tagName === 'SELECT' ? 'select' : (input.tagName === 'TEXTAREA' ? 'textarea' : input.type || 'text'),
                    id: input.id || '',
                    name: input.name || '',
                    placeholder: input.placeholder || '',
                    options: options,
                    value: input.value || ''
                });
            }
        });

        // Also get checkboxes and radio buttons
        const checks = document.querySelectorAll('input[type="checkbox"], input[type="radio"]');
        checks.forEach(input => {
            if (!input.offsetParent) return;
            let label = '';
            if (input.id) {
                const lbl = document.querySelector(`label[for="${input.id}"]`);
                if (lbl) label = lbl.innerText.trim();
            }
            if (label) {
                results.push({
                    label: label.replace(/\\*/g, '').trim(),
                    type: input.type,
                    id: input.id || '',
                    name: input.name || '',
                    options: [],
                    value: input.value || ''
                });
            }
        });

        return results;
    }
    """)
    return fields


# ─────────────────────────────────────────────
#  GROQ-POWERED FORM FILLER
# ─────────────────────────────────────────────
async def fill_form_with_groq(page):
    """Use Groq LLM to intelligently fill every field on the current page."""
    print("\n🤖 Groq is reading the form fields...")

    # Get page context (job title / company from page title or headings)
    page_context = ""
    try:
        heading = await page.locator("h1, h2, .job-title, [data-automation-id='jobPostingHeader']").first.inner_text()
        page_context = heading[:200]
    except Exception:
        pass

    fields = await get_all_form_fields(page)
    print(f"   Found {len(fields)} fields on this page")

    filled = 0
    skipped = 0

    for field in fields:
        label = field["label"]
        ftype = field["type"]
        options = field["options"]
        field_id = field["id"]
        field_name = field["name"]

        if not label or len(label) < 2:
            continue

        # Skip already-filled fields
        if field["value"] and ftype not in ("select",):
            print(f"  ↷ Already filled: {label[:40]}")
            continue

        print(f"  🧠 Groq filling: [{ftype}] {label[:50]}...")

        # Ask Groq
        if ftype == "textarea":
            answer = ask_groq_for_textarea(label, page_context)
        else:
            answer = ask_groq_for_field(label, ftype, options if options else None, page_context)

        if not answer or answer == "SKIP":
            print(f"     → Skipped")
            skipped += 1
            continue

        print(f"     → '{answer[:60]}'")

        # Fill the field on the page
        try:
            # Find the element
            locator = None
            if field_id:
                locator = page.locator(f"#{field_id}").first
            elif field_name:
                locator = page.locator(f"[name='{field_name}']").first
            else:
                locator = page.locator(f"[aria-label='{label}']").first

            if not locator or await locator.count() == 0:
                skipped += 1
                continue

            if ftype == "select":
                # Try exact match first, then partial
                try:
                    await locator.select_option(label=answer)
                except Exception:
                    # Try to find best matching option
                    for opt in options:
                        if answer.lower() in opt.lower() or opt.lower() in answer.lower():
                            try:
                                await locator.select_option(label=opt)
                                break
                            except Exception:
                                pass

            elif ftype in ("checkbox", "radio"):
                if answer.lower() in ("yes", "true", "1"):
                    try:
                        await locator.check()
                    except Exception:
                        pass

            else:
                await locator.click()
                await locator.fill(answer)

            filled += 1
            await asyncio.sleep(0.4)

        except Exception as e:
            print(f"     ⚠ Could not fill: {e}")
            skipped += 1

    # Handle resume upload separately
    resume_path = os.environ.get("RESUME_PATH", RESUME_PATH)
    if Path(resume_path).exists():
        try:
            upload = page.locator("input[type='file']").first
            if await upload.count() > 0:
                await upload.set_input_files(resume_path)
                print(f"  ✓ Uploaded resume: {Path(resume_path).name}")
                filled += 1
                await asyncio.sleep(1)
        except Exception as e:
            print(f"  ⚠ Resume upload: {e}")
    else:
        print(f"  ⚠ Resume not found at: {resume_path}")

    print(f"\n  ✅ Filled: {filled} fields | Skipped: {skipped} fields")
    return filled


# ─────────────────────────────────────────────
#  WORKDAY STEP NAVIGATOR
# ─────────────────────────────────────────────
async def handle_workday_steps(page, company):
    """Navigate through Workday's multi-step application using Groq to fill each page."""
    step = 1
    max_steps = 15
    submitted = False
    last_url = ""

    while step <= max_steps and not submitted:
        current_url = page.url
        print(f"\n{'─'*55}")
        print(f"📄 Step {step} | {current_url[:70]}")
        print(f"{'─'*55}")
        await asyncio.sleep(2)

        # CAPTCHA check
        if await detect_captcha(page):
            await wait_for_user("🔒 CAPTCHA detected! Please solve it in the browser.")
            await asyncio.sleep(2)

        # Fill current page with Groq
        await fill_form_with_groq(page)
        await asyncio.sleep(1)

        # Find navigation buttons
        submit_btn = None
        next_btn = None

        for txt in ["Submit Application", "Submit", "Apply Now", "Send Application"]:
            btn = page.locator(f"button:has-text('{txt}')").first
            if await btn.count() > 0:
                submit_btn = btn
                print(f"  🚀 Found submit button: '{txt}'")
                break

        if not submit_btn:
            for txt in ["Next", "Save and Continue", "Continue", "Save & Continue"]:
                btn = page.locator(f"button:has-text('{txt}')").first
                if await btn.count() > 0:
                    next_btn = btn
                    print(f"  ➡ Found next button: '{txt}'")
                    break

        # Act on buttons
        if submit_btn:
            await wait_for_user("Ready to SUBMIT. Review the form in the browser, then press Enter to submit.")
            try:
                await submit_btn.click()
                await asyncio.sleep(3)
                print(f"\n🎉 Application SUBMITTED to {company}!")
                log_application(current_url, company, "Submitted ✓")
                submitted = True
            except Exception as e:
                print(f"  ⚠ Submit failed: {e}")
                await wait_for_user("Please click Submit manually in the browser, then press Enter.")
                log_application(current_url, company, "Manually Submitted")
                submitted = True

        elif next_btn:
            try:
                await next_btn.click()
                await asyncio.sleep(2.5)
                # Check if page actually changed
                if page.url == last_url:
                    print("  ⚠ Page didn't change — there may be validation errors.")
                    await wait_for_user("Fix any errors in the browser, then press Enter.")
                last_url = page.url
                step += 1
            except Exception as e:
                print(f"  ⚠ Next failed: {e}")
                await wait_for_user("Please click Next manually, then press Enter.")
                step += 1
        else:
            print("  ⚠ No Next/Submit button found on this page.")
            await wait_for_user("Please navigate manually to the next step, then press Enter.")
            if page.url != current_url:
                step += 1

    if not submitted:
        log_application(page.url, company, "Incomplete — check browser")

    return submitted


# ─────────────────────────────────────────────
#  MAIN AGENT RUNNER
# ─────────────────────────────────────────────
async def run_agent(job_url: str, company: str):
    print(f"""
╔══════════════════════════════════════════════════╗
║  🎯 Workday Agent (Groq LLaMA 3.3 70B)          ║
║  Applicant: Rajendra Dayma                       ║
║  Company:   {company:<38}║
╚══════════════════════════════════════════════════╝
""")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=150)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Auto-download resume from GitHub
        resume_path = os.environ.get("RESUME_PATH", RESUME_PATH)
        if not Path(resume_path).exists():
            github_url = os.environ.get("GITHUB_RESUME_URL", GITHUB_RESUME)
            downloaded = download_resume_from_github(github_url)
            if downloaded:
                os.environ["RESUME_PATH"] = downloaded
            else:
                print("  ⚠ Could not download resume. Upload will be skipped.")
        else:
            print(f"  ✓ Using local resume: {resume_path}")

        print(f"🌐 Opening: {job_url}")
        await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)

        # Click Apply button if on the job listing page
        for apply_text in ["Apply", "Apply Now", "Apply for Job", "Quick Apply"]:
            btn = page.locator(f"button:has-text('{apply_text}'), a:has-text('{apply_text}')").first
            if await btn.count() > 0:
                print(f"  ✓ Clicking '{apply_text}'...")
                await btn.click()
                await asyncio.sleep(2)
                break

        # Manual login step
        await wait_for_user(
            "📋 MANUAL LOGIN STEP\n"
            "   1. Log in (or create your Workday account) in the browser\n"
            "   2. Navigate to the application form\n"
            "   Then press Enter and Groq will take over"
        )

        if await detect_captcha(page):
            await wait_for_user("🔒 CAPTCHA detected! Please solve it, then press Enter.")

        # Run Groq-powered form filling
        await handle_workday_steps(page, company)

        print("\n✅ Agent finished. Press Enter to close the browser.")
        await asyncio.get_event_loop().run_in_executor(None, input)
        await browser.close()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
async def main():
    if not os.environ.get("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not set.")
        print("   Export it: export GROQ_API_KEY='gsk_...'")
        sys.exit(1)

    if len(sys.argv) >= 3:
        job_url = sys.argv[1]
        company = sys.argv[2]
    else:
        print("""
╔══════════════════════════════════════════════╗
║   🎯 Workday Agent — Powered by Groq LLaMA  ║
╚══════════════════════════════════════════════╝
        """)
        print("1. Apply to a job")
        print("2. View application log")
        print("3. Exit")
        choice = input("\nChoose (1/2/3): ").strip()

        if choice == "2":
            print_log()
            return
        elif choice == "3":
            return

        job_url = input("\nPaste Workday job URL: ").strip()
        company = input("Company name: ").strip()

    if not job_url.startswith("http"):
        print("❌ Invalid URL.")
        return

    resume_path = os.environ.get("RESUME_PATH", RESUME_PATH)
    if not Path(resume_path).exists():
        print(f"\n⚠  Resume not found at: {resume_path}")
        alt = input("   Enter full path to resume PDF (or press Enter to skip): ").strip()
        if alt and Path(alt).exists():
            os.environ["RESUME_PATH"] = alt

    await run_agent(job_url, company)


if __name__ == "__main__":
    asyncio.run(main())
