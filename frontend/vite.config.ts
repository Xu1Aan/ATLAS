import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [vue()],
    base: env.VITE_APP_BASE || '/',
    server: {
      host: '0.0.0.0',
      port: 3666,
      proxy: {
        '/api': { target: 'http://127.0.0.1:8088', changeOrigin: true },
        '/geoserver': { target: 'http://127.0.0.1:8080', changeOrigin: true },
        '/public/dwgconvert/api': { target: 'http://127.0.0.1:8088', changeOrigin: true },
        '/public/dwgconvert/geoserver': { target: 'http://127.0.0.1:8080', changeOrigin: true },
      },
    },
  }
})
