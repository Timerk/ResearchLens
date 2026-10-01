import { expect, test, type Page } from '@playwright/test';
import { responses, technicalPassage } from '../testing/fixtures';

async function mockHealth(page: Page, mode = 'openai') {
  await page.route('**/api/health', (route) => route.fulfill({ json: { status: 'ok', mode } }));
}

async function expectFocusRing(page: Page) {
  const ring = await page.evaluate(() => {
    const style = getComputedStyle(document.activeElement!);
    return { style: style.outlineStyle, width: parseFloat(style.outlineWidth) };
  });
  expect(ring.style).toBe('solid');
  expect(ring.width).toBeGreaterThanOrEqual(2);
}

test('desktop keyboard submission, loading, citation expansion and source links', async ({
  page,
}, testInfo) => {
  await mockHealth(page);
  let requests = 0;
  let release!: () => void;
  const responseReady = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/api/ask', async (route) => {
    requests++;
    expect(route.request().postDataJSON()).toEqual({
      question: 'Which illumination methods have limitations?',
    });
    await responseReady;
    await route.fulfill({ json: responses.answered });
  });
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Ask documents' })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('desktop-initial.png'), fullPage: true });
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'ResearchLens / lab' })).toBeFocused();
  await expectFocusRing(page);
  await page.keyboard.press('Tab');
  const input = page.getByRole('textbox', { name: 'Your research question' });
  await expect(input).toBeFocused();
  await expectFocusRing(page);
  await input.fill('  Which illumination methods have limitations?  ');
  await page.keyboard.press('Tab');
  const submit = page.getByRole('button', { name: 'Ask documents' });
  await expect(submit).toBeFocused();
  await expectFocusRing(page);
  await page.keyboard.press('Enter');
  await expect(page.getByRole('status')).toHaveText('Searching documents…');
  await expect(input).toHaveJSProperty('readOnly', true);
  await expect(page.getByRole('button', { name: 'Working' })).toBeFocused();
  await expect(page.getByRole('button', { name: 'Working' })).toHaveAttribute(
    'aria-disabled',
    'true',
  );
  await page.keyboard.press('Enter');
  await page.keyboard.press('Space');
  await page.screenshot({ path: testInfo.outputPath('desktop-loading.png'), fullPage: true });
  release();
  await expect(page.getByRole('heading', { name: 'Answer with source references' })).toBeVisible();
  expect(requests).toBe(1);
  await expect(submit).toBeFocused();
  await expect(page.getByRole('status')).toHaveText('Answer with source references ready.');
  await page.keyboard.press('Tab');
  const citation = page.locator('summary').filter({ hasText: technicalPassage.title });
  await expect(citation).toBeFocused();
  await expectFocusRing(page);
  await page.keyboard.press('Enter');
  await expect(citation.locator('..')).toHaveAttribute('open', '');
  await expect(citation.locator('..').getByRole('blockquote')).toHaveText(technicalPassage.text);
  await page.keyboard.press('Tab');
  const reference = page.getByText('Inspect reference', { exact: true });
  await expect(reference).toBeFocused();
  await expectFocusRing(page);
  await page.keyboard.press('Space');
  await expect(reference.locator('..')).toHaveAttribute('open', '');
  await page.keyboard.press('Tab');
  const license = page.getByRole('link', { name: 'CC-BY-4.0' });
  await expect(license).toBeFocused();
  await expectFocusRing(page);
  await page.keyboard.press('Tab');
  const source = page.getByRole('link', { name: 'Original document' });
  await expect(source).toBeFocused();
  await expect(source).toHaveAttribute('href', technicalPassage.source_url!);
  await expect(source).toHaveAttribute('target', '_blank');
  await expect(source).toHaveAttribute('rel', 'noopener noreferrer');
  await expectFocusRing(page);
  await page.screenshot({
    path: testInfo.outputPath('desktop-answer-expanded.png'),
    fullPage: true,
  });
  expect(errors).toEqual([]);
});

test('API error alert and keyboard retry recover without stale content', async ({
  page,
}, testInfo) => {
  await mockHealth(page);
  let requests = 0;
  await page.route('**/api/ask', (route) => {
    requests++;
    return requests === 1
      ? route.fulfill({ status: 504, json: { detail: 'OpenAI timed out. Please try again.' } })
      : route.fulfill({ json: responses.insufficient });
  });
  await page.goto('/');
  const submit = page.getByRole('button', { name: 'Ask documents' });
  await submit.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('alert')).toHaveText('OpenAI timed out. Please try again.');
  await expect(submit).toBeFocused();
  await page.screenshot({ path: testInfo.outputPath('desktop-error.png'), fullPage: true });
  await page.keyboard.press('Enter');
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Insufficient evidence' })).toBeVisible();
  await expect(page.getByRole('status')).toHaveText('Insufficient evidence ready.');
  await expect(page.getByText('Inspect reference', { exact: true })).toBeVisible();
  expect(requests).toBe(2);
  await page.screenshot({ path: testInfo.outputPath('desktop-insufficient.png'), fullPage: true });
});

test('320px mobile validation, long metadata, preview, no matches and answer', async ({
  page,
}, testInfo) => {
  await page.setViewportSize({ width: 320, height: 740 });
  await mockHealth(page, 'local_preview');
  let requests = 0;
  await page.route('**/api/ask', (route) => {
    requests++;
    return route.fulfill({
      json:
        requests === 1
          ? {
              ...responses.preview,
              passages: [
                { ...technicalPassage, source_locator: './body/' + 'long-location'.repeat(25) },
              ],
            }
          : requests === 2
            ? responses.noMatches
            : responses.answered,
    });
  });
  await page.goto('/');
  const input = page.getByRole('textbox', { name: 'Your research question' });
  const submit = page.getByRole('button', { name: 'Find passages' });
  await input.fill(' a ');
  await expect(submit).toBeDisabled();
  await expect(input).toHaveAttribute('aria-invalid', 'true');
  await expect(
    page.getByText('Enter at least 3 characters, excluding surrounding spaces.'),
  ).toBeVisible();
  await input.fill('Which illumination methods have limitations?');
  await expect(submit).toBeEnabled();
  await submit.click();
  await expect(
    page.getByRole('heading', { name: 'Retrieved passages', exact: true }),
  ).toBeVisible();
  await page.getByText('Inspect reference', { exact: true }).click();
  await expect(page.getByRole('link', { name: 'Original document' })).toBeVisible();
  const size = await page.evaluate(() => ({
    content: document.documentElement.scrollWidth,
    viewport: innerWidth,
  }));
  expect(size.content).toBeLessThanOrEqual(size.viewport);
  await page.screenshot({
    path: testInfo.outputPath('mobile-preview-expanded.png'),
    fullPage: true,
  });
  await input.fill('What about an unrelated topic?');
  await submit.click();
  await expect(page.getByRole('heading', { name: 'No matching passages' })).toBeVisible();
  await expect(page.locator('article')).toHaveCount(0);
  await expect(page.getByRole('status')).toHaveText('No matching passages ready.');
  await page.screenshot({ path: testInfo.outputPath('mobile-no-matches.png'), fullPage: true });
  await input.fill('Why combine illumination methods?');
  await submit.click();
  await expect(page.getByRole('heading', { name: 'Answer with source references' })).toBeVisible();
  await page.locator('summary').filter({ hasText: technicalPassage.title }).click();
  await page.getByText('Inspect reference', { exact: true }).click();
  await expect(page.getByRole('link', { name: 'Original document' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
  await page.screenshot({
    path: testInfo.outputPath('mobile-answer-expanded.png'),
    fullPage: true,
  });
});
