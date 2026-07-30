// World Model 테마 브리지
//
// 메인 앱(React)에 iframe 으로 임베드될 때, 부모가 postMessage 로 보내는
// 테마(dark/light/ungdroo)에 맞춰 --wm-* 의미 토큰 전체를 documentElement 에
// 인라인으로 쓴다. **이것이 부모 테마 전파의 유일한 경로다.**
//   · 토큰 정본 정의/문서: src/assets/market-world.css
//   · --uf-* / --c-* 는 market-world.css 에서 --wm-* 를 재노출하는 별칭이라
//     여기서 따로 쓰지 않아도 셸·Home 까지 함께 따라온다.
//   · 새 색을 추가할 때는 market-world.css 의 :root(dark) + waiker-light +
//     waiker-ungdroo, 그리고 이 파일의 3 팔레트에 같이 넣어야 한다.
//
// 단독 실행(standalone)에서는 메시지가 오지 않으므로 market-world.css 의
// :root(dark) 값이 그대로 쓰인다 — 기능/동작 변화 없음.
//
// 기준값은 메인 앱과 맞춘다:
//   dark  bg #070a08 · text #f3f4f6      (contexts/ThemeContext.tsx)
//   light bg #f9fafb · text #111827      (contexts/ThemeContext.tsx)
//   accent #1fcb6e / #05ad59             (index.css --waiker-accent, Sidebar.tsx)

const DARK = {
  '--wm-bg': '#070a08',
  '--wm-surface': '#0d120f',
  '--wm-surface-2': '#131a16',
  '--wm-surface-3': '#1b241e',
  '--wm-stage': '#040705',
  '--wm-chrome': '#050806',
  '--wm-chrome-active': '#13201a',

  '--wm-border': '#232e28',
  '--wm-border-soft': '#161d19',
  '--wm-border-strong': '#37483f',

  '--wm-text': '#f3f4f6',
  '--wm-text-muted': '#93a79c',
  '--wm-text-dim': '#7d8f85',
  '--wm-on-accent': '#04150c',

  '--wm-accent': '#1fcb6e',
  '--wm-accent-hover': '#34d399',
  '--wm-accent-soft': 'rgba(31,203,110,0.14)',
  '--wm-accent-border': 'rgba(31,203,110,0.42)',
  // 강조색을 글자·아이콘 색으로 쓸 때 전용(다크는 --wm-accent 와 같은 값)
  '--wm-accent-text': '#1fcb6e',

  '--wm-alt': '#a78bfa',
  '--wm-alt-soft': 'rgba(167,139,250,0.16)',

  '--wm-pos': '#2ee27f',
  '--wm-pos-soft': 'rgba(46,226,127,0.14)',
  '--wm-neg': '#ff6b6b',
  '--wm-neg-soft': 'rgba(255,107,107,0.14)',
  '--wm-warn': '#fbbf24',
  '--wm-warn-soft': 'rgba(251,191,36,0.14)',
  '--wm-info': '#38bdf8',
  '--wm-info-soft': 'rgba(56,189,248,0.14)',

  '--wm-overlay': 'rgba(2,6,4,0.82)',
  '--wm-scrim': 'rgba(5,8,6,0.72)',
  '--wm-shadow-1': '0 1px 2px rgba(0,0,0,0.5)',
  '--wm-shadow-2': '0 10px 30px rgba(0,0,0,0.42)',
  '--wm-shadow-3': '0 28px 80px rgba(0,0,0,0.6)',
  '--wm-glow': '0 0 0 1px rgba(31,203,110,0.35), 0 0 26px rgba(31,203,110,0.18)',

  '--wm-grid': 'rgba(120,152,138,0.08)',
  '--wm-edge': '#3d4f47',
  '--wm-edge-strong': '#1fcb6e',
  '--wm-node-stroke': '#040705',

  '--wm-cat-1': '#4ecdc4',
  '--wm-cat-2': '#ff8a5b',
  '--wm-cat-3': '#a78bfa',
  '--wm-cat-4': '#38bdf8',
  '--wm-cat-5': '#fbbf24',
  '--wm-cat-6': '#f472b6',
  '--wm-cat-7': '#84cc16',
  '--wm-cat-8': '#fb923c',
  '--wm-cat-9': '#22d3ee',
  '--wm-cat-10': '#c084fc',

  '--wm-logo-filter': 'grayscale(1) contrast(1.2) brightness(1.7)',
  'color-scheme': 'dark',
}

const LIGHT = {
  '--wm-bg': '#f9fafb',
  '--wm-surface': '#ffffff',
  '--wm-surface-2': '#f2f5f3',
  '--wm-surface-3': '#e8ece9',
  '--wm-stage': '#fcfdfc',
  '--wm-chrome': '#ffffff',
  '--wm-chrome-active': '#eaf4ee',

  '--wm-border': '#dfe5e1',
  '--wm-border-soft': '#eef1ef',
  '--wm-border-strong': '#b8c5bd',

  '--wm-text': '#111827',
  '--wm-text-muted': '#556158',
  '--wm-text-dim': '#5f6c65',
  '--wm-on-accent': '#ffffff',

  '--wm-accent': '#05ad59',
  '--wm-accent-hover': '#048a47',
  '--wm-accent-soft': 'rgba(5,173,89,0.10)',
  '--wm-accent-border': 'rgba(5,173,89,0.38)',
  // 라이트 강조(#05ad59)는 흰 배경 대비 2.95:1 이라 글자색으로 쓸 수 없다 → 별도 값
  '--wm-accent-text': '#0a7a41',

  '--wm-alt': '#7c3aed',
  '--wm-alt-soft': 'rgba(124,58,237,0.10)',

  '--wm-pos': '#08a35a',
  '--wm-pos-soft': 'rgba(8,163,90,0.10)',
  '--wm-neg': '#d92d20',
  '--wm-neg-soft': 'rgba(217,45,32,0.10)',
  '--wm-warn': '#b45309',
  '--wm-warn-soft': 'rgba(180,83,9,0.10)',
  '--wm-info': '#0369a1',
  '--wm-info-soft': 'rgba(3,105,161,0.10)',

  '--wm-overlay': 'rgba(15,25,20,0.42)',
  '--wm-scrim': 'rgba(255,255,255,0.86)',
  '--wm-shadow-1': '0 1px 2px rgba(15,25,20,0.06)',
  '--wm-shadow-2': '0 8px 24px rgba(15,25,20,0.08)',
  '--wm-shadow-3': '0 24px 64px rgba(15,25,20,0.16)',
  '--wm-glow': '0 0 0 1px rgba(5,173,89,0.28), 0 6px 20px rgba(5,173,89,0.16)',

  '--wm-grid': 'rgba(13,26,19,0.06)',
  '--wm-edge': '#b6c4bc',
  '--wm-edge-strong': '#05ad59',
  '--wm-node-stroke': '#ffffff',

  '--wm-cat-1': '#0d9488',
  '--wm-cat-2': '#ea580c',
  '--wm-cat-3': '#7c3aed',
  '--wm-cat-4': '#0369a1',
  '--wm-cat-5': '#b45309',
  '--wm-cat-6': '#be185d',
  '--wm-cat-7': '#4d7c0f',
  '--wm-cat-8': '#c2410c',
  '--wm-cat-9': '#0e7490',
  '--wm-cat-10': '#7e22ce',

  '--wm-logo-filter': 'grayscale(1) contrast(1.05) brightness(0.35)',
  'color-scheme': 'light',
}

const PALETTES = {
  dark: DARK,
  light: LIGHT,
  // ungdroo 는 light 로 근사한다. 메인 앱 ThemeContext 의 Theme 타입은 현재
  // 'dark' | 'light' 뿐이라 실제로 전달되지 않는 레거시 값이다(확인 필요 시 ThemeContext.tsx).
  ungdroo: LIGHT,
}

const THEME_CLASSES = ['waiker-dark', 'waiker-light', 'waiker-ungdroo']

function applyTheme(theme) {
  const key = PALETTES[theme] ? theme : 'dark'
  const palette = PALETTES[key]
  const root = document.documentElement

  // 이전 테마의 잔여 인라인 값 제거 후 재적용(팔레트 간 키 차이 방어)
  for (const other of Object.values(PALETTES)) {
    for (const k of Object.keys(other)) {
      if (!(k in palette)) root.style.removeProperty(k)
    }
  }
  for (const [k, v] of Object.entries(palette)) {
    root.style.setProperty(k, v)
  }

  root.classList.add('waiker-embed')
  root.classList.remove(...THEME_CLASSES)
  // 라이트 계열은 waiker-light 도 함께 붙여 기존 선택자(main.js·컴포넌트) 호환 유지
  root.classList.add(key === 'dark' ? 'waiker-dark' : 'waiker-light')
  if (key === 'ungdroo') root.classList.add('waiker-ungdroo')
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
