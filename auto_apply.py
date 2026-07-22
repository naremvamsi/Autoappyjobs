import os
import re
import time
from html import unescape
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

from config import ANSWERS

SEARCH_URL = "https://www.naukri.com/devops-engineer-azure-devops-engineer-site-reliability-engineer-azure-cloud-jobs?k=devops%20engineer%2C%20azure%20devops%20engineer%2C%20site%20reliability%20engineer%2C%20azure%20cloud&nignbevent_src=jobsearchDeskGNB"
APPLIED_FILE = "applied_jobs.txt"
EXTERNAL_SITES = ["workday", "oracle", "greenhouse", "lever", "successfactors"]


def should_launch_headless():
    return os.getenv("GITHUB_ACTIONS") == "true"


def load_applied():
    try:
        with open(APPLIED_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    except Exception:
        return set()


def extract_job_links_from_html(html_text):
    if not html_text:
        return []

    links = []
    seen = set()
    for match in re.finditer(r'https?://[^\s"\']+|/job-listings[^\s"\']*', html_text, re.IGNORECASE):
        href = match.group(0)
        normalized = unescape(href).strip()
        if not normalized:
            continue
        if normalized.startswith("/"):
            normalized = urljoin("https://www.naukri.com", normalized)
        if "job-listings" not in normalized.lower():
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        links.append(normalized)

    return links


def save_applied(url):
    with open(APPLIED_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")


def get_answer_for_body(body_text):
    if not body_text:
        return None

    body_lower = body_text.lower()
    for keyword, answer in ANSWERS.items():
        if keyword.lower() in body_lower:
            return str(answer)
    return None


def try_fill_field(page, value):
    fields = page.locator("input, textarea, select")
    count = fields.count()

    for i in range(count):
        field = fields.nth(i)
        try:
            if not field.is_visible():
                continue

            tag_name = field.evaluate("el => (el.tagName || '').toLowerCase()")
            input_type = field.get_attribute("type") or ""

            if tag_name == "select":
                field.select_option(index=0)
            elif input_type.lower() in {"checkbox", "radio"}:
                if not field.is_checked():
                    field.check()
            else:
                field.fill(str(value))
            return True
        except Exception:
            continue

    return False


def fill_common_fields(page, body_text):
    body_lower = (body_text or "").lower()

    for keyword in ["sre", "devops", "azure", "kubernetes", "Azure Devops" , "terraform", "total", "current ctc", "expected ctc", "notice"]:
        if keyword in body_lower:
            answer = ANSWERS.get(keyword)
            if answer and try_fill_field(page, answer):
                return True

    for keyword in ["experience", "ctc", "notice", "salary"]:
        if keyword in body_lower:
            answer = ANSWERS.get("total") or ANSWERS.get("expected ctc") or ANSWERS.get("notice")
            if answer and try_fill_field(page, answer):
                return True

    return try_fill_field(page, "5")


def click_best_action(page):
    action_texts = ["submit", "apply", "continue", "next", "review"]

    for text in action_texts:
        try:
            element = page.get_by_text(text, exact=False).first
            if element.is_visible():
                element.click()
                return True
        except Exception:
            continue

    buttons = page.locator("button")
    count = buttons.count()
    for i in range(count):
        try:
            btn = buttons.nth(i)
            if btn.is_visible():
                txt = btn.inner_text().lower()
                if any(key in txt for key in action_texts):
                    btn.click()
                    return True
        except Exception:
            continue

    return False


def process_workday(page):
    try:
        print("Handling Workday flow")
        # Workday often uses links/buttons labelled 'Apply on company site' or 'Apply'
        click_best_action(page)
        time.sleep(2)
        body = page.locator("body").inner_text()
        fill_common_fields(page, body)
        click_best_action(page)
    except Exception as e:
        print("Workday handler failed:", e)


def process_greenhouse(page):
    try:
        print("Handling Greenhouse flow")
        click_best_action(page)
        time.sleep(2)
        body = page.locator("body").inner_text()
        fill_common_fields(page, body)
        click_best_action(page)
    except Exception as e:
        print("Greenhouse handler failed:", e)


def process_lever(page):
    try:
        print("Handling Lever flow")
        click_best_action(page)
        time.sleep(2)
        body = page.locator("body").inner_text()
        fill_common_fields(page, body)
        click_best_action(page)
    except Exception as e:
        print("Lever handler failed:", e)


def process_job_page(page, job_url):
    print("Processing:", job_url)
    current_url = page.url.lower()

    # Route to site-specific handlers where possible
    if "workday" in current_url:
        print("External site detected: workday")
        process_workday(page)
        return
    if "greenhouse" in current_url:
        print("External site detected: greenhouse")
        process_greenhouse(page)
        return
    if "lever" in current_url:
        print("External site detected: lever")
        process_lever(page)
        return

    # Generic flow for other pages
    time.sleep(5)

    apply_btn = None
    try:
        apply_btn = page.get_by_text("Apply", exact=False).first
    except Exception:
        pass

    if apply_btn:
        try:
            apply_btn.click()
            print("Apply clicked")
            time.sleep(4)
        except Exception as exc:
            print("Could not click Apply button:", exc)

    body_text = page.locator("body").inner_text().lower()

    try:
        fill_common_fields(page, body_text)
        click_best_action(page)
    except Exception as exc:
        print("Question handling skipped:", exc)


def main():
    applied_jobs = load_applied()

    with sync_playwright() as p:
        headless = should_launch_headless()
        launch_args = ["--no-sandbox"] if headless else []
        browser = p.chromium.launch(headless=headless, args=launch_args, slow_mo=1000 if not headless else 0)
        context = browser.new_context(storage_state="state.json")
        page = context.new_page()

        print("Opening Naukri...")
        page.goto(SEARCH_URL, timeout=120000, wait_until="domcontentloaded")
        time.sleep(10)

        try:
            # Try several label variants to reliably select the recent-date filter
            applied_filter = False
            candidates = ["Last 10 days", "Last 7 days", "Last 1 week", "Last 2 days", "Last 15 days"]
            for label in candidates:
                try:
                    el = page.get_by_text(label, exact=False).first
                    if el and el.is_visible():
                        el.click()
                        print(f"{label} filter applied")
                        time.sleep(5)
                        applied_filter = True
                        break
                except Exception:
                    continue

            # As a fallback, click any control that contains the text "Last" then try again
            if not applied_filter:
                try:
                    last_ctrl = page.get_by_text("Last", exact=False).first
                    if last_ctrl and last_ctrl.is_visible():
                        last_ctrl.click()
                        time.sleep(1)
                        for label in candidates:
                            try:
                                el = page.get_by_text(label, exact=False).first
                                if el and el.is_visible():
                                    el.click()
                                    print(f"{label} filter applied")
                                    time.sleep(5)
                                    applied_filter = True
                                    break
                            except Exception:
                                continue
                except Exception:
                    pass

            if not applied_filter:
                print("Could not apply Last 10 Days filter")
        except Exception:
            print("Could not apply Last 10 Days filter")

        page_html = page.content()
        links = extract_job_links_from_html(page_html)

        if not links:
            for a in page.locator("a").all():
                try:
                    href = a.get_attribute("href")
                    if href and "job-listings" in href:
                        links.append(href)
                except Exception:
                    pass

        links = list(dict.fromkeys(links))
        print(f"Found {len(links)} jobs")

        for job_url in links[:50]:
            if job_url in applied_jobs:
                continue

            try:
                job_page = context.new_page()
                job_page.goto(job_url, timeout=120000, wait_until="domcontentloaded")
                process_job_page(job_page, job_url)
                save_applied(job_url)
                print("Processed:", job_url)
                time.sleep(3)
                job_page.close()
            except Exception as e:
                print("Error:", e)

        browser.close()

    print("Completed")


if __name__ == "__main__":
    main()
