import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

const devPort = Number(process.env.VITE_DEV_PORT ?? 5173)

export default defineConfig({
  plugins: [react()],
  server: { port: devPort, proxy: { '/api': { target: process.env.VITE_API_PROXY_TARGET ?? 'http://127.0.0.1:8000', changeOrigin: true, rewrite: (path) => path.replace(/^\/api/, '') } } },
  test: { environment: 'jsdom', environmentOptions: { jsdom: { url: 'http://localhost/' } }, setupFiles: './src/test/setup.ts', css: true, exclude: ['e2e/**', 'node_modules/**', 'dist/**'] },
})
