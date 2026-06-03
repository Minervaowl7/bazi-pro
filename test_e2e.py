"""bazi-pro E2E 测试 — 首页加载 + 排盘流程"""
from playwright.sync_api import sync_playwright
import time
import sys

BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8712"

def test_homepage(page):
    print("[TEST] 访问首页...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")
    title = page.title()
    print(f"  页面标题: {title}")
    page.screenshot(path="screenshot_01_home.png", full_page=True)

    # 检查是否有排盘按钮
    buttons = page.locator("button").all()
    print(f"  页面按钮数: {len(buttons)}")
    for btn in buttons[:5]:
        text = btn.inner_text().strip()
        if text:
            print(f"    - {text}")

    # 检查是否有输入框
    inputs = page.locator("input").all()
    print(f"  输入框数: {len(inputs)}")

    return len(buttons) > 0 and len(inputs) > 0


def test_paipan(page):
    print("[TEST] 测试排盘流程...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 选择日期
    date_input = page.locator('input[type="date"]')
    if date_input.count() == 0:
        print("  未找到日期输入框")
        return False

    date_input.fill("2002-05-19")
    print("  填写日期: 2002-05-19")

    # 选择时间
    time_input = page.locator('input[type="time"]')
    if time_input.count() > 0:
        time_input.fill("06:14")
        print("  填写时间: 06:14")

    # 点击排盘按钮
    paipan_btn = page.locator("button:has-text('排盘')").first
    if paipan_btn.count() == 0:
        print("  未找到排盘按钮")
        return False

    paipan_btn.click()
    print("  点击排盘...")

    # 等待排盘结果
    try:
        page.wait_for_selector("text=八字命盘", timeout=15000)
        print("  排盘成功！")
    except:
        print("  排盘超时，截图查看...")
        page.screenshot(path="screenshot_02_paipan_error.png", full_page=True)
        return False

    page.screenshot(path="screenshot_02_paipan.png", full_page=True)
    return True


def test_api_health():
    """测试后端 API 是否可用"""
    import urllib.request
    print("[TEST] 测试后端 API...")
    try:
        resp = urllib.request.urlopen(f"{API_URL}/api/v2/history", timeout=5)
        print(f"  状态码: {resp.status}")
        return resp.status == 200
    except Exception as e:
        print(f"  API 不可用: {e}")
        return False


def main():
    print("=" * 50)
    print("bazi-pro E2E 测试")
    print("=" * 50)

    # API 健康检查
    if not test_api_health():
        print("后端 API 未启动，跳过测试")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        try:
            ok1 = test_homepage(page)
            print(f"[RESULT] 首页测试: {'通过' if ok1 else '失败'}")

            ok2 = test_paipan(page)
            print(f"[RESULT] 排盘测试: {'通过' if ok2 else '失败'}")

            if ok1 and ok2:
                print("\n所有测试通过！")
                sys.exit(0)
            else:
                print("\n部分测试失败")
                sys.exit(1)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
