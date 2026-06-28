import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],

  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true,

    // cpolar 公网模式关闭 HMR，避免 WebSocket 1006 错误
    hmr: process.env.VITE_PUBLIC_TUNNEL === '1'
      ? false
      : true,

    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8080',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api/, '')
      }
    }
  }
})