import json
import time
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = "c:/Users/李云龙/Desktop/bazi-pro/test-screenshots"
ERRORS = []
API_LOGS = []

def screenshot(page, name):
    path = f"{SCREENSHOT_DIR}/{name}.png"
    page.screenshot(path=path, full_page=True)
    print(f"  Screenshot: {path}")

def check_console_errors(page):
    errors = []
    def on_console(msg):
        if msg.type in ("error", "warning"):
            text = msg.text
            errors.append(f"[{msg.type}] {text}")
    page.on("console", on_console)
    return errors

def capture_api_responses(page):
    def on_response(response):
        url = response.url
        if "/api/v2/" in url:
            try:
                body = response.text()
                API_LOGS.append({"url": url, "status": response.status, "body": body[:3000]})
            except:
                pass
    page.on("response", on_response)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()

    console_errors = check_console_errors(page)
    capture_api_responses(page)

    # ===== TEST 1: Homepage Load =====
    print("\n" + "="*60)
    print("TEST 1: Homepage Load")
    print("="*60)
    page.goto("http://localhost:3000", timeout=60000)
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    screenshot(page, "01-homepage")
    title = page.title()
    print(f"  Page title: {title}")

    # ===== TEST 2: Fill Form & Paipan =====
    print("\n" + "="*60)
    print("TEST 2: Fill Form & Paipan")
    print("="*60)

    date_input = page.locator('input[type="date"]')
    time_input = page.locator('input[type="time"]')
    date_input.fill("2002-05-19")
    time_input.fill("06:30")
    print("  Date: 2002-05-19, Time: 06:30")

    female_btn = page.locator('button:has-text("女")')
    if female_btn.count() > 0:
        female_btn.click()
        print("  Gender: 女 (clicked)")
    else:
        print("  WARNING: Female button not found")

    paipan_btn = page.locator('button[type="submit"]')
    paipan_btn.click()
    print("  Clicked 排盘 button")

    page.wait_for_load_state("networkidle")
    time.sleep(4)

    paipan_table = page.locator('table')
    if paipan_table.count() > 0:
        print("  ✅ Paipan table appeared")
    else:
        print("  WARNING: Paipan table not found")

    screenshot(page, "02-paipan-result")

    # ===== TEST 3: Deep Analysis (子平法) =====
    print("\n" + "="*60)
    print("TEST 3: Deep Analysis - 子平法")
    print("="*60)

    ziping_btn = page.locator('button:has-text("子平")')
    if ziping_btn.count() > 0:
        ziping_btn.click()
        print("  School: 子平法 (clicked)")
    else:
        print("  WARNING: 子平法 button not found")

    deep_btn = page.locator('button:has-text("深度解读")')
    if deep_btn.count() > 0:
        deep_btn.click()
        print("  Clicked 深度解读 button")
    else:
        print("  WARNING: 深度解读 button not found")
        all_btns = page.locator('button').all()
        print(f"  Available buttons: {[b.text_content().strip() for b in all_btns]}")

    time.sleep(5)
    screenshot(page, "03-analysis-loading")

    for i in range(30):
        time.sleep(3)
        current_url = page.url
        if "/analyze/" in current_url:
            page.wait_for_load_state("networkidle")
            body_text = page.locator("body").inner_text()
            has_result = any(kw in body_text for kw in ["格局", "用神", "旺衰", "命理解读"])
            if has_result:
                print(f"  ✅ Analysis result appeared after {(i+1)*3}s")
                print(f"  Current URL: {current_url}")
                break
        if i % 5 == 0:
            print(f"  Waiting... ({(i+1)*3}s, url={page.url})")

    time.sleep(3)
    screenshot(page, "04-analysis-ziping-result")

    body_text = page.locator("body").inner_text()

    if "化木格" in body_text:
        print("  ❌ BUG: 仍然显示化木格！")
        ERRORS.append("化气格误判：2002-05-19 06:30 女命仍显示化木格")
    elif "月劫格" in body_text or "建禄格" in body_text:
        print("  ✅ 格局判定正确（月劫格/建禄格）")
    else:
        pattern_section = ""
        for line in body_text.split("\n"):
            if "格" in line and len(line) < 100:
                pattern_section += line + " | "
        print(f"  Pattern-related text: {pattern_section[:500]}")

    for kw in ["破格调整", "用神"]:
        if kw in body_text:
            print(f"  ✅ 子平法关键词: {kw}")

    # ===== TEST 4: Check API Response Data =====
    print("\n" + "="*60)
    print("TEST 4: Check API Response Data")
    print("="*60)

    analysis_api_logs = [l for l in API_LOGS if "/api/v2/analysis/" in l["url"]]
    for log in analysis_api_logs[-3:]:
        print(f"  API: {log['url']} (status={log['status']})")
        try:
            data = json.loads(log['body'])
            if 'result' in data:
                result = data['result']
                pattern = result.get('pattern', {})
                if isinstance(pattern, dict):
                    print(f"    result.pattern.pattern: {pattern.get('pattern', 'N/A')}")
                    print(f"    result.pattern.layer: {pattern.get('layer', 'N/A')}")
                else:
                    print(f"    result.pattern: {pattern}")
            if 'pattern' in data and isinstance(data['pattern'], str):
                print(f"    top-level pattern: {data['pattern']}")
            if 'narration' in data:
                narration = data['narration']
                if isinstance(narration, dict):
                    narr_pattern = narration.get('pattern', '')
                    if narr_pattern:
                        print(f"    narration.pattern: {narr_pattern[:200]}")
        except Exception as ex:
            print(f"    (parse error: {ex})")

    # ===== TEST 5: Direct Backend API Test =====
    print("\n" + "="*60)
    print("TEST 5: Direct Backend API Test")
    print("="*60)

    api_page = ctx.new_page()
    api_page.goto("http://127.0.0.1:8711/api/health", timeout=10000)
    api_page.wait_for_load_state("networkidle")
    health = api_page.locator("body").inner_text()
    print(f"  Health: {health[:200]}")
    api_page.close()

    # ===== TEST 6: 盲派 Analysis =====
    print("\n" + "="*60)
    print("TEST 6: 盲派 Analysis")
    print("="*60)

    page.goto("http://localhost:3000", timeout=60000)
    page.wait_for_load_state("networkidle")
    time.sleep(3)

    date_input = page.locator('input[type="date"]')
    time_input = page.locator('input[type="time"]')
    date_input.fill("2002-05-19")
    time_input.fill("06:30")

    female_btn = page.locator('button:has-text("女")')
    if female_btn.count() > 0:
        female_btn.click()

    paipan_btn = page.locator('button[type="submit"]')
    paipan_btn.click()
    page.wait_for_load_state("networkidle")
    time.sleep(4)

    mangpai_btn = page.locator('button:has-text("盲派")')
    if mangpai_btn.count() > 0:
        mangpai_btn.click()
        print("  School: 盲派 (clicked)")

    deep_btn = page.locator('button:has-text("深度解读")')
    if deep_btn.count() > 0:
        deep_btn.click()
        print("  Clicked 深度解读")

    for i in range(30):
        time.sleep(3)
        current_url = page.url
        if "/analyze/" in current_url:
            page.wait_for_load_state("networkidle")
            body_text = page.locator("body").inner_text()
            has_result = any(kw in body_text for kw in ["格局", "用神", "旺衰", "命理解读"])
            if has_result:
                print(f"  ✅ Analysis result appeared after {(i+1)*3}s")
                break

    time.sleep(3)
    screenshot(page, "05-analysis-mangpai-result")

    body_text_mangpai = page.locator("body").inner_text()
    for kw in ["宾主", "体用", "做功", "功力"]:
        if kw in body_text_mangpai:
            print(f"  ✅ 盲派关键词: {kw}")
        else:
            print(f"  ⚠️ 盲派关键词缺失: {kw}")

    # ===== TEST 7: 新派 Analysis =====
    print("\n" + "="*60)
    print("TEST 7: 新派 Analysis")
    print("="*60)

    page.goto("http://localhost:3000", timeout=60000)
    page.wait_for_load_state("networkidle")
    time.sleep(3)

    date_input = page.locator('input[type="date"]')
    time_input = page.locator('input[type="time"]')
    date_input.fill("2002-05-19")
    time_input.fill("06:30")

    female_btn = page.locator('button:has-text("女")')
    if female_btn.count() > 0:
        female_btn.click()

    paipan_btn = page.locator('button[type="submit"]')
    paipan_btn.click()
    page.wait_for_load_state("networkidle")
    time.sleep(4)

    xinpai_btn = page.locator('button:has-text("新派")')
    if xinpai_btn.count() > 0:
        xinpai_btn.click()
        print("  School: 新派 (clicked)")

    deep_btn = page.locator('button:has-text("深度解读")')
    if deep_btn.count() > 0:
        deep_btn.click()
        print("  Clicked 深度解读")

    for i in range(30):
        time.sleep(3)
        current_url = page.url
        if "/analyze/" in current_url:
            page.wait_for_load_state("networkidle")
            body_text = page.locator("body").inner_text()
            has_result = any(kw in body_text for kw in ["格局", "用神", "旺衰", "命理解读"])
            if has_result:
                print(f"  ✅ Analysis result appeared after {(i+1)*3}s")
                break

    time.sleep(3)
    screenshot(page, "06-analysis-xinpai-result")

    body_text_xinpai = page.locator("body").inner_text()
    for kw in ["百神", "空亡", "反断", "身扶"]:
        if kw in body_text_xinpai:
            print(f"  ✅ 新派关键词: {kw}")
        else:
            print(f"  ⚠️ 新派关键词缺失: {kw}")

    # ===== TEST 8: Console Error Check =====
    print("\n" + "="*60)
    print("TEST 8: Console Error Check")
    print("="*60)

    fetch_errors = [e for e in console_errors if "Failed to fetch" in e]
    type_errors = [e for e in console_errors if "TypeError" in e]
    other_errors = [e for e in console_errors if "Failed to fetch" not in e and "TypeError" not in e and "Warning" not in e and "warning" not in e and "Download the React DevTools" not in e]

    if fetch_errors:
        print(f"  ❌ Failed to fetch errors ({len(fetch_errors)}):")
        for e in fetch_errors[:5]:
            print(f"    {e}")
        ERRORS.append(f"Console: {len(fetch_errors)} 'Failed to fetch' errors")
    else:
        print("  ✅ No 'Failed to fetch' errors")

    if type_errors:
        print(f"  ❌ TypeError errors ({len(type_errors)}):")
        for e in type_errors[:5]:
            print(f"    {e}")
        ERRORS.append(f"Console: {len(type_errors)} TypeError errors")
    else:
        print("  ✅ No TypeError errors")

    if other_errors:
        print(f"  ⚠️ Other console errors ({len(other_errors)}):")
        for e in other_errors[:5]:
            print(f"    {e}")

    # ===== TEST 9: History Sidebar =====
    print("\n" + "="*60)
    print("TEST 9: History Sidebar")
    print("="*60)

    page.goto("http://localhost:3000", timeout=60000)
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    screenshot(page, "07-history-sidebar")

    # ===== SUMMARY =====
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    if ERRORS:
        print(f"\n❌ Found {len(ERRORS)} issues:")
        for i, e in enumerate(ERRORS, 1):
            print(f"  {i}. {e}")
    else:
        print("\n✅ All tests passed!")

    print(f"\nScreenshots saved to: {SCREENSHOT_DIR}/")

    browser.close()
