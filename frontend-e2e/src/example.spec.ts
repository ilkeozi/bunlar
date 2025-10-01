import { test, expect } from '@playwright/test';

test.describe('Atomic Explorer', () => {
  test('renders the default hydrogen atom stats', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { level: 1 })).toHaveText('Atomic Explorer');
    await expect(page.getByRole('heading', { level: 2 })).toHaveText('Hydrogen');

    await expect(page.getByText('Atomic number').locator('xpath=following-sibling::dd[1]')).toHaveText('1');
    await expect(page.getByText('Protons').locator('xpath=following-sibling::dd[1]')).toHaveText('1');
    await expect(page.getByText('Electrons').locator('xpath=following-sibling::dd[1]')).toHaveText('1');
  });

  test('updates stats and selection when choosing carbon', async ({ page }) => {
    await page.goto('/');

    await page.selectOption('#element-select', 'C');

    await expect(page.getByRole('heading', { level: 2 })).toHaveText('Carbon');
    await expect(page.getByText('Atomic number').locator('xpath=following-sibling::dd[1]')).toHaveText('6');
    await expect(page.getByText('Protons').locator('xpath=following-sibling::dd[1]')).toHaveText('6');
    await expect(page.getByText('Electrons').locator('xpath=following-sibling::dd[1]')).toHaveText('6');

    const canvas = page.locator('canvas');
    await expect(canvas).toBeVisible();
  });
});
