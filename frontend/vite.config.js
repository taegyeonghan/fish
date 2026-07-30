import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // 서브경로 마운트(/world-model) 대응: base 는 .env.production 의 VITE_BASE 에서 온다.
  // Vite 는 .env 파일 값을 process.env 로 노출하지 않으므로 config 에서는 loadEnv 로 읽어야 한다.
  // loadEnv 는 .env 파일 → process.env 순으로 병합하므로 쉘/CLI 지정이 여전히 우선한다.
  const env = loadEnv(mode, __dirname, 'VITE_')

  return {
    base: env.VITE_BASE || '/',
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
        '@locales': path.resolve(__dirname, '../locales')
      }
    },
    server: {
      port: 3000,
      open: true,
      proxy: {
        '/api': {
          target: 'http://localhost:5001',
          changeOrigin: true,
          secure: false
        }
      }
    }
  }
})
