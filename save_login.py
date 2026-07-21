from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        slow_mo=500
    )

    context = browser.new_context()

    page = context.new_page()

    print("Opening Naukri...")

    page.goto(
        "https://www.naukri.com",
        wait_until="domcontentloaded",
        timeout=120000
    )

    print("Please login manually in the browser window.")
    print("After login is successful, press ENTER here.")

    input()

    context.storage_state(path="state.json")

    print("Login saved successfully!")
    print("state.json file created.")

    browser.close()