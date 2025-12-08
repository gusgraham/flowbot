import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    allowedHosts: ['localhost', '127.0.0.1', '0.0.0.0', 'localhost:8001', 'ttl-5cg0279x0v', 'GLWS-150447-BMF', 'glws-150447-bmf'],
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
