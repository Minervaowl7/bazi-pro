"""测试命理问答上下文扩展效果"""
from playwright.sync_api import sync_playwright
import sys
import urllib.request
import json

BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8712"


def main():
    print("=" * 50)
    print("命理问答上下文扩展测试")
    print("=" * 50)

    # 创建分析
    print("[SETUP] 创建分析...")
    req = urllib.request.Request(
        f"{API_URL}/api/v2/analyze",
        data=json.dumps({
            "性别": "女",
            "八字": "壬午 乙巳 丁亥 癸卯",
            "日主": "丁",
            "阳历": "2002-05-19 06:14",
            "detail_level": "standard",
            "school": "ziping"
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read())
    analysis_id = data["analysis_id"]
    print(f"  分析ID: {analysis_id}")

    # 等待分析完成
    print("[SETUP] 等待分析完成...")
    for i in range(30):
        import time
        time.sleep(2)
        status_req = urllib.request.Request(f"{API_URL}/api/v2/analysis/{analysis_id}")
        status_resp = urllib.request.urlopen(status_req, timeout=10)
        status_data = json.loads(status_resp.read())
        if status_data.get("status") == "completed":
            print("  分析完成")
            break
        if status_data.get("status") == "failed":
            print("  分析失败")
            sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        print("[TEST] 访问分析页面...")
        page.goto(f"{BASE_URL}/analyze/{analysis_id}")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # 点击命理问答Tab
        tab = page.locator("text=命理问答").first
        if tab.count() > 0:
            tab.click()
            page.wait_for_timeout(2000)

        page.screenshot(path="screenshot_08_chat_before.png", full_page=True)

        # 查找输入框 - 尝试多种选择器
        chat_input = page.locator('input[placeholder*="输入你的问题"]').first
        if chat_input.count() == 0:
            chat_input = page.locator('textarea[placeholder*="输入你的问题"]').first
        if chat_input.count() == 0:
            chat_input = page.locator('input[type="text"]').last
        if chat_input.count() == 0:
            chat_input = page.locator('textarea').last

        print(f"  找到输入框: {chat_input.count() > 0}")

        if chat_input.count() == 0:
            print("  未找到聊天输入框")
            page.screenshot(path="screenshot_08_chat_error.png", full_page=True)
            sys.exit(1)

        # 问一个需要知道年龄的问题
        chat_input.fill("我今年运势如何？")
        print("  提问: 我今年运势如何？")

        send_btn = page.locator("button:has-text('发送')").first
        if send_btn.count() == 0:
            chat_input.press("Enter")
        else:
            send_btn.click()

        # 等待回复
        print("  等待回复...")
        page.wait_for_timeout(60000)

        # 检查回复内容
        content = page.content()
        has_age = "24岁" in content or "24" in content
        has_dayun = "壬寅" in content or "大运" in content
        has_liunian = "丙午" in content or "流年" in content

        print(f"  提到年龄: {has_age}")
        print(f"  提到大运: {has_dayun}")
        print(f"  提到流年: {has_liunian}")

        page.screenshot(path="screenshot_08_chat_context.png", full_page=True)

        if has_age and has_dayun:
            print("\n[RESULT] 通过 - LLM 正确使用了命盘上下文")
            sys.exit(0)
        else:
            print("\n[RESULT] 失败 - LLM 未正确使用命盘上下文")
            sys.exit(1)

        browser.close()


if __name__ == "__main__":
    main()
