import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { initThemeBridge } from './theme-bridge'
import './theme-dark-overrides.css'

const app = createApp(App)

app.use(router)
app.use(i18n)

app.mount('#app')

// 메인 앱 임베드 시 테마 동기화(단독 실행이면 no-op)
initThemeBridge()

// 메인 앱 임베드 시: 현재 라우트를 부모에 알려, 시뮬레이션 중 다른 데로 갔다가
// 다시 열 때 마지막 화면(진행 중 시뮬레이션 등)으로 복원하게 한다. (단독 실행이면 no-op)
if (window.parent !== window) {
  router.afterEach((to) => {
    try {
      window.parent.postMessage({ type: 'waiker-forecast-route', path: to.fullPath }, '*')
    } catch (e) { /* noop */ }
  })
}