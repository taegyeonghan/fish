// Waiker Forecast 테마 브리지
// 메인 앱(React)에 iframe 으로 임베드될 때, 부모가 보내는 테마(dark/light/ungdroo)에 맞춰
// 셸의 --uf-* CSS 변수를 오버라이드해 색감을 메인 앱과 맞춘다.
// 단독 실행(standalone) 시에는 메시지가 오지 않으므로 원래 테마 그대로 — 기능/동작 변화 없음.

const PALETTES = {
  dark: {
    '--uf-bg': '#111827',
    '--uf-surface': '#1f2937',
    '--uf-sidebar-bg': '#0b1220',
    '--uf-sidebar-active': '#283344',
    '--uf-sidebar-text': '#9ca3af',
    '--uf-sidebar-text-active': '#f9fafb',
    '--uf-text': '#f3f4f6',
    '--uf-text-muted': '#9ca3af',
    '--uf-accent': '#6366f1',
    '--uf-accent-hover': '#4f46e5',
    '--uf-accent-soft': 'rgba(99,102,241,0.16)',
    '--uf-border': '#374151',
    '--uf-border-light': '#243040',
  },
  light: {
    '--uf-bg': '#f9fafb',
    '--uf-surface': '#ffffff',
    '--uf-sidebar-bg': '#1f2937',
    '--uf-sidebar-active': '#374151',
    '--uf-sidebar-text': '#9ca3af',
    '--uf-sidebar-text-active': '#ffffff',
    '--uf-text': '#111827',
    '--uf-text-muted': '#6b7280',
    '--uf-accent': '#6366f1',
    '--uf-accent-hover': '#4f46e5',
    '--uf-accent-soft': '#eef2ff',
    '--uf-border': '#e5e7eb',
    '--uf-border-light': '#f3f4f6',
  },
}
// ungdroo(메인 앱 파스텔)는 라이트 팔레트로 근사
PALETTES.ungdroo = PALETTES.light

// 하드코딩된 녹색(액센트 글로우 등) 보정 — 임베드 시에만 적용
function ensureOverrideStyle() {
  if (document.getElementById('waiker-embed-overrides')) return
  const el = document.createElement('style')
  el.id = 'waiker-embed-overrides'
  el.textContent = `
    html.waiker-embed .uf-step-item.uf-step-active {
      box-shadow: 0 4px 12px rgba(99,102,241,0.4) !important;
    }
  `
  document.head.appendChild(el)
}

function applyTheme(theme) {
  const palette = PALETTES[theme] || PALETTES.dark
  const root = document.documentElement
  for (const [k, v] of Object.entries(palette)) {
    root.style.setProperty(k, v)
  }
  ensureOverrideStyle()
  root.classList.add('waiker-embed')
  root.classList.remove('waiker-dark', 'waiker-light')
  root.classList.add(theme === 'light' || theme === 'ungdroo' ? 'waiker-light' : 'waiker-dark')
}

export function initThemeBridge() {
  // iframe(부모 존재) 안일 때만 동작
  if (window.parent === window) return

  window.addEventListener('message', (e) => {
    const data = e && e.data
    if (data && data.type === 'waiker-theme' && typeof data.theme === 'string') {
      applyTheme(data.theme)
    }
  })

  // 부모에게 준비 완료 알림 → 부모가 현재 테마를 회신(초기 레이스 방지)
  try {
    window.parent.postMessage({ type: 'waiker-embed-ready' }, '*')
  } catch (_) { /* noop */ }
}
