from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    console_errors = []
    page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ["error", "warning"] else None)
    page.on("pageerror", lambda err: console_errors.append(f"[pageerror] {err}"))

    print("=== Step 1: Navigate to homepage ===")
    page.goto("http://localhost:3000", wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(2000)

    print("=== Step 2: Take screenshot of initial state ===")
    page.screenshot(path="/workspace/test_screenshots/step2_initial.png", full_page=True)

    print("=== Step 3: Check page content ===")
    html = page.content()
    print(f"Page title: {page.title()}")
    print(f"HTML length: {len(html)}")
    print(f"data-theme attr: {page.evaluate('document.documentElement.getAttribute(\"data-theme\")')}")

    print("=== Step 4: Check form elements ===")
    date_input = page.locator('input[type="date"]')
    time_input = page.locator('input[type="time"]')
    submit_btn = page.locator('button[type="submit"]')
    print(f"Date input count: {date_input.count()}")
    print(f"Time input count: {time_input.count()}")
    print(f"Submit button count: {submit_btn.count()}")
    if submit_btn.count() > 0:
        print(f"Submit button text: {submit_btn.first.text_content()}")
        print(f"Submit button disabled: {submit_btn.first.is_disabled()}")

    print("=== Step 5: Fill form ===")
    date_input.fill("1990-01-15")
    time_input.fill("12:00")
    page.wait_for_timeout(500)

    print("=== Step 6: Take screenshot after fill ===")
    page.screenshot(path="/workspace/test_screenshots/step6_filled.png", full_page=True)

    print("=== Step 7: Click submit button ===")
    submit_btn.click()
    page.wait_for_timeout(5000)

    print("=== Step 8: Take screenshot after submit ===")
    page.screenshot(path="/workspace/test_screenshots/step8_after_submit.png", full_page=True)

    print("=== Step 9: Check for paipan result ===")
    paipan_section = page.locator("text=八字命盘")
    print(f"Paipan section visible: {paipan_section.count() > 0}")

    error_msg = page.locator("text=排盘失败")
    print(f"Error message visible: {error_msg.count() > 0}")

    page_content = page.content()
    if "己巳" in page_content or "庚辰" in page_content:
        print("SUCCESS: Paipan result is displayed on page!")
    else:
        print("FAIL: No paipan result found on page")

    print("=== Step 10: Check console errors ===")
    if console_errors:
        print(f"Console errors/warnings ({len(console_errors)}):")
        for e in console_errors:
            print(f"  {e}")
    else:
        print("No console errors")

    print("=== Step 11: Direct API call from browser ===")
    result = page.evaluate("""async () => {
        try {
            const res = await fetch('http://127.0.0.1:8711/api/v2/paipan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({性别: '男', 阳历: '1990-01-15 12:00'})
            });
            const data = await res.json();
            return JSON.stringify(data);
        } catch(e) {
            return 'FETCH_ERROR: ' + e.message;
        }
    }""")
    print(f"Direct API call from browser: {result[:300]}")

    browser.close()
