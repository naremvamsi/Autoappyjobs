from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("https://www.naukri.com/devops-engineer-jobs")

    page.wait_for_timeout(5000)

    jobs = page.locator("a.title")

    count = min(jobs.count(), 10)

    print(f"Found {count} jobs")

    for i in range(count):
        print(jobs.nth(i).inner_text())

    input("Press Enter to close...")
    browser.close()