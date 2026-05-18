import { expect, test } from '@playwright/test';
import * as path from 'node:path';

test.describe('STEP Converter (Browser)', () => {
  test('surfaces UNSUPPORTED_STEP_CONTENT for syntactically valid empty STEP', async ({
    page,
  }) => {
    test.setTimeout(180_000);

    await page.goto('/tools/step-converter-browser');

    await page.setInputFiles(
      '#step-file',
      path.join(__dirname, 'fixtures', 'empty.step')
    );

    await page.getByRole('button', { name: 'Convert now' }).click();

    const status = page.getByTestId('step-converter-status');
    await expect(status).toHaveAttribute(
      'data-error-code',
      'UNSUPPORTED_STEP_CONTENT',
      { timeout: 120_000 }
    );

    await expect(page.getByText('Download bundle')).not.toBeVisible();
  });
});
