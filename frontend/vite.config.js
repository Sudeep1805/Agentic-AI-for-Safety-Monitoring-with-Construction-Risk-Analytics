import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173, strictPort: true },
  test: { environment: 'jsdom', setupFiles: './src/test-setup.js', include: ['src/**/*.test.jsx'] },
})
