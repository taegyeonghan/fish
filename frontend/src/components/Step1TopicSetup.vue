<template>
  <div class="topic-setup-panel">
    <div class="scroll-container">

      <!-- Section 01: 토론 주제 입력 -->
      <div class="step-card">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">01</span>
            <span class="step-title">토론 주제 입력</span>
          </div>
        </div>
        <div class="card-content">
          <p class="api-note">투자 토론의 핵심 주제를 설정합니다</p>
          <p class="description">
            투자자들이 논의할 주제를 구체적으로 입력해주세요.
            예: "삼성전자 2026년 하반기 투자 전략", "미국 빅테크 vs 한국 반도체 비교 분석"
          </p>
          <textarea
            v-model="topic"
            class="topic-input"
            :placeholder="'예: 삼성전자 2026년 하반기 투자 전략'"
            rows="3"
          ></textarea>
        </div>
      </div>

      <!-- Section 02: 종목 선택 -->
      <div class="step-card">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">02</span>
            <span class="step-title">종목 선택</span>
          </div>
          <div class="step-status">
            <span class="badge" :class="tickers.length > 0 ? 'success' : 'pending'">
              {{ tickers.length }}개 종목
            </span>
          </div>
        </div>
        <div class="card-content">
          <p class="api-note">토론에 포함할 종목 티커를 추가합니다</p>
          <p class="description">
            종목 티커를 입력하고 Enter 또는 추가 버튼을 눌러주세요.
            한국 종목은 "005930.KS", 미국 종목은 "AAPL" 형식을 사용합니다.
          </p>
          <div class="ticker-input-row">
            <input
              v-model="tickerInput"
              class="ticker-input"
              placeholder="종목 티커 입력 (예: 005930.KS, AAPL)"
              @keydown.enter.prevent="addTicker"
            />
            <button class="add-btn" @click="addTicker" :disabled="!tickerInput.trim()">추가</button>
          </div>
          <div v-if="tickers.length" class="chips-container">
            <span
              v-for="(ticker, idx) in tickers"
              :key="idx"
              class="chip"
            >
              {{ ticker }}
              <button class="chip-remove" @click="removeTicker(idx)">&times;</button>
            </span>
          </div>
        </div>
      </div>

      <!-- Section 03: 투자자 페르소나 선택 -->
      <div class="step-card">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">03</span>
            <span class="step-title">투자자 페르소나 선택</span>
          </div>
          <div class="step-status">
            <span class="badge" :class="selectedPersonaIds.length >= 4 && selectedPersonaIds.length <= 8 ? 'success' : selectedPersonaIds.length > 0 ? 'processing' : 'pending'">
              {{ selectedPersonaIds.length }}명 선택
            </span>
          </div>
        </div>
        <div class="card-content">
          <p class="api-note">GET /api/invest/personas</p>
          <p class="description">
            토론에 참여할 투자자 페르소나를 4~8명 선택해주세요.
            각 페르소나는 고유한 투자 성향과 전략을 가지고 있습니다.
          </p>

          <div class="persona-actions">
            <button
              class="recommend-btn"
              @click="recommendPersonas"
              :disabled="!topic.trim() || recommending"
            >
              <span v-if="recommending" class="spinner-sm"></span>
              {{ recommending ? '추천 중...' : '주제 기반 추천 받기' }}
            </button>
            <span class="persona-hint" v-if="selectedPersonaIds.length > 0 && (selectedPersonaIds.length < 4 || selectedPersonaIds.length > 8)">
              {{ selectedPersonaIds.length < 4 ? `최소 4명을 선택해주세요 (현재 ${selectedPersonaIds.length}명)` : `최대 8명까지 선택 가능합니다 (현재 ${selectedPersonaIds.length}명)` }}
            </span>
          </div>

          <!-- Loading -->
          <div v-if="loadingPersonas" class="progress-section">
            <div class="spinner-sm"></div>
            <span>페르소나 목록을 불러오는 중...</span>
          </div>

          <!-- Error -->
          <div v-if="personaError" class="error-msg">
            {{ personaError }}
            <button class="retry-link" @click="fetchPersonas">다시 시도</button>
          </div>

          <!-- Persona Cards Grid -->
          <div v-if="personas.length" class="persona-grid">
            <div
              v-for="persona in personas"
              :key="persona.id"
              class="persona-card"
              :class="{ selected: selectedPersonaIds.includes(persona.id) }"
              @click="togglePersona(persona.id)"
            >
              <div class="persona-card-header">
                <span class="persona-name">{{ persona.name_ko || persona.name }}</span>
                <span class="persona-check" v-if="selectedPersonaIds.includes(persona.id)">&#10003;</span>
              </div>
              <div class="persona-type">{{ persona.type_ko || persona.type }}</div>
              <div class="persona-risk">
                위험 성향: <span class="risk-value">{{ persona.risk_tolerance }}</span>
              </div>
              <div class="persona-bio">{{ persona.bio }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Section 04: 시작 -->
      <div class="step-card">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">04</span>
            <span class="step-title">토론 준비</span>
          </div>
        </div>
        <div class="card-content">
          <p class="description">
            모든 설정이 완료되면 토론 준비를 시작합니다.
            투자자들이 주제에 대해 사전 조사를 수행하고 토론 환경을 구성합니다.
          </p>

          <!-- Summary -->
          <div class="setup-summary">
            <div class="summary-row">
              <span class="summary-label">주제</span>
              <span class="summary-value">{{ topic || '미설정' }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">종목</span>
              <span class="summary-value">{{ tickers.length > 0 ? tickers.join(', ') : '미설정' }}</span>
            </div>
            <div class="summary-row">
              <span class="summary-label">참여 인원</span>
              <span class="summary-value">{{ selectedPersonaIds.length }}명</span>
            </div>
          </div>

          <button
            class="action-btn"
            :disabled="!canStart"
            @click="handleStart"
          >
            토론 준비 시작 &#10132;
          </button>
          <p v-if="!canStart" class="validation-msg">
            {{ validationMessage }}
          </p>
        </div>
      </div>
    </div>

    <!-- Bottom System Log -->
    <div class="system-logs">
      <div class="log-header">
        <span class="log-title">SYSTEM DASHBOARD</span>
        <span class="log-id">UngdrooFish v1.0</span>
      </div>
      <div class="log-content" ref="logContent">
        <div class="log-line" v-for="(log, idx) in systemLogs" :key="idx">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-msg">{{ log.msg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import api from '../api/index'

// ---- Emits ----
const emit = defineEmits(['start-preparation'])

// ---- Props ----
const props = defineProps({
  systemLogs: { type: Array, default: () => [] }
})

// ---- Refs ----
const logContent = ref(null)

// Topic
const topic = ref('')

// Tickers
const tickerInput = ref('')
const tickers = ref([])

// Personas
const personas = ref([])
const selectedPersonaIds = ref([])
const loadingPersonas = ref(false)
const personaError = ref('')
const recommending = ref(false)

// ---- Ticker Methods ----
const addTicker = () => {
  const val = tickerInput.value.trim().toUpperCase()
  if (!val) return
  if (tickers.value.includes(val)) {
    tickerInput.value = ''
    return
  }
  tickers.value.push(val)
  tickerInput.value = ''
}

const removeTicker = (idx) => {
  tickers.value.splice(idx, 1)
}

// ---- Persona Methods ----
const fetchPersonas = async () => {
  loadingPersonas.value = true
  personaError.value = ''
  try {
    const res = await api.get('/api/invest/personas')
    const data = res.data || res
    personas.value = Array.isArray(data) ? data : (data.personas || [])
  } catch (err) {
    console.error('Failed to fetch personas:', err)
    personaError.value = '페르소나 목록을 불러오지 못했습니다: ' + (err.message || '알 수 없는 오류')
  } finally {
    loadingPersonas.value = false
  }
}

const togglePersona = (id) => {
  const idx = selectedPersonaIds.value.indexOf(id)
  if (idx >= 0) {
    selectedPersonaIds.value.splice(idx, 1)
  } else {
    if (selectedPersonaIds.value.length >= 8) return
    selectedPersonaIds.value.push(id)
  }
}

const recommendPersonas = async () => {
  if (!topic.value.trim()) return
  recommending.value = true
  try {
    const res = await api.post('/api/invest/personas/recommend', {
      topic: topic.value.trim()
    })
    const data = res.data || res
    const ids = data.persona_ids || data.recommended_ids || []
    if (ids.length) {
      selectedPersonaIds.value = [...ids]
    }
  } catch (err) {
    console.error('Failed to get persona recommendations:', err)
  } finally {
    recommending.value = false
  }
}

// ---- Validation ----
const canStart = computed(() => {
  return (
    topic.value.trim().length > 0 &&
    tickers.value.length > 0 &&
    selectedPersonaIds.value.length >= 4 &&
    selectedPersonaIds.value.length <= 8
  )
})

const validationMessage = computed(() => {
  const issues = []
  if (!topic.value.trim()) issues.push('토론 주제를 입력해주세요')
  if (tickers.value.length === 0) issues.push('종목을 최소 1개 추가해주세요')
  if (selectedPersonaIds.value.length < 4) issues.push('페르소나를 최소 4명 선택해주세요')
  if (selectedPersonaIds.value.length > 8) issues.push('페르소나는 최대 8명까지 선택 가능합니다')
  return issues.join(' / ')
})

// ---- Start ----
const handleStart = () => {
  if (!canStart.value) return
  emit('start-preparation', {
    topic: topic.value.trim(),
    tickers: [...tickers.value],
    persona_ids: [...selectedPersonaIds.value]
  })
}

// ---- Lifecycle ----
onMounted(() => {
  fetchPersonas()
})

// Auto-scroll logs
watch(() => props.systemLogs.length, () => {
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
})
</script>

<style scoped>
/* =============================================
   Dark theme with green accents
   ============================================= */

.topic-setup-panel {
  height: 100%;
  background-color: #0a0a0a;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  color: #e0e0e0;
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.scroll-container::-webkit-scrollbar {
  width: 6px;
}

.scroll-container::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 3px;
}

/* ---- Step Card ---- */
.step-card {
  background: #111;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #222;
  transition: all 0.3s ease;
}

.step-card:hover {
  border-color: #2e7d32;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.step-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 20px;
  font-weight: 700;
  color: #4caf50;
}

.step-title {
  font-weight: 600;
  font-size: 14px;
  letter-spacing: 0.5px;
  color: #e0e0e0;
}

/* ---- Badges ---- */
.badge {
  font-size: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: uppercase;
  font-family: 'JetBrains Mono', monospace;
}

.badge.success { background: #1b5e20; color: #a5d6a7; }
.badge.processing { background: #4caf50; color: #fff; }
.badge.pending { background: #1a1a1a; color: #666; }

/* ---- Card Content ---- */
.api-note {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #4caf50;
  margin-bottom: 8px;
}

.description {
  font-size: 12px;
  color: #888;
  line-height: 1.6;
  margin-bottom: 16px;
}

/* ---- Topic Input ---- */
.topic-input {
  width: 100%;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #e0e0e0;
  font-size: 13px;
  font-family: 'JetBrains Mono', monospace;
  padding: 12px;
  resize: vertical;
  line-height: 1.5;
  box-sizing: border-box;
}

.topic-input:focus {
  outline: none;
  border-color: #4caf50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.15);
}

.topic-input::placeholder {
  color: #555;
}

/* ---- Ticker Input ---- */
.ticker-input-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.ticker-input {
  flex: 1;
  background: #0a0a0a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #e0e0e0;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  padding: 10px 12px;
}

.ticker-input:focus {
  outline: none;
  border-color: #4caf50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.15);
}

.ticker-input::placeholder {
  color: #555;
}

.add-btn {
  background: #1b5e20;
  color: #a5d6a7;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.add-btn:hover:not(:disabled) {
  background: #2e7d32;
}

.add-btn:disabled {
  background: #1a1a1a;
  color: #555;
  cursor: not-allowed;
}

/* ---- Chips ---- */
.chips-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #1a2e1a;
  border: 1px solid #2e7d32;
  color: #a5d6a7;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
}

.chip-remove {
  background: none;
  border: none;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
}

.chip-remove:hover {
  color: #ef5350;
}

/* ---- Persona Actions ---- */
.persona-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.recommend-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #0a0a0a;
  border: 1px solid #4caf50;
  color: #4caf50;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.recommend-btn:hover:not(:disabled) {
  background: #1b5e20;
  color: #a5d6a7;
}

.recommend-btn:disabled {
  border-color: #333;
  color: #555;
  cursor: not-allowed;
}

.persona-hint {
  font-size: 11px;
  color: #ff9800;
  font-family: 'JetBrains Mono', monospace;
}

/* ---- Loading / Error ---- */
.progress-section {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #4caf50;
  margin-bottom: 12px;
}

.spinner-sm {
  width: 14px;
  height: 14px;
  border: 2px solid #1b5e20;
  border-top-color: #4caf50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

.error-msg {
  font-size: 12px;
  color: #ef5350;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.retry-link {
  background: none;
  border: none;
  color: #4caf50;
  text-decoration: underline;
  cursor: pointer;
  font-size: 12px;
}

/* ---- Persona Grid ---- */
.persona-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.persona-card {
  background: #0a0a0a;
  border: 1px solid #222;
  border-radius: 6px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.persona-card:hover {
  border-color: #4caf50;
}

.persona-card.selected {
  border-color: #4caf50;
  background: #0d1f0d;
  box-shadow: 0 0 0 1px #4caf50;
}

.persona-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.persona-name {
  font-size: 13px;
  font-weight: 700;
  color: #e0e0e0;
}

.persona-check {
  color: #4caf50;
  font-size: 14px;
  font-weight: 700;
}

.persona-type {
  font-size: 10px;
  color: #4caf50;
  font-family: 'JetBrains Mono', monospace;
  text-transform: uppercase;
  margin-bottom: 6px;
}

.persona-risk {
  font-size: 10px;
  color: #888;
  margin-bottom: 8px;
}

.risk-value {
  color: #ff9800;
  font-weight: 600;
}

.persona-bio {
  font-size: 11px;
  color: #666;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ---- Setup Summary ---- */
.setup-summary {
  background: #0a0a0a;
  border: 1px solid #222;
  border-radius: 6px;
  padding: 14px;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-row {
  display: flex;
  gap: 12px;
  font-size: 12px;
  align-items: baseline;
}

.summary-label {
  font-family: 'JetBrains Mono', monospace;
  color: #4caf50;
  font-weight: 600;
  min-width: 70px;
  font-size: 10px;
  text-transform: uppercase;
}

.summary-value {
  color: #ccc;
  font-family: 'JetBrains Mono', monospace;
  word-break: break-all;
}

/* ---- Action Button ---- */
.action-btn {
  width: 100%;
  background: #2e7d32;
  color: #fff;
  border: none;
  padding: 14px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s;
  letter-spacing: 0.5px;
}

.action-btn:hover:not(:disabled) {
  background: #388e3c;
}

.action-btn:disabled {
  background: #1a1a1a;
  color: #555;
  cursor: not-allowed;
}

.validation-msg {
  font-size: 11px;
  color: #ff9800;
  margin-top: 8px;
  text-align: center;
  font-family: 'JetBrains Mono', monospace;
}

/* ---- System Logs (bottom bar) ---- */
.system-logs {
  background: #000;
  color: #ddd;
  padding: 16px;
  font-family: 'JetBrains Mono', monospace;
  border-top: 1px solid #1b5e20;
  flex-shrink: 0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid #222;
  padding-bottom: 8px;
  margin-bottom: 8px;
  font-size: 10px;
  color: #4caf50;
}

.log-title {
  color: #4caf50;
}

.log-id {
  color: #666;
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 80px;
  overflow-y: auto;
  padding-right: 4px;
}

.log-content::-webkit-scrollbar {
  width: 4px;
}

.log-content::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 2px;
}

.log-line {
  font-size: 11px;
  display: flex;
  gap: 12px;
  line-height: 1.5;
}

.log-time {
  color: #555;
  min-width: 75px;
}

.log-msg {
  color: #888;
  word-break: break-all;
}
</style>