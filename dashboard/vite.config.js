import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/scan': 'http://127.0.0.1:8000',
      '/graph': 'http://127.0.0.1:8000',
      '/queue': 'http://127.0.0.1:8000',
      '/findings': 'http://127.0.0.1:8000',
      '/memory': 'http://127.0.0.1:8000',
      '/report': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/screenshots': 'http://127.0.0.1:8000',
    }
  }
})
