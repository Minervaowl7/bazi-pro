"""bazi-pro E2E 测试 — 深度分析流程"""
from playwright.sync_api import sync_playwright
import sys

BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8712"


def test_full_analysis(page):
    print("[TEST] 测试完整分析流程...")
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 填写日期和时间
    page.locator('input[type="date"]').fill("2002-05-19")
    page.locator('input[type="time"]').fill("06:14")
    print("  填写出生信息")

    # 点击排盘
    page.locator("button:has-text('排盘')").first.click()
    page.wait_for_selector("text=八字命盘", timeout=15000)
    print("  排盘完成")

    # 选择流派（子平法）
    page.locator("text=传统子平法").first.click()
    print("  选择子平法")

    # 点击深度解读
    page.locator("button:has-text('深度解读')").first.click()
    print("  点击深度解读，等待分析...")

    # 等待分析完成或失败
    try:
        # 等待分析完成标志
        page.wait_for_selector("text=旺衰", timeout=120000)
        print("  分析完成！")
    except:
        # 检查是否失败
        error = page.locator("text=分析失败").count()
        if error > 0:
            print("  分析失败！")
            page.screenshot(path="screenshot_03_analysis_failed.png", full_page=True)
            return False
        else:
            print("  分析超时，截图查看...")
            page.screenshot(path="screenshot_03_analysis_timeout.png", full_page=True)
            return False

    page.screenshot(path="screenshot_03_analysis.png", full_page=True)

    # 检查关键数据是否显示
    has_day_master = page.locator("text=日主").count() > 0
    has_pattern = page.locator("text=格局").count() > 0
    print(f"  显示日主: {has_day_master}, 显示格局: {has_pattern}")

    return has_day_master and has_pattern


def main():
    print("=" * 50)
    print("bazi-pro 深度分析 E2E 测试")
    print("=" * 50)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        try:
            ok = test_full_analysis(page)
            print(f"[RESULT] 分析测试: {'通过' if ok else '失败'}")
            sys.exit(0 if ok else 1)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
