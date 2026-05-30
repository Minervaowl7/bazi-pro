from playwright.sync_api import sync_playwright
import os

SCREENSHOT_DIR = "/workspace/test-screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})

    console_logs = []
    page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

    page_errors = []
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    print("=== Step 1: Navigate to homepage ===")
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(2000)

    page.screenshot(path=f"{SCREENSHOT_DIR}/01-homepage.png", full_page=True)
    print(f"Page title: {page.title()}")
    print(f"Page URL: {page.url}")

    body_text = page.locator("body").inner_text()
    print(f"Body text preview: {body_text[:200]}")

    print("\n=== Step 2: Check form elements ===")
    date_input = page.locator('input[type="date"]')
    time_input = page.locator('input[type="time"]')
    submit_btn = page.locator('button[type="submit"]')
    gender_btns = page.locator('button[type="button"]')

    print(f"Date input count: {date_input.count()}")
    print(f"Time input count: {time_input.count()}")
    print(f"Submit button count: {submit_btn.count()}")
    print(f"Gender buttons count: {gender_btns.count()}")

    if submit_btn.count() > 0:
        print(f"Submit button text: {submit_btn.first.inner_text()}")

    print("\n=== Step 3: Fill form and submit ===")
    if date_input.count() > 0:
        date_input.first.fill("1990-06-15")
        print("Filled date: 1990-06-15")

    if time_input.count() > 0:
        time_input.first.fill("12:00")
        print("Filled time: 12:00")

    page.screenshot(path=f"{SCREENSHOT_DIR}/02-form-filled.png", full_page=True)

    if submit_btn.count() > 0:
        print("Clicking submit button...")
        submit_btn.first.click()
        page.wait_for_timeout(5000)
        page.screenshot(path=f"{SCREENSHOT_DIR}/03-after-paipan.png", full_page=True)

        body_text_after = page.locator("body").inner_text()
        print(f"Body text after paipan: {body_text_after[:400]}")

        deep_analysis_btn = page.locator('button:has-text("深度解读")')
        print(f"Deep analysis button count: {deep_analysis_btn.count()}")
    else:
        print("ERROR: No submit button found!")

    print("\n=== Step 4: Check console logs ===")
    for log in console_logs[-20:]:
        print(f"  {log}")

    print("\n=== Step 5: Check page errors ===")
    for err in page_errors:
        print(f"  ERROR: {err}")

    browser.close()
    print("\n=== Test complete ===")
