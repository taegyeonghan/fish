<template>
  <router-view />
</template>

<script setup>
</script>

<style>
/* 색·형태는 전부 assets/market-world.css 의 --wm-* 토큰에서 온다.
   여기에 hex 를 새로 박지 말 것(테마 전파가 끊긴다). */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  scrollbar-color: var(--wm-border-strong) transparent;
  scrollbar-width: thin;
}

#app {
  font-family: var(--wm-font);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--wm-text);
  background-color: var(--wm-bg);
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--wm-border-strong);
  border-radius: var(--wm-radius-pill);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--wm-accent);
}

button {
  font-family: inherit;
}

a {
  color: inherit;
  text-decoration: none;
}

:focus-visible {
  outline: 2px solid var(--wm-accent);
  outline-offset: 2px;
}
</style>