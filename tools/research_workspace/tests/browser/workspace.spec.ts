import { test, expect } from '@playwright/test';
import { dimensionNames, metricNames } from '../../src/contracts';

test.beforeEach(async ({ page }) => {
  page.on('pageerror', error => { throw error; });
});

test('reading desk uses actual records, global search, exact provenance and safe source rendering', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  const outbound: string[] = []; page.on('request', r => { if (!r.url().startsWith('http://127.0.0.1:4173/')) outbound.push(r.url()); });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Your research/ })).toBeVisible();
  await expect(page.getByLabel('Snapshot contents')).toContainText('39');
  await page.screenshot({ path: 'screenshots/desk.png', fullPage: true });
  await page.getByRole('button', { name: 'Find something' }).click();
  await page.getByRole('textbox', { name: 'Search all research' }).fill('F19');
  await expect(page.getByRole('dialog')).toContainText(/guaranty/i);
  await page.getByRole('button', { name: 'Close search' }).click();
  await page.getByRole('button', { name: 'Open the notebook' }).click();
  await expect(page.getByRole('heading', { name: /guaranty/i }).first()).toBeVisible();
  await page.getByRole('tab', { name: /Evidence & gaps/ }).click();
  const source = page.getByRole('tabpanel').getByRole('button', { name: /Read source|report/ }).first();
  await source.click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.locator('mark')).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Find in source document' })).not.toBeEmpty();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
  expect(errors).toEqual([]); expect(outbound).toEqual([]);
});

test('graph bounds, filters, selected-node inspection and first unsupported inference', async ({ page }) => {
  await page.goto('/#connections');
  await expect(page.getByRole('heading', { name: 'See how things connect.' })).toBeVisible();
  await expect(page.locator('.graph-node')).toHaveCount(8);
  await page.getByLabel('Neighbourhood').selectOption('16');
  expect(await page.locator('.graph-node').count()).toBeLessThanOrEqual(16);
  await page.getByRole('button', { name: /^Explain .* connection$/ }).first().click();
  await expect(page.getByText('FIRST UNSUPPORTED ECONOMIC INFERENCE')).toBeVisible();
  await expect(page.locator('.explanation')).toContainText(/connectivity|assertion/i);
  await page.screenshot({ path: 'screenshots/connections.png', fullPage: true });
  await page.getByLabel('Verified assertions only').check();
  await expect(page.getByRole('heading', { name: 'No assertions meet these filters' })).toBeVisible();
  await page.getByLabel('Verified assertions only').uncheck();
  await page.getByLabel('Records', { exact: true }).selectOption('live');
  await expect(page.getByRole('heading', { name: 'No live campaigns in this snapshot' })).toBeVisible();
  await page.getByLabel('Records', { exact: true }).selectOption('synthetic');
  await expect(page.getByRole('heading', { name: 'No synthetic records included' })).toBeVisible();
});

test('claim reformulations, source limits and shared measurement memory preserve boundaries', async ({ page }) => {
  await page.goto('/#investigations/HIST-EF06');
  await page.getByRole('tab', { name: /Claim history/ }).click();
  await expect(page.locator('.claim-timeline > article')).toHaveCount(2);
  await expect(page.locator('.claim-timeline')).toContainText('Counts as original: no');
  await page.keyboard.press('ArrowLeft');
  await expect(page.getByRole('tab', { name: /Evidence & gaps/ })).toHaveAttribute('aria-selected', 'true');
  await page.keyboard.press('ArrowRight');
  await expect(page.getByRole('tab', { name: /Claim history/ })).toHaveAttribute('aria-selected', 'true');
  await page.screenshot({ path: 'screenshots/claim-history.png', fullPage: true });
  await page.goto('/#memory/REQ_ENTITY_COHORT_JOIN');
  await expect(page.locator('.memory-detail')).toContainText('Curated retrieval match');
  await page.getByRole('tab', { name: 'Source limitations' }).click();
  await page.getByRole('textbox', { name: 'Search source limitations' }).fill('prefix');
  await expect(page.locator('.source-limit-result').first()).toBeVisible();
  await page.getByRole('tab', { name: 'What has changed?' }).click();
  await expect(page.getByRole('heading', { name: 'No recorded changes or conflicts' })).toBeVisible();
});

test('pilot defaults empty; import is explicit, constrained, and safe against HTML', async ({ page }) => {
  await page.goto('/#pilot');
  await expect(page.getByRole('heading', { name: 'No completed pilot report loaded' })).toBeVisible();
  await expect(page.getByLabel('Import completed pilot report')).toBeDisabled();
  await page.getByRole('checkbox').check();
  await page.getByLabel('Import completed pilot report').setInputFiles({ name: 'active.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify({ scope: 'ACTIVE', blind_key: 'forbidden' })) });
  await expect(page.getByRole('alert')).toContainText('not a completed');
  await expect(page.locator('script:not([src])')).toHaveCount(0);
  const arm = () => ({ campaign: 'SOFTWARE_TEST_ONLY', ...Object.fromEntries(metricNames.map(n => [n, null])),
    decisive_falsification: { 'CLAIM-TEST': 'UNKNOWN' }, graph_suggestions_false_or_trivial: [0, 0],
    budget_violations: [{ code: 'OVER_CAMPAIGN_CEILING', field: 'source_starts', used: 7, ceiling: 6 }] });
  const report = { schema: 'WORKSPACE_COMPLETED_PILOT_V1', lifecycle: 'COMPLETED_UNSEALED',
    authorisation: { path: 'docs/strategy/owner_test_only.md', sha256: 'a'.repeat(64) }, source_report_sha256: 'b'.repeat(64),
    report: { banner: 'DERIVED RESEARCH VIEW - NOT INDEPENDENT EVIDENCE - NO RESEARCH AUTHORITY', scope: 'PILOT_PAIRED_REPORT',
      classification: 'INCONCLUSIVE', notes: ['<img src="https://example.invalid/" onerror="alert(1)">'],
      packets: [{ packet: 'SOFTWARE_TEST_ONLY', method: 'SOFTWARE_TEST_ONLY', S: arm(), G: arm(),
        directions: Object.fromEntries(dimensionNames.map(n => [n, 'NOT_COMPARABLE'])) }] } };
  await page.getByLabel('Import completed pilot report').setInputFiles({ name: 'completed-test.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(report)) });
  await expect(page.getByRole('heading', { name: 'Inconclusive' })).toBeVisible();
  await expect(page.locator('td').first()).toHaveText('Unknown');
  await expect(page.locator('table')).toContainText('Over campaign ceiling · Source starts: 7 / 6');
  await expect(page.locator('img')).toHaveCount(0);
  await page.getByRole('button', { name: 'Remove report from this tab' }).click();
  await expect(page.getByRole('heading', { name: 'No completed pilot report loaded' })).toBeVisible();
});

test('mobile navigation, evening theme, no horizontal document overflow and keyboard search', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Your research/ })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'screenshots/mobile.png', fullPage: true });
  await page.getByRole('button', { name: 'A softer evening view' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  const rootColor = await page.evaluate(() => getComputedStyle(document.documentElement).color);
  await expect(page.locator('.row-body strong').first()).toHaveCSS('color', rootColor);
  await page.screenshot({ path: 'screenshots/evening.png', fullPage: true });
  await page.getByRole('link', { name: 'Investigations' }).click();
  await expect(page.getByRole('heading', { name: 'Follow a question.' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.keyboard.press('Control+k');
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).not.toBeVisible();
});
