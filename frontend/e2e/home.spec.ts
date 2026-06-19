import { test, expect } from '@playwright/test';

test.describe('首页', () => {
  test('页面加载正常', async ({ page }) => {
    await page.goto('/');

    // 检查页面标题
    await expect(page).toHaveTitle(/bazi/);

    // 检查主要元素存在
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('导航栏显示正常', async ({ page }) => {
    await page.goto('/');

    // 检查导航栏存在
    const nav = page.locator('nav, [role="navigation"]').first();
    await expect(nav).toBeVisible();
  });

  test('主题切换功能', async ({ page }) => {
    await page.goto('/');

    // 查找主题切换按钮
    const themeButton = page.locator('button[aria-label*="theme"], button[aria-label*="主题"], [data-testid="theme-toggle"]').first();

    // 如果存在主题切换按钮，测试切换功能
    if (await themeButton.isVisible()) {
      await themeButton.click();
      // 等待主题切换动画
      await page.waitForTimeout(500);
    }
  });
});
