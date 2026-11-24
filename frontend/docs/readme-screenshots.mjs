// Captures the README screenshots in docs/images from a running stack without an API key:
//   docker compose up -d --build --wait   (repository root; local preview, no .env needed)
//   node docs/readme-screenshots.mjs      (from frontend/)
// The answers are recorded evaluation answers replayed by the backend; nothing calls OpenAI.
import { chromium } from '@playwright/test';
import { fileURLToPath } from 'node:url';

const base = process.env['BASE_URL'] ?? 'http://127.0.0.1:4200';
const out = (name) => fileURLToPath(new URL(`../../docs/images/${name}`, import.meta.url));
const example = 'TDI stages and fixed-pattern noise in wafer inspection';
const question = 'Why combine forward and backward lighting for aircraft glass canopy inspection?';

const browser = await chromium.launch();

async function open(path, viewport, deviceScaleFactor = 1) {
  const page = await browser.newPage({ viewport, deviceScaleFactor, colorScheme: 'light' });
  await page.goto(base + path);
  await page.evaluate(() => document.fonts.ready);
  return page;
}

async function replay(page) {
  await page.getByRole('button', { name: example }).click();
  await page.getByTestId('replay-label').waitFor();
  await page.locator('.citation summary').first().click();
  await page.mouse.move(0, 0);
  // Let the disclosure chevron finish its rotation.
  await page.waitForTimeout(500);
}

/** Full-page capture cut off just below the given element. */
async function upTo(page, selector, path, margin = 32) {
  const box = await page.locator(selector).first().boundingBox();
  const width = page.viewportSize().width;
  const scrollY = await page.evaluate(() => window.scrollY);
  await page.screenshot({
    path,
    fullPage: true,
    clip: { x: 0, y: 0, width, height: Math.ceil(box.y + scrollY + box.height + margin) },
  });
}

// Desktop: the replayed answer with its first citation open.
let page = await open('/ask', { width: 1280, height: 900 });
await replay(page);
await upTo(page, '.answer-section', out('desktop-answer.png'));
await page.screenshot({ path: out('desktop-answer-full.png'), fullPage: true });
await page.close();

// Mobile (390 px at 2x): one screen of the same replay, scrolled to the answer.
page = await open('/ask', { width: 390, height: 844 }, 2);
await replay(page);
await page.evaluate(() => {
  const heading = document.querySelector('.result-heading');
  window.scrollTo(0, heading.getBoundingClientRect().top + window.scrollY - 16);
});
await page.screenshot({ path: out('mobile-answer.png') });
await page.close();

// Local preview: a typed question answered with ranked passages, no written answer.
page = await open('/ask', { width: 1280, height: 900 });
await page.getByRole('textbox', { name: 'Your research question' }).fill(question);
await page.getByRole('button', { name: 'Find passages' }).click();
await page.locator('.passage').first().waitFor();
await page.mouse.move(0, 0);
await page.waitForTimeout(500);
await upTo(page, '.passage >> nth=1', out('desktop-local-preview.png'));
await page.close();

// Landing page, first screen.
page = await open('/', { width: 1280, height: 900 });
await page.screenshot({ path: out('landing.png') });
await page.close();

await browser.close();
