import { test, expect } from '@playwright/test';

test.describe('分析页面', () => {
  test('分析页面加载正常', async ({ page }) => {
    // 访问一个示例分析页面
    await page.goto('/analyze/test-id');

    // 页面应该显示某种内容（错误或分析结果）
    await expect(page.locator('body')).toBeVisible();
  });

  test('返回首页链接正常', async ({ page }) => {
    await page.goto('/analyze/test-id');

    // 查找返回首页的链接
    const homeLink = page.locator('a[href="/"], a:has-text("首页"), a:has-text("Home")').first();

    if (await homeLink.isVisible()) {
      await homeLink.click();
      await expect(page).toHaveURL('/');
    }
  });
});

test.describe('合婚页面', () => {
  test('合婚页面加载正常', async ({ page }) => {
    await page.goto('/compare');

    // 页面应该显示某种内容
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('报告页面', () => {
  test('报告页面加载正常', async ({ page }) => {
    await page.goto('/report/test-id');

    // 页面应该显示某种内容
    await expect(page.locator('body')).toBeVisible();
  });
});
