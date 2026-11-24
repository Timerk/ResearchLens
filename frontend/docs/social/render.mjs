// Renders og-image.html to public/og-image.png. Run from frontend/: node docs/social/render.mjs
import { chromium } from '@playwright/test';
import { fileURLToPath, pathToFileURL } from 'node:url';

const source = fileURLToPath(new URL('./og-image.html', import.meta.url));
const target = fileURLToPath(new URL('../../public/og-image.png', import.meta.url));
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
await page.goto(pathToFileURL(source).href);
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: target });
await browser.close();
console.log(`Wrote ${target}`);
