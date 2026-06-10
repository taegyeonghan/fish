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