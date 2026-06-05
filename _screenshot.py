from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    page.goto("http://localhost:3000")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.screenshot(path="c:/Users/李云龙/Desktop/bazi-pro/_shot_home.png", full_page=True)

    browser.close()
