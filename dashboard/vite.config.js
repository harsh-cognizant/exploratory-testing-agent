import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/scan': 'http://localhost:8000',
      '/graph': 'http://localhost:8000',
      '/queue': 'http://localhost:8000',
      '/findings': 'http://localhost:8000',
      '/memory': 'http://localhost:8000',
      '/report': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/screenshots': 'http://localhost:8000',
    }
  }
})
