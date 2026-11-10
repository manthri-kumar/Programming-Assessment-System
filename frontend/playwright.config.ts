import { defineConfig, devices } from '@playwright/test'

const systemBrowser = process.env.PW_USE_SYSTEM_CHROME === '1' ? { channel: 'chrome' as const } : {}
const webPort = Number(process.env.E2E_WEB_PORT ?? 5173)

export default defineConfig({
  testDir: './e2e',
  webServer: { command: `npm run dev -- --host 127.0.0.1 --port ${webPort}`, port: webPort, reuseExistingServer: true },
  use: { baseURL: `http://127.0.0.1:${webPort}`, trace: 'retain-on-failure', ...systemBrowser },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'tablet', use: { ...devices['iPad (gen 7)'], browserName: 'chromium' } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
})
