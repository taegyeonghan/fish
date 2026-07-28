import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import { initThemeBridge } from './theme-bridge'
import './theme-dark-overrides.css'
import './assets/market-world.css'

const app = createApp(App)

app.use(router)
app.use(i18n)

app.mount('#app')

// 메인 앱 임베드 시 테마 동기화(단독 실행이면 no-op)
initThemeBridge()

// 단독 실행 워크벤치는 금융 시뮬레이터의 다크 데이터 테마를 사용한다.
// 홈은 자체 시네마틱 테마를 가지므로 생성된 컴포넌트 오버라이드를 적용하지 않는다.
if (window.parent === window) {
  const syncWorkbenchTheme = (to) => {
    const enabled = to?.name !== 'Home'
    document.documentElement.classList.toggle('waiker-embed', enabled)
    document.documentElement.classList.toggle('waiker-dark', enabled)
  }
  router.afterEach(syncWorkbenchTheme)
  router.isReady().then(() => syncWorkbenchTheme(router.currentRoute.value))
}

// 메인 앱 임베드 시: 현재 라우트를 부모에 알려, 시뮬레이션 중 다른 데로 갔다가
// 다시 열 때 마지막 화면(진행 중 시뮬레이션 등)으로 복원하게 한다. (단독 실행이면 no-op)
if (window.parent !== window) {
  router.afterEach((to) => {
    try {
      window.parent.postMessage({ type: 'waiker-forecast-route', path: to.fullPath }, '*')
    } catch (e) { /* noop */ }
  })
}
