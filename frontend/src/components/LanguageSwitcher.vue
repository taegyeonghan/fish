<template>
  <div class="language-switcher" ref="switcherRef">
    <button class="switcher-trigger" @click="toggleDropdown">
      {{ currentLabel }}
      <span class="caret">{{ open ? '▲' : '▼' }}</span>
    </button>
    <ul v-if="open" class="switcher-dropdown">
      <li
        v-for="loc in availableLocales"
        :key="loc.key"
        class="switcher-option"
        :class="{ active: loc.key === locale }"
        @click="switchLocale(loc.key)"
      >
        {{ loc.label }}
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { availableLocales } from '@/i18n/index.js'

const { locale } = useI18n({ useScope: 'global' })
const open = ref(false)
const switcherRef = ref(null)

const currentLabel = computed(() => {
  const found = availableLocales.find(l => l.key === locale.value)
  return found ? found.label : locale.value
})

const toggleDropdown = () => {
  open.value = !open.value
}

const switchLocale = (key) => {
  locale.value = key
  localStorage.setItem('locale', key)
  document.documentElement.lang = key
  open.value = false
}

const onClickOutside = (e) => {
  if (switcherRef.value && !switcherRef.value.contains(e.target)) {
    open.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
  document.documentElement.lang = locale.value
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
})
</script>

<style scoped>
/* 색·형태는 --wm-* 정본 토큰만 쓴다(정의: assets/market-world.css). */
.language-switcher {
  position: relative;
  display: inline-block;
  font-family: var(--wm-mono);
}

.switcher-trigger {
  background: var(--wm-surface-2);
  color: var(--wm-text-muted);
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-sm);
  padding: 4px 12px;
  font-family: var(--wm-mono);
  font-size: 0.8rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  transition: border-color 0.2s, color 0.2s, opacity 0.2s;
}

.switcher-trigger:hover {
  border-color: var(--wm-border-strong);
  color: var(--wm-text);
}

.caret {
  font-size: 0.6rem;
}

.switcher-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: var(--wm-surface);
  color: var(--wm-text);
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-sm);
  list-style: none;
  padding: 4px 0;
  min-width: 100%;
  z-index: 1000;
  box-shadow: var(--wm-shadow-2);
}

.switcher-option {
  padding: 6px 12px;
  font-size: 0.8rem;
  color: var(--wm-text-muted);
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s, color 0.15s;
}

.switcher-option:hover {
  background: var(--wm-chrome-active);
  color: var(--wm-text);
}

/* theme-dark-overrides.css 가 임베드에서 .switcher-option 색을 !important 로 덮어
   현재 선택된 언어가 구분되지 않았다 — 같은 무게로 되돌린다. */
.switcher-option.active {
  color: var(--wm-accent-text) !important;
}

/* 워크벤치 좌측 레일(84px, ≤1180 에서 64px) 안에서는 트리거가 줄바꿈되고
   드롭다운이 레일 아래(화면 밖)로 열렸다. 레일에서는 압축 + 위로 열기. */
.uf-sidebar .language-switcher {
  max-width: 100%;
}

.uf-sidebar .switcher-trigger {
  padding: 4px 6px;
  gap: 3px;
  font-size: 0.7rem;
  letter-spacing: 0;
}

.uf-sidebar .switcher-dropdown {
  top: auto;
  right: auto;
  left: 0;
  bottom: calc(100% + 4px);
  margin-top: 0;
  min-width: max-content;
}

@media (max-width: 1180px) {
  .uf-sidebar .switcher-trigger {
    padding: 4px;
    font-size: 0.62rem;
  }

  .uf-sidebar .caret {
    display: none;
  }
}
</style>