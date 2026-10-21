import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests/browser', fullyParallel: false, workers: 1,
  use: { baseURL: 'http://127.0.0.1:4173', browserName: 'chromium', headless: true, viewport: { width: 1440, height: 1100 },
    launchOptions: process.env.WORKSPACE_CHROMIUM ? { executablePath: process.env.WORKSPACE_CHROMIUM } : {} },
  webServer: { command: 'npm run preview -- --port 4173 --strictPort', url: 'http://127.0.0.1:4173', reuseExistingServer: false },
});
