"""
Workday Job Application Agent — Rajendra Dayma
Powered by Groq LLaMA 3.3 70B
"""

import asyncio
import json
import os
import sys
import re
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path
from groq import Groq
from playwright.async_api import async_playwright

# ── Config ───────────────────────────────────
GITHUB_RESUME = "https://github.com/rajendradayma/Job-Application-Agent/blob/main/Rajendra_Dayma_FlowCV_Resume_2026-05-28.pdf"
LOG_FILE = Path(__file__).parent / "applications_log.json"
PROGRESS_FILE = Path(tempfile.gettempdir()) / "agent_progress.json"
RESUME_PATH = str(Path(__file__).parent / "resume.pdf")

# ── Resume context for Groq ──────────────────
RESUME_CONTEXT = """
You are filling a Workday job application form for Rajendra Dayma.

PERSONAL:
- Full name: Rajendra Dayma
- First name: Rajendra
- Last name: Dayma
- Email: rajendradayma88@gmail.com
- Phone: 7067409386 (India +91)
- City: Bhopal
- State: Madhya Pradesh
- Country: India
- ZIP: 462001
- LinkedIn: https://linkedin.com/in/rajendradayma
- GitHub: https://github.com/rajendradayma

CURRENT JOB:
- Company: DataNeuron
- Title: Data Science Intern
- Start: October 2025, still working
- Work: RAG pipelines, LLMs, AI agents, Multi-Agent Systems, Knowledge Graphs, PEFT, RBAC

PREVIOUS JOBS:
- Junior AI/ML Engineer at Xapton Solutions (Jun–Sep 2025): FastAPI, AI agents, microservices
- Data Science Intern at Code Clause (Mar–Apr 2023): data analysis, visualization
- AI Intern at IBM SkillsBuild (Jan–Mar 2023): drowsiness detection system

TOTAL EXPERIENCE: 2 years AI/ML

EDUCATION:
- Degree: Bachelor of Technology (B.Tech)
- Major: Computer Science and Engineering (Data Science)
- University: Oriental Institute of Science and Technology, Bhopal
- GPA: 8.11/10
- Graduated: 2024 (started 2020)

SKILLS: Python, LangChain, RAG, LLMs, FastAPI, Docker, PyTorch, AWS, NLP, MLOps, AI Agents

CERTS: IBM Data Science, Oracle Cloud GenAI Professional, AWS Analytics, Supervised ML

WORK AUTH: Authorized to work in India. No sponsorship needed. Open to relocate. Open to remote.

AWARDS: Rank 6, DataViz Hackathon, IIM Calcutta (Aug 2023)
"""

# ── Helpers ──────────────────────────────────
def write_progress(status, message, step=0, total=0, done=False):
    data = {"status": status, "message": message, "step": step,
            "total": total, "done": done, "timestamp": datetime.now().isoformat()}
    try:
        PROGRESS_FILE.write_text(json.dumps(data))
    except Exception:
        pass
    print(f"  [{status}] {message}")
    sys.stdout.flush()

def get_groq_client():
    api_key = None
    try:
        import streamlit as st
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in secrets or environment.")
    return Groq(api_key=api_key)

def get_raw_github_url(url):
    return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

def download_resume():
    local = Path(tempfile.gettempdir()) / "rajendra_resume.pdf"
    github_url = os.environ.get("GITHUB_RESUME_URL", GITHUB_RESUME)
    raw_url = get_raw_github_url(github_url)
    write_progress("starting", "Downloading resume from GitHub...")
    try:
        urllib.request.urlretrieve(raw_url, local)
        print(f"  Resume downloaded: {local} ({local.stat().st_size // 1024} KB)")
        return str(local)
    except Exception as e:
        print(f"  Resume download failed: {e}")
        return ""

def load_log():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text())
    return []

def save_log(entries):
    LOG_FILE.write_text(json.dumps(entries, indent=2))

def log_application(url, company, status):
    entries = load_log()
    entries.append({"url": url, "company": company, "status": status,
                    "timestamp": datetime.now().isoformat()})
    save_log(entries)

# ── Groq field answering ─────────────────────
def ask_groq(label, ftype, options=None, context=""):
    opts_text = f"\nChoose EXACTLY one of these options: {options}" if options else ""
    prompt = f"""{RESUME_CONTEXT}

A Workday form field needs to be filled:
Field label: "{label}"
Field type: {ftype}
Page context: "{context}"{opts_text}

Rules:
- Return ONLY the value, no explanation, no quotes
- Yes/No questions: return exactly Yes or No
- If options provided: return exactly one option as written
- Dates: MM/YYYY format
- Salary/compensation: return SKIP
- Unknown fields: return SKIP

Answer:"""
    try:
        r = get_groq_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=80,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        return r.choices[0].message.content.strip().strip('"\'')
    except Exception as e:
        print(f"    Groq error: {e}")
        return "SKIP"

def ask_groq_long(label, context=""):
    prompt = f"""{RESUME_CONTEXT}

Write a 2-3 sentence professional answer for this Workday form field:
Field: "{label}"
Context: "{context}"

Return ONLY the answer text:"""
    try:
        r = get_groq_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=250,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"    Groq error: {e}")
        return ""

# ── Workday-specific field extractor ─────────
async def extract_workday_fields(page):
    """
    Workday uses data-automation-id attributes on its custom React components.
    This extractor specifically targets Workday's component patterns.
    """
    # Scroll to load all lazy fields
    await page.evaluate("""
        async () => {
            for (let i = 0; i < 5; i++) {
                window.scrollBy(0, 400);
                await new Promise(r => setTimeout(r, 300));
            }
            window.scrollTo(0, 0);
        }
    """)
    await asyncio.sleep(1)

    fields = await page.evaluate("""
    () => {
        const results = [];
        const seen = new Set();

        function getText(el) {
            return el ? el.innerText.replace(/[*\\n]/g,'').trim() : '';
        }

        function findLabel(el) {
            // Walk up DOM to find associated label text
            let node = el;
            for (let i = 0; i < 8; i++) {
                if (!node) break;
                // aria-label on element itself
                if (node.getAttribute && node.getAttribute('aria-label')) {
                    return node.getAttribute('aria-label').replace(/[*]/g,'').trim();
                }
                // aria-labelledby
                if (node.getAttribute && node.getAttribute('aria-labelledby')) {
                    const ids = node.getAttribute('aria-labelledby').split(' ');
                    const t = ids.map(id => {
                        const e = document.getElementById(id);
                        return e ? getText(e) : '';
                    }).filter(Boolean).join(' ');
                    if (t) return t;
                }
                // label[for=id]
                if (el.id) {
                    const lbl = document.querySelector('label[for="' + el.id + '"]');
                    if (lbl) return getText(lbl);
                }
                // Workday label siblings / parents
                if (node.parentElement) {
                    const lbl = node.parentElement.querySelector(
                        'label, [data-automation-id="formLabel"], [class*="label"], [class*="Label"]'
                    );
                    if (lbl && lbl !== el && getText(lbl)) return getText(lbl);
                }
                node = node.parentElement;
            }
            return el.placeholder || el.getAttribute('name') || '';
        }

        function addField(label, type, el, opts=[]) {
            label = label.replace(/[*]/g,'').trim();
            if (!label || label.length > 120) return;
            const key = label.toLowerCase();
            if (seen.has(key)) return;
            seen.add(key);
            results.push({
                label,
                type,
                id: el.id || '',
                name: el.name || el.getAttribute('name') || '',
                automationId: el.getAttribute('data-automation-id') || '',
                options: opts,
                value: el.value || el.innerText?.trim() || '',
                isWorkday: true
            });
        }

        // 1. Standard inputs
        document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=file])').forEach(el => {
            if (!el.offsetParent) return;
            const label = findLabel(el);
            if (label) addField(label, el.type || 'text', el);
        });

        // 2. Textareas
        document.querySelectorAll('textarea').forEach(el => {
            if (!el.offsetParent) return;
            const label = findLabel(el);
            if (label) addField(label, 'textarea', el);
        });

        // 3. Standard selects
        document.querySelectorAll('select').forEach(el => {
            if (!el.offsetParent) return;
            const label = findLabel(el);
            const opts = Array.from(el.options).map(o => o.text.trim()).filter(t => t && !['Select...','--',''].includes(t));
            if (label) addField(label, 'select', el, opts);
        });

        // 4. Workday custom dropdowns (role=combobox or data-automation-id selects)
        document.querySelectorAll('[role="combobox"], [data-automation-id="selectWidget"], [data-automation-id="comboBox"]').forEach(el => {
            if (!el.offsetParent) return;
            const label = findLabel(el);
            if (!label) return;
            // Get options from the listbox if open, else from data attributes
            const listbox = document.querySelector('[role="listbox"]');
            const opts = listbox
                ? Array.from(listbox.querySelectorAll('[role="option"]')).map(o => o.innerText.trim()).filter(Boolean)
                : [];
            addField(label, 'workday-select', el, opts);
        });

        // 5. Workday radio buttons
        document.querySelectorAll('[role="radio"], [data-automation-id="radioBtn"]').forEach(el => {
            if (!el.offsetParent) return;
            const label = findLabel(el);
            if (label) addField(label, 'radio', el);
        });

        // 6. Workday checkboxes
        document.querySelectorAll('[role="checkbox"], [data-automation-id="checkboxPanel"]').forEach(el => {
            if (!el.offsetParent) return;
            const label = findLabel(el);
            if (label) addField(label, 'checkbox', el);
        });

        return results;
    }
    """)

    return fields


# ── Fill one field ────────────────────────────
async def fill_field(page, field, page_context):
    label = field["label"]
    ftype = field["type"]
    options = field.get("options", [])
    fid = field.get("id", "")
    fname = field.get("name", "")
    automation_id = field.get("automationId", "")

    # Ask Groq
    if ftype == "textarea":
        answer = ask_groq_long(label, page_context)
    else:
        answer = ask_groq(label, ftype, options if options else None, page_context)

    if not answer or answer.upper() == "SKIP":
        return False

    print(f"    -> '{answer[:60]}'")

    try:
        # Build locator — try multiple strategies
        locator = None

        if fid:
            locator = page.locator(f"#{fid}").first
        elif fname:
            locator = page.locator(f"[name='{fname}']").first
        elif automation_id:
            locator = page.locator(f"[data-automation-id='{automation_id}']").first

        if not locator or await locator.count() == 0:
            # Try by label text
            locator = page.get_by_label(label, exact=False).first

        if not locator or await locator.count() == 0:
            return False

        if ftype in ("select",):
            try:
                await locator.select_option(label=answer)
            except Exception:
                # Try partial match
                for opt in options:
                    if answer.lower() in opt.lower():
                        try:
                            await locator.select_option(label=opt)
                            break
                        except Exception:
                            pass

        elif ftype == "workday-select":
            # Click to open dropdown, then click the option
            await locator.click()
            await asyncio.sleep(0.8)
            # Type to filter
            await page.keyboard.type(answer[:20], delay=50)
            await asyncio.sleep(0.8)
            # Click first matching option
            option = page.locator(f"[role='option']:has-text('{answer[:20]}')").first
            if await option.count() > 0:
                await option.click()
            else:
                await page.keyboard.press("Escape")

        elif ftype in ("checkbox", "radio"):
            if answer.lower() in ("yes", "true", "1"):
                try:
                    await locator.check()
                except Exception:
                    await locator.click()

        else:
            # Text / textarea
            await locator.click()
            await locator.fill("")
            await locator.type(answer, delay=30)

        await asyncio.sleep(0.4)
        return True

    except Exception as e:
        print(f"    Could not fill '{label}': {e}")
        return False


# ── Fill entire page ──────────────────────────
async def fill_page_with_groq(page):
    write_progress("scanning", "Scanning Workday form fields...")

    page_context = ""
    try:
        heading = await page.locator("h1, h2, [data-automation-id='jobPostingHeader']").first.inner_text()
        page_context = heading[:200]
    except Exception:
        pass

    fields = await extract_workday_fields(page)
    total = len(fields)
    print(f"\n  Found {total} fields")
    write_progress("filling", f"Found {total} fields — Groq filling...", 0, total)

    filled = 0
    skipped = 0

    for i, field in enumerate(fields):
        label = field["label"]
        if field.get("value") and field["type"] not in ("workday-select",):
            print(f"  -> Already filled: {label[:40]}")
            continue

        print(f"  [{i+1}/{total}] {field['type']} | {label[:50]}")
        write_progress("filling", f"Filling: {label[:45]}", i+1, total)

        success = await fill_field(page, field, page_context)
        if success:
            filled += 1
        else:
            skipped += 1

    # Upload resume
    resume = os.environ.get("RESUME_PATH", RESUME_PATH)
    if Path(resume).exists():
        try:
            upload = page.locator("input[type='file']").first
            if await upload.count() > 0:
                await upload.set_input_files(resume)
                print("  Uploaded resume PDF")
                write_progress("filling", "Uploaded resume PDF", filled, total)
                filled += 1
                await asyncio.sleep(1)
        except Exception as e:
            print(f"  Resume upload failed: {e}")

    write_progress("filled", f"Done: {filled} filled, {skipped} skipped", filled, total)
    return filled


# ── Navigate Workday steps ────────────────────
async def navigate_workday(page, company):
    step = 1
    max_steps = 15
    submitted = False

    while step <= max_steps and not submitted:
        url = page.url
        # Detect Workday step name from page
        step_name = ""
        try:
            step_el = await page.locator(
                "[data-automation-id='currentStepName'], "
                "[data-automation-id='stepNumber'], "
                "ol li[aria-current='step'], "
                ".css-step--active, h2"
            ).first.inner_text()
            step_name = step_el.strip()[:50]
        except Exception:
            pass
        label = f"Step {step}/5: {step_name}" if step_name else f"Step {step}"
        print(f"\n--- {label} | {url[:60]}")
        write_progress("navigating", f"{label} — filling form...", step, 5)
        await asyncio.sleep(2)

        # CAPTCHA check
        for sel in ["iframe[src*='recaptcha']", "iframe[src*='hcaptcha']", "[data-sitekey]"]:
            if await page.locator(sel).count() > 0:
                write_progress("captcha", "CAPTCHA detected! Please solve it in your browser.")
                await asyncio.sleep(5)
                break

        # Fill current page
        await fill_page_with_groq(page)
        await asyncio.sleep(1)

        # Workday uses data-automation-id for navigation buttons
        # Try all known Workday button patterns
        submit_btn = None
        next_btn = None

        # All selectors to try for submit
        submit_selectors = [
            "[data-automation-id='bottomNavigationSubmitButton']",
            "[data-automation-id='submitButton']",
            "[data-automation-id='Submit']",
            "button:has-text('Submit Application')",
            "button:has-text('Submit')",
            "button:has-text('Apply Now')",
            "button:has-text('Send Application')",
            # Workday Review step final button
            "[data-automation-id='review-submit-button']",
        ]
        # Words that must NOT be in the button text (false positive guard)
        EXCLUDE_BUTTON_TEXT = ["create account", "create", "sign in", "log in", "cancel", "back", "remove"]
        # All selectors to try for next
        next_selectors = [
            "button:has-text('Save and Continue')",
            "button:has-text('Save & Continue')",
            "[data-automation-id='bottomNavigationNext']",
            "[data-automation-id='nextButton']",
            "button[data-automation-id*='next' i]",
            "button[data-automation-id*='continue' i]",
            "button[data-automation-id*='save' i]",
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Save')",
            # Workday sometimes wraps button in a div with role=button
            "[role='button']:has-text('Save and Continue')",
            "[role='button']:has-text('Next')",
        ]

        async def is_valid_btn(locator, exclude=EXCLUDE_BUTTON_TEXT):
            try:
                if await locator.count() == 0: return False
                if not await locator.is_visible(): return False
                txt = (await locator.inner_text()).strip().lower()
                if any(ex in txt for ex in exclude): return False
                return True
            except Exception:
                return False

        for sel in submit_selectors:
            try:
                btn = page.locator(sel).last
                if await is_valid_btn(btn):
                    submit_btn = btn
                    print(f"  Found submit: {sel} -> '{(await btn.inner_text()).strip()}'")
                    break
            except Exception:
                pass

        if not submit_btn:
            for sel in next_selectors:
                try:
                    btn = page.locator(sel).last
                    if await is_valid_btn(btn):
                        next_btn = btn
                        print(f"  Found next: {sel} -> '{(await btn.inner_text()).strip()}'")
                        break
                except Exception:
                    pass

        # If still not found, dump all visible buttons for debugging
        if not submit_btn and not next_btn:
            all_btns = await page.evaluate("""
                () => Array.from(document.querySelectorAll('button, [role="button"], [data-automation-id]'))
                    .filter(b => b.offsetParent)
                    .map(b => ({
                        text: b.innerText.trim().slice(0, 50),
                        automationId: b.getAttribute('data-automation-id') || '',
                    }))
                    .filter(b => b.text || b.automationId)
                    .slice(0, 15)
            """)
            btn_summary = [b["automationId"] or b["text"] for b in all_btns if b["automationId"] or b["text"]]
            print(f"  Visible elements: {btn_summary}")
            write_progress("waiting", f"Cannot find button. Visible: {btn_summary[:6]}. Retrying in 5s...")
            await asyncio.sleep(5)
            # Retry once after wait — page might still be loading
            for sel in next_selectors + submit_selectors:
                try:
                    btn = page.locator(sel).last
                    if await btn.count() > 0 and await btn.is_visible():
                        next_btn = btn
                        print(f"  Found on retry: {sel}")
                        break
                except Exception:
                    pass
            if not next_btn and not submit_btn:
                write_progress("error", f"No button found. Page elements: {btn_summary[:6]}")
                log_application(url, company, "Incomplete — button not found")
                break

        if submit_btn:
            write_progress("submitting", f"Submitting application to {company}...")
            try:
                await submit_btn.click()
                await asyncio.sleep(3)
                write_progress("submitted", f"Application submitted to {company}!", done=True)
                log_application(url, company, "Submitted")
                submitted = True
            except Exception as e:
                print(f"  Submit failed: {e}")
                write_progress("error", f"Submit failed: {e}")
                log_application(url, company, "Submit failed — check browser")
                submitted = True

        elif next_btn:
            try:
                await next_btn.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                await next_btn.click(force=True)
                await asyncio.sleep(3)
                step += 1
            except Exception as e:
                print(f"  Next click failed: {e}, trying JS click...")
                try:
                    await page.evaluate("btn => btn.click()", await next_btn.element_handle())
                    await asyncio.sleep(3)
                    step += 1
                except Exception as e2:
                    print(f"  JS click also failed: {e2}")
                    step += 1
        else:
            print("  No button found — ending")
            write_progress("error", "Could not find Next or Submit button on this page.")
            log_application(url, company, "Incomplete — no button found")
            break

    return submitted


# ── Main agent ────────────────────────────────
async def run_agent(job_url, company):
    print(f"\n=== Workday Agent | {company} ===")

    # Download resume
    resume_path = os.environ.get("RESUME_PATH", RESUME_PATH)
    if not Path(resume_path).exists():
        downloaded = download_resume()
        if downloaded:
            os.environ["RESUME_PATH"] = downloaded

    async with async_playwright() as p:
        import shutil
        sys_chrome = shutil.which("chromium") or shutil.which("chromium-browser")
        launch_args = {
            "headless": True,
            "slow_mo": 200,
            "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        }
        if sys_chrome:
            launch_args["executable_path"] = sys_chrome

        browser = await p.chromium.launch(**launch_args)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        write_progress("starting", f"Opening job page for {company}...")
        await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)

        # Click Apply on the job listing page
        for txt in ["Apply", "Apply Now", "Apply for Job"]:
            btn = page.locator(f"button:has-text('{txt}'), a:has-text('{txt}')").first
            if await btn.count() > 0:
                await btn.click()
                await asyncio.sleep(2)
                break

        # Wait for post-login URL from Streamlit or terminal
        print("\n--- WAITING FOR POST-LOGIN URL ---")
        print("Log in on your browser, navigate to the form, paste the URL.")
        write_progress("waiting", "Waiting for you to log in and send the URL...")
        sys.stdout.flush()

        post_login_url = await asyncio.get_event_loop().run_in_executor(
            None, lambda: sys.stdin.readline().strip()
        )

        if post_login_url and post_login_url.startswith("http"):
            write_progress("navigating", "Navigating to your authenticated form...")
            await page.goto(post_login_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

        await navigate_workday(page, company)

        print("\nAgent done. Closing in 5 seconds...")
        await asyncio.sleep(5)
        await browser.close()


async def main():
    if not (os.environ.get("GROQ_API_KEY")):
        # Try streamlit secrets
        try:
            import streamlit as st
            if not st.secrets.get("GROQ_API_KEY"):
                raise ValueError("No key")
        except Exception:
            print("ERROR: GROQ_API_KEY not set.")
            sys.exit(1)

    if len(sys.argv) >= 3:
        job_url, company = sys.argv[1], sys.argv[2]
    else:
        job_url = input("Workday job URL: ").strip()
        company = input("Company name: ").strip()

    if not job_url.startswith("http"):
        print("Invalid URL.")
        return

    await run_agent(job_url, company)


if __name__ == "__main__":
    asyncio.run(main())
