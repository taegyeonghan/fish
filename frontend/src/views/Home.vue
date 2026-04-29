<template>
  <div class="home">
    <nav class="nav">
      <div class="nav-brand" @click="$router.push('/')">
        <img src="../assets/logo/ungdroo_logo.png" alt="logo" class="nav-logo" />
        <div class="nav-name">
          <span class="nav-title">UngdrooFish</span>
          <span class="nav-sub">Investment Simulation Engine</span>
        </div>
      </div>
      <div class="nav-actions">
        <LanguageSwitcher />
      </div>
    </nav>

    <main class="main">
      <section class="hero">
        <div class="hero-badge">
          <span class="pulse-dot"></span>
          <span>AI-Powered Investment Debate</span>
        </div>
        <h1 class="hero-title">
          10명의 AI 투자자와 함께<br>
          <span class="accent">시장의 미래를 시뮬레이션</span>
        </h1>
        <p class="hero-desc">
          질문을 입력하면 관련 자료를 자동으로 결합하고 가치투자자, 성장주 전문가, 매크로 전략가 등<br>
          다양한 관점의 AI 페르소나가 토론을 통해 투자 시나리오를 도출합니다.
        </p>
      </section>

      <div class="flow-indicator">
        <div class="flow-step" :class="{ done: formData.simulationRequirement.trim() }">
          <div class="flow-num">1</div>
          <div class="flow-label">요구사항 입력</div>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-step" :class="{ done: true }">
          <div class="flow-num">2</div>
          <div class="flow-label">시간 설정</div>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-step" :class="{ done: canSubmit }">
          <div class="flow-num">3</div>
          <div class="flow-label">시작</div>
        </div>
      </div>

      <section class="form-grid">
        <div class="card">
          <div class="card-head">
            <div class="card-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
              </svg>
            </div>
            <div class="card-title-group">
              <div class="card-title">시뮬레이션 요구사항</div>
              <div class="card-hint">분석하고 싶은 투자 시나리오를 자연어로 설명</div>
            </div>
          </div>

          <textarea
            v-model="formData.simulationRequirement"
            class="prompt-input"
            placeholder="예) 이란-이스라엘 전쟁이 장기화될 경우 에너지 섹터와 방산주에 미칠 영향을 분석하고, 각 투자자 페르소나의 관점에서 향후 6개월 전략을 제시해주세요."
            rows="7"
            :disabled="loading"
          ></textarea>

          <div class="prompt-footer">
            <div class="sample-chips">
              <button class="chip" @click="useSample(0)" type="button">에너지 섹터</button>
              <button class="chip" @click="useSample(1)" type="button">AI 반도체</button>
              <button class="chip" @click="useSample(2)" type="button">금리 인상</button>
            </div>
            <div class="char-count">{{ formData.simulationRequirement.length }}</div>
          </div>
        </div>
      </section>

      <!-- Simulation Time Config -->
      <section class="time-config-card">
        <div class="tc-head">
          <div class="tc-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div class="tc-title-group">
            <div class="tc-title">시뮬레이션 시간 설정</div>
            <div class="tc-hint">에이전트가 시뮬레이션할 시간 단위와 전체 예측 기간</div>
          </div>
        </div>

        <div class="tc-body">
          <div class="tc-field">
            <label class="tc-label">1 라운드 = 시간 단위</label>
            <div class="seg-group">
              <button
                v-for="opt in timeUnits"
                :key="opt.value"
                class="seg-btn"
                :class="{ active: simConfig.timeUnit === opt.value }"
                @click="simConfig.timeUnit = opt.value"
                type="button"
              >{{ opt.label }}</button>
            </div>
          </div>

          <div class="tc-field">
            <label class="tc-label">
              예측 기간 <span class="tc-label-val">{{ simConfig.forecastHorizon }} {{ currentUnitLabel }}</span>
            </label>
            <input
              type="range"
              class="tc-range"
              :min="currentRangeMin"
              :max="currentRangeMax"
              v-model.number="simConfig.forecastHorizon"
            />
            <div class="tc-range-labels">
              <span>{{ currentRangeMin }}</span>
              <span>{{ currentRangeMax }}</span>
            </div>
          </div>

          <div class="tc-summary">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            총 <strong>{{ simConfig.forecastHorizon }} 라운드</strong>의 시뮬레이션이 실행됩니다
            (예상 소요시간 약 {{ estimatedMinutes }}분)
          </div>
        </div>
      </section>

      <div class="submit-wrap">
        <button
          class="submit-btn"
          @click="startSimulation"
          :disabled="!canSubmit || loading"
        >
          <span v-if="!loading">시뮬레이션 시작하기</span>
          <span v-else>엔진 초기화 중...</span>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </button>
        <div v-if="!canSubmit" class="hint-text">
          {{ !formData.simulationRequirement.trim() ? '요구사항을 입력해주세요' : '' }}
        </div>
      </div>

      <section class="history">
        <div class="history-header">
          <h2 class="history-title">최근 시뮬레이션</h2>
          <span class="history-sub">이전에 실행한 프로젝트</span>
        </div>
        <HistoryDatabase />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import HistoryDatabase from '../components/HistoryDatabase.vue'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

const router = useRouter()

const formData = ref({ simulationRequirement: '' })
const loading = ref(false)

const simConfig = ref({
  timeUnit: 'day',
  forecastHorizon: 14
})

const timeUnits = [
  { value: 'hour', label: '시간', min: 6, max: 48, default: 24, estPerRound: 0.4 },
  { value: 'day', label: '일', min: 3, max: 60, default: 14, estPerRound: 0.6 },
  { value: 'week', label: '주', min: 2, max: 26, default: 8, estPerRound: 0.9 },
  { value: 'month', label: '개월', min: 1, max: 12, default: 6, estPerRound: 1.2 }
]

const currentUnit = computed(() => timeUnits.find(u => u.value === simConfig.value.timeUnit))
const currentUnitLabel = computed(() => currentUnit.value?.label || '')
const currentRangeMin = computed(() => currentUnit.value?.min || 1)
const currentRangeMax = computed(() => currentUnit.value?.max || 30)
const estimatedMinutes = computed(() => {
  const per = currentUnit.value?.estPerRound || 0.5
  return Math.max(1, Math.round(simConfig.value.forecastHorizon * per))
})

// Reset horizon when unit changes
import { watch } from 'vue'
watch(() => simConfig.value.timeUnit, (newVal) => {
  const unit = timeUnits.find(u => u.value === newVal)
  if (unit) simConfig.value.forecastHorizon = unit.default
})

const samples = [
  '원유 가격 급등이 에너지 섹터와 전기차 관련주에 미칠 영향을 분석하고, 각 투자자 페르소나의 관점에서 향후 3개월 전략을 제시해주세요.',
  'AI 반도체 수요 증가가 엔비디아, TSMC, SK하이닉스 등 주요 기업들에 미칠 영향과 밸류에이션 적정성을 토론해주세요.',
  '연준의 기준금리 인상이 성장주와 가치주에 미치는 차별적 영향을 분석하고, 섹터별 포지셔닝 전략을 제시해주세요.'
]

const canSubmit = computed(() => {
  return formData.value.simulationRequirement.trim() !== ''
})

const useSample = (idx) => { formData.value.simulationRequirement = samples[idx] }

const startSimulation = () => {
  if (!canSubmit.value || loading.value) return
  import('../store/pendingUpload.js').then(({ setPendingUpload }) => {
    setPendingUpload([], formData.value.simulationRequirement, {
      timeUnit: simConfig.value.timeUnit,
      forecastHorizon: simConfig.value.forecastHorizon
    })
    router.push({ name: 'Process', params: { projectId: 'new' } })
  })
}
</script>

<style scoped>
.home {
  --c-bg: #fbfaf7;
  --c-surface: #ffffff;
  --c-text: #0c1e3e;
  --c-text-muted: #64748b;
  --c-text-dim: #94a3b8;
  --c-accent: #d97706;
  --c-accent-hover: #b45309;
  --c-accent-soft: #fef3c7;
  --c-navy: #0c1e3e;
  --c-border: #e7e5e0;
  --c-border-soft: #f5f3ee;
  min-height: 100vh;
  background: var(--c-bg);
  font-family: 'Inter', 'Noto Sans KR', system-ui, sans-serif;
  color: var(--c-text);
}

.nav {
  height: 68px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  background: var(--c-surface);
  border-bottom: 1px solid var(--c-border);
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-brand { display: flex; align-items: center; gap: 12px; cursor: pointer; }
.nav-logo { width: 42px; height: 42px; border-radius: 10px; }
.nav-name { display: flex; flex-direction: column; line-height: 1.2; }
.nav-title { font-weight: 800; font-size: 17px; letter-spacing: -0.4px; color: var(--c-navy); }
.nav-sub { font-size: 11px; color: var(--c-text-muted); font-weight: 500; letter-spacing: 0.3px; }
.nav-actions { display: flex; align-items: center; gap: 12px; }

.main {
  max-width: 1080px;
  margin: 0 auto;
  padding: 56px 32px 80px;
}

.hero { text-align: center; margin-bottom: 40px; }
.hero-badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 7px 16px;
  background: var(--c-accent-soft);
  color: var(--c-accent);
  border-radius: 100px;
  font-size: 12px; font-weight: 700; letter-spacing: 0.3px;
  margin-bottom: 24px;
  border: 1px solid rgba(217, 119, 6, 0.15);
}
.pulse-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--c-accent); animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(0.8); } }

.hero-title {
  font-size: 42px; font-weight: 800; line-height: 1.25;
  letter-spacing: -1.2px; color: var(--c-navy); margin: 0 0 20px;
}
.hero-title .accent { color: var(--c-accent); }
.hero-desc {
  font-size: 16px; line-height: 1.7; color: var(--c-text-muted);
  max-width: 640px; margin: 0 auto;
}

.flow-indicator {
  display: flex; align-items: center; justify-content: center; gap: 16px;
  margin-bottom: 32px; padding: 16px;
}
.flow-step { display: flex; align-items: center; gap: 10px; opacity: 0.55; transition: opacity 0.3s; }
.flow-step.done { opacity: 1; }
.flow-num {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--c-surface); border: 2px solid var(--c-border);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: var(--c-text-muted);
  transition: all 0.3s;
}
.flow-step.done .flow-num {
  background: var(--c-navy); border-color: var(--c-navy); color: #fff;
}
.flow-label { font-size: 13px; font-weight: 600; color: var(--c-text); }
.flow-arrow { color: var(--c-text-dim); font-size: 14px; }

.form-grid {
  margin-bottom: 24px;
}

.card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: 14px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.card:hover { border-color: #d6d3cc; box-shadow: 0 4px 16px rgba(12, 30, 62, 0.04); }

.card-head { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
.card-icon {
  width: 38px; height: 38px; border-radius: 10px;
  background: var(--c-accent-soft); color: var(--c-accent);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.card-title-group { display: flex; flex-direction: column; gap: 2px; }
.card-title { font-size: 15px; font-weight: 700; color: var(--c-navy); letter-spacing: -0.2px; }
.card-hint { font-size: 12px; color: var(--c-text-muted); font-weight: 500; }

.prompt-input {
  flex: 1; width: 100%; min-height: 220px;
  padding: 14px 16px;
  background: var(--c-border-soft);
  border: 1px solid var(--c-border);
  border-radius: 8px;
  font-family: inherit; font-size: 14px; line-height: 1.6;
  color: var(--c-text); resize: none; outline: none;
  transition: all 0.2s;
}
.prompt-input::placeholder { color: var(--c-text-dim); }
.prompt-input:focus {
  background: var(--c-surface);
  border-color: var(--c-accent);
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.1);
}

.prompt-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 14px; gap: 12px; }
.sample-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.chip {
  font-size: 11px; font-weight: 600; padding: 5px 11px;
  background: var(--c-border-soft);
  border: 1px solid var(--c-border);
  border-radius: 100px;
  color: var(--c-text-muted);
  cursor: pointer; transition: all 0.15s;
  font-family: inherit;
}
.chip:hover { background: var(--c-accent-soft); border-color: var(--c-accent); color: var(--c-accent); }
.char-count { font-size: 11px; color: var(--c-text-dim); font-family: 'JetBrains Mono', monospace; flex-shrink: 0; }

/* Time Config */
.time-config-card {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: 14px;
  padding: 24px;
  margin-bottom: 24px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.time-config-card:hover { border-color: #d6d3cc; box-shadow: 0 4px 16px rgba(12, 30, 62, 0.04); }

.tc-head { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.tc-icon {
  width: 38px; height: 38px; border-radius: 10px;
  background: var(--c-accent-soft); color: var(--c-accent);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.tc-title-group { display: flex; flex-direction: column; gap: 2px; }
.tc-title { font-size: 15px; font-weight: 700; color: var(--c-navy); letter-spacing: -0.2px; }
.tc-hint { font-size: 12px; color: var(--c-text-muted); font-weight: 500; }

.tc-body { display: flex; flex-direction: column; gap: 20px; }
.tc-field { display: flex; flex-direction: column; gap: 10px; }
.tc-label {
  font-size: 13px; font-weight: 600; color: var(--c-text);
  display: flex; justify-content: space-between; align-items: center;
}
.tc-label-val {
  color: var(--c-accent); font-weight: 700;
  font-family: 'JetBrains Mono', monospace; font-size: 13px;
}

.seg-group {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px;
  background: var(--c-border-soft); padding: 4px; border-radius: 10px;
}
.seg-btn {
  padding: 9px 0; font-size: 13px; font-weight: 600;
  background: transparent; border: none; border-radius: 7px;
  color: var(--c-text-muted); cursor: pointer;
  font-family: inherit; transition: all 0.15s;
}
.seg-btn:hover:not(.active) { color: var(--c-text); }
.seg-btn.active {
  background: var(--c-surface); color: var(--c-navy);
  box-shadow: 0 1px 3px rgba(12, 30, 62, 0.08);
  font-weight: 700;
}

.tc-range {
  width: 100%; height: 6px;
  -webkit-appearance: none; appearance: none;
  background: var(--c-border); border-radius: 3px; outline: none;
  cursor: pointer;
}
.tc-range::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none;
  width: 20px; height: 20px; border-radius: 50%;
  background: var(--c-accent); cursor: pointer;
  border: 3px solid #fff; box-shadow: 0 2px 6px rgba(217, 119, 6, 0.4);
  transition: transform 0.15s;
}
.tc-range::-webkit-slider-thumb:hover { transform: scale(1.15); }
.tc-range::-moz-range-thumb {
  width: 20px; height: 20px; border-radius: 50%;
  background: var(--c-accent); cursor: pointer;
  border: 3px solid #fff; box-shadow: 0 2px 6px rgba(217, 119, 6, 0.4);
}
.tc-range-labels {
  display: flex; justify-content: space-between;
  font-size: 11px; color: var(--c-text-dim);
  font-family: 'JetBrains Mono', monospace;
}

.tc-summary {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 14px;
  background: var(--c-accent-soft);
  border: 1px solid rgba(217, 119, 6, 0.2);
  border-radius: 8px;
  font-size: 12px; color: var(--c-navy);
}
.tc-summary strong { color: var(--c-accent); font-weight: 700; }

.submit-wrap { text-align: center; margin-bottom: 64px; }
.submit-btn {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 16px 40px;
  background: var(--c-navy); color: #fff;
  border: none; border-radius: 12px;
  font-family: inherit; font-size: 15px; font-weight: 700;
  cursor: pointer; transition: all 0.2s;
  box-shadow: 0 4px 14px rgba(12, 30, 62, 0.15);
}
.submit-btn:hover:not(:disabled) {
  background: var(--c-accent);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(217, 119, 6, 0.3);
}
.submit-btn:disabled { background: var(--c-border); color: var(--c-text-dim); cursor: not-allowed; box-shadow: none; }
.hint-text { margin-top: 12px; font-size: 12px; color: var(--c-text-muted); }

.history { padding-top: 40px; border-top: 1px solid var(--c-border); }
.history-header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 20px; }
.history-title { font-size: 18px; font-weight: 700; color: var(--c-navy); margin: 0; }
.history-sub { font-size: 13px; color: var(--c-text-muted); }

@media (max-width: 900px) {
  .form-grid { grid-template-columns: 1fr; }
  .hero-title { font-size: 32px; }
  .main { padding: 40px 20px 60px; }
}
@media (max-width: 600px) {
  .nav { padding: 0 20px; }
  .nav-sub { display: none; }
  .flow-label { display: none; }
}
</style>