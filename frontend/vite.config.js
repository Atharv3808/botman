import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    target: 'esnext',
    cssMinify: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom', 'react-router-dom', 'axios'],
          'ui-icons': ['lucide-react'],
          'firebase': ['firebase/app', 'firebase/auth'],
        }
      }
    },
    chunkSizeWarningLimit: 1000,
  }
})
