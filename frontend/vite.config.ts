import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// The app derives its API and WebSocket URLs from the page's own origin, because
// one Render service serves both in production (docs/adr/0007). The dev server
// therefore has to stand in for that service and forward both to the backend,
// or the live counter gets no state messages and never advances.
const backend = process.env.PUSHFORM_BACKEND ?? 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: backend, changeOrigin: true },
      '/ws': { target: backend, changeOrigin: true, ws: true },
    },
  },
  test: {
    environment: 'jsdom',
    globals: false,
    setupFiles: ['./src/test-setup.ts'],
  },
})
