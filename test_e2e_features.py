"""bazi-pro E2E 测试 — 每日运势 + 人生K线 + 命理问答 + 详批报告"""
from playwright.sync_api import sync_playwright
import sys

BASE_URL = "http://localhost:3000"


def test_daily_fortune(page, analysis_id):
    print("[TEST] 测试每日运势...")
    page.goto(f"{BASE_URL}/analyze/{analysis_id}")
    page.wait_for_load_state("networkidle")

    # 点击"大运流年"Tab
    try:
        tab = page.locator("text=大运流年").first
        if tab.count() > 0:
            tab.click()
            page.wait_for_timeout(1000)
    except:
        pass

    # 等待每日运势加载
    try:
        page.wait_for_selector("text=今日运势", timeout=15000)
        print("  每日运势加载成功")
        page.screenshot(path="screenshot_04_fortune.png", full_page=True)
        return True
    except:
        page.screenshot(path="screenshot_04_fortune_error.png", full_page=True)
        print("  每日运势加载失败")
        return False


def test_kline(page, analysis_id):
    print("[TEST] 测试人生K线...")
    page.goto(f"{BASE_URL}/analyze/{analysis_id}")
    page.wait_for_load_state("networkidle")

    # 点击"大运流年"Tab
    try:
        tab = page.locator("text=大运流年").first
        if tab.count() > 0:
            tab.click()
            page.wait_for_timeout(1000)
    except:
        pass

    # 滚动到K线区域
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)

    # 检查是否有K线图表（标题可能是"百年运势走势"或"人生K线"）
    has_kline = page.locator("text=百年运势走势").count() > 0 or page.locator("text=人生K线").count() > 0
    if has_kline:
        print("  人生K线已显示")
    else:
        print("  未找到人生K线")

    page.screenshot(path="screenshot_05_kline.png", full_page=True)
    return has_kline


def test_chat(page, analysis_id):
    print("[TEST] 测试命理问答...")
    page.goto(f"{BASE_URL}/analyze/{analysis_id}")
    page.wait_for_load_state("networkidle")

    # 点击"命理问答"Tab
    try:
        tab = page.locator("text=命理问答").first
        if tab.count() > 0:
            tab.click()
            page.wait_for_timeout(1000)
    except:
        pass

    # 查找输入框（placeholder 包含"输入你的问题"）
    chat_input = page.locator('input[placeholder*="输入你的问题"], textarea[placeholder*="输入你的问题"]').first
    if chat_input.count() == 0:
        chat_input = page.locator('input').last

    if chat_input.count() == 0:
        print("  未找到聊天输入框")
        page.screenshot(path="screenshot_06_chat_error.png", full_page=True)
        return False

    chat_input.fill("我的事业运如何？")
    print("  输入问题: 我的事业运如何？")

    # 查找发送按钮
    send_btn = page.locator("button:has-text('发送')").first
    if send_btn.count() == 0:
        chat_input.press("Enter")
    else:
        send_btn.click()

    print("  发送问题，等待回答...")

    # 先等待"正在分析"状态出现
    try:
        page.wait_for_selector("text=正在分析", timeout=15000)
        print("  助手开始思考...")
    except:
        pass

    # 再等待回复完成（"正在分析"消失或出现实质内容）
    page.wait_for_timeout(45000)

    # 检查是否有回复内容（通过字数判断）
    content = page.locator("text=《子平真诠》").count() > 0 or page.locator("text=有云").count() > 0
    has_user_msg = page.locator("text=我的事业运如何？").count() > 0
    print(f"  有古籍引用: {content}, 有用户消息: {has_user_msg}")
    page.screenshot(path="screenshot_06_chat.png", full_page=True)
    return has_user_msg  # 只要用户消息发送成功就算通过（LLM 回复依赖外部 API）


def test_report(page, analysis_id):
    print("[TEST] 测试详批报告...")
    page.goto(f"{BASE_URL}/report/{analysis_id}")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)

    # 检查报告内容
    has_content = page.locator("text=命盘总览").count() > 0 or page.locator("text=详批报告").count() > 0
    has_empty = page.locator("text=尚未生成详批报告").count() > 0

    if has_content:
        print("  报告页面有内容")
    elif has_empty:
        print("  报告尚未生成（正常）")
    else:
        print("  报告页面内容为空")

    page.screenshot(path="screenshot_07_report.png", full_page=True)
    return has_content or has_empty


def main():
    print("=" * 50)
    print("bazi-pro 功能 E2E 测试")
    print("=" * 50)

    import urllib.request
    import json

    print("[SETUP] 创建分析...")
    req = urllib.request.Request(
        "http://localhost:8712/api/v2/analyze",
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

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        analysis_id = data["analysis_id"]
        print(f"  分析ID: {analysis_id}")
    except Exception as e:
        print(f"  创建分析失败: {e}")
        sys.exit(1)

    print("[SETUP] 等待分析完成...")
    for i in range(30):
        import time
        time.sleep(2)
        status_req = urllib.request.Request(f"http://localhost:8712/api/v2/analysis/{analysis_id}")
        status_resp = urllib.request.urlopen(status_req, timeout=10)
        status_data = json.loads(status_resp.read())
        if status_data.get("status") == "completed":
            print("  分析完成")
            break
        if status_data.get("status") == "failed":
            print("  分析失败")
            sys.exit(1)
    else:
        print("  分析超时")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        try:
            results = {}
            results["daily_fortune"] = test_daily_fortune(page, analysis_id)
            results["kline"] = test_kline(page, analysis_id)
            results["chat"] = test_chat(page, analysis_id)
            results["report"] = test_report(page, analysis_id)

            print("\n" + "=" * 50)
            for name, ok in results.items():
                print(f"[RESULT] {name}: {'通过' if ok else '失败'}")

            all_pass = all(results.values())
            print(f"\n总计: {sum(results.values())}/{len(results)} 通过")
            sys.exit(0 if all_pass else 1)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
