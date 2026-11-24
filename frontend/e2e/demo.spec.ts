import { expect, test } from '@playwright/test';
import { demoResponses, demoStatus, recordedLabel, technicalPassage } from '../testing/fixtures';

test('demo flow: recorded replay, one live answer, then free preview after the limit', async ({
  page,
}, testInfo) => {
  await page.route('**/api/health', (route) =>
    route.fulfill({ json: { status: 'ok', mode: 'openai', retrieval_tier: 'light' } }),
  );
  await page.route('**/api/demo', (route) => route.fulfill({ json: demoStatus }));
  let replays = 0;
  await page.route('**/api/examples/mock-example', (route) => {
    replays++;
    return route.fulfill({ json: demoResponses.recorded });
  });
  const asks: { headers: Record<string, string>; body: unknown }[] = [];
  await page.route('**/api/ask', (route) => {
    asks.push({ headers: route.request().headers(), body: route.request().postDataJSON() });
    return asks.length === 1
      ? route.fulfill({ json: demoResponses.live })
      : route.fulfill({
          status: 429,
          headers: { 'Retry-After': '3600' },
          json: { ...demoResponses.limited, detail: demoResponses.limited.notice },
        });
  });
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/ask');

  // 1. Replay: a real recorded answer, clearly labelled, without an ask request.
  await page.getByRole('button', { name: 'Mock recorded example' }).click();
  await expect(page.getByTestId('replay-label')).toContainText(recordedLabel);
  await expect(page.getByText('Recorded, no API call')).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Your research question' })).toHaveValue(
    demoStatus.examples[0].question,
  );
  await page.locator('summary').filter({ hasText: technicalPassage.title }).first().click();
  await expect(page.getByRole('blockquote').first()).toHaveText(technicalPassage.text);
  expect(replays).toBe(1);
  expect(asks).toHaveLength(0);
  await page.screenshot({ path: testInfo.outputPath('demo-replay.png'), fullPage: true });

  // 2. A live answer uses the last of today's quota.
  const status = page.getByTestId('live-status');
  await expect(status).toContainText('1 of 5');
  await page.getByRole('textbox', { name: 'Your research question' }).fill('What limits glass?');
  await page.getByRole('button', { name: 'Ask the papers' }).click();
  await expect(page.getByRole('heading', { name: 'Answer with source references' })).toBeVisible();
  await expect(status).toContainText('No live answers left today');
  await expect(page.getByTestId('replay-label')).toHaveCount(0);

  // 3. Over the limit: HTTP 429 falls back to the free preview with a friendly notice.
  await page.getByRole('button', { name: 'Find passages' }).click();
  await expect(page.getByTestId('fallback-notice')).toContainText("used today's live answers");
  await expect(
    page.getByRole('heading', { name: 'Retrieved passages', exact: true }),
  ).toBeVisible();
  await expect(page.getByRole('alert')).toHaveCount(0);
  await expect(page.getByText('OpenAI answers from the papers only')).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('demo-limited.png'), fullPage: true });

  // 4. A visitor key travels only as a header and is never rendered.
  const key = 'sk-test-visitor-key-0123456789abcdef';
  await page.getByText('Use your own OpenAI API key').click();
  await page.getByLabel('OpenAI API key').fill(key);
  await page.getByRole('button', { name: 'Ask the papers' }).click();
  await expect(page.getByTestId('fallback-notice')).toBeVisible();
  expect(asks.map((ask) => ask.headers['x-openai-api-key'])).toEqual([undefined, undefined, key]);
  expect(JSON.stringify(asks.map((ask) => ask.body))).not.toContain(key);
  await expect(page.locator('body')).not.toContainText(key);
  expect(await page.evaluate(() => JSON.stringify({ ...localStorage, ...sessionStorage }))).toBe(
    '{}',
  );
  expect(errors).toEqual([]);
});
