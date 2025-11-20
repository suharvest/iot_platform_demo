import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    host: true, // 在 macOS 上使用 true 可以同时监听 IPv4 和 IPv6
    port: 5173,
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:9099',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://127.0.0.1:9099',
        ws: true
      },
      '/static': {
        target: 'http://127.0.0.1:9099',
        changeOrigin: true
      }
    }
  }
})
