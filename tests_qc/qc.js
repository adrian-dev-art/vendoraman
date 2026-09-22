import { chromium } from 'playwright';
import fs from 'fs';

const outDir = '/root/.gemini/antigravity-ide/brain/804a9e53-8959-4eec-a6ec-5b7a28392e28';

async function runQC() {
  console.log('Starting Playwright Chromium...');
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });

  const page = await context.newPage();

  const consoleLogs = [];
  const failedRequests = [];

  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleLogs.push(`[${msg.type()}] ${msg.text()}`);
    }
  });

  page.on('requestfailed', req => {
    failedRequests.push(`${req.method()} ${req.url()} -> ${req.failure()?.errorText || 'failed'}`);
  });

  page.on('pageerror', err => {
    consoleLogs.push(`[PAGE ERROR] ${err.message}`);
  });

  const urls = [
    { url: 'https://vendoraman.vitnite.cloud/', name: 'homepage', file: `${outDir}/qc_homepage.png` },
    { url: 'https://vendoraman.vitnite.cloud/wizard/', name: 'wizard', file: `${outDir}/qc_wizard.png` },
    { url: 'https://vendoraman.vitnite.cloud/login/', name: 'login', file: `${outDir}/qc_login.png` },
    { url: 'https://vendoraman.vitnite.cloud/trust-guarantee/', name: 'trust', file: `${outDir}/qc_trust.png` }
  ];

  const results = [];

  for (const item of urls) {
    console.log(`Testing ${item.url}...`);
    try {
      const response = await page.goto(item.url, { waitUntil: 'networkidle', timeout: 30000 });
      const status = response ? response.status() : 'no response';
      const title = await page.title();
      await page.screenshot({ path: item.file, fullPage: false });
      results.push({
        name: item.name,
        url: item.url,
        status,
        title,
        screenshot: item.file,
        success: status >= 200 && status < 400
      });
      console.log(`✓ ${item.name}: Status ${status}, Title: "${title}"`);
    } catch (err) {
      console.error(`✗ Failed to load ${item.url}:`, err.message);
      results.push({
        name: item.name,
        url: item.url,
        error: err.message,
        success: false
      });
    }
  }

  await browser.close();

  console.log('\n=== QC SUMMARY ===');
  console.log(JSON.stringify({
    results,
    consoleErrors: consoleLogs,
    failedRequests
  }, null, 2));
}

runQC().catch(err => {
  console.error('Fatal Error:', err);
  process.exit(1);
});
