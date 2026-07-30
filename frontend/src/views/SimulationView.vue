<template>
  <!-- /simulation = 세계 객체 설정 화면 → 덱 우위(uf-shell--deck-lead), 스테이지는 검증용 참조 -->
  <div
    class="uf-shell uf-shell--deck-lead"
    :class="{ 'graph-fullscreen': drawerMode === 'full' }"
    :style="{ '--wm-progress': stepProgressRatio }"
  >
    <!-- Left Sidebar -->
    <aside class="uf-sidebar">
      <img src="../assets/logo/ungdroo_logo.png" alt="logo" class="uf-sidebar-logo" @click="router.push('/')" />
      <div class="uf-sidebar-divider"></div>

      <nav class="uf-steps-vertical">
        <div
          v-for="(name, idx) in $tm('main.stepNames')"
          :key="idx"
          class="uf-step-item"
          :class="{
            'uf-step-active': 2 === idx + 1,
            'uf-step-completed': 2 > idx + 1,
            'uf-step-disabled': 2 < idx + 1
          }"
          :data-label="name"
        >
          {{ String(idx + 1).padStart(2, '0') }}
        </div>
      </nav>

      <div class="uf-sidebar-footer">
        <LanguageSwitcher />
      </div>
    </aside>

    <!-- Main Area -->
    <main class="uf-main">
      <div class="uf-subheader">
        <div class="uf-subheader-left">
          <span class="uf-crumb">World Model</span>
          <span class="uf-crumb-arrow">▸</span>
          <span class="uf-crumb">Step 2</span>
          <span class="uf-crumb-arrow">▸</span>
          <span class="uf-crumb-current">{{ $tm('main.stepNames')[1] }}</span>
        </div>
        <div class="uf-subheader-right">
          <span class="uf-status" :class="statusClass">
            <span class="uf-status-dot"></span>
            {{ statusText }}
          </span>
          <button class="uf-toggle-graph" :class="{ active: drawerMode !== 'hidden' }" @click="toggleDrawer">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <circle cx="6" cy="6" r="2"/><circle cx="18" cy="6" r="2"/>
              <circle cx="6" cy="18" r="2"/><circle cx="18" cy="18" r="2"/>
              <line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="18" x2="16" y2="18"/>
              <line x1="6" y1="8" x2="6" y2="16"/><line x1="18" y1="8" x2="18" y2="16"/>
            </svg>
            Knowledge Graph
          </button>
        </div>
      </div>

      <div class="uf-content-wrap">
        <div class="uf-content">
          <!-- 상태 배너: 시뮬레이션 미존재 등 실패 시 원인(마지막 시스템 메시지)과 복귀 경로를 덱 상단에 둔다 -->
          <div v-if="currentStatus === 'error' && bannerText" class="deck-banner" role="alert">
            <span class="deck-banner-status">{{ statusText }}</span>
            <span class="deck-banner-msg">{{ bannerText }}</span>
            <button class="deck-banner-action" @click="handleGoBack">← {{ $t('step2.backToGraphBuild') }}</button>
          </div>
          <Step2EnvSetup
            :simulationId="currentSimulationId"
            :projectData="projectData"
            :graphData="graphData"
            :systemLogs="systemLogs"
            @go-back="handleGoBack"
            @next-step="handleNextStep"
            @add-log="addLog"
            @update-status="updateStatus"
          />
        </div>

        <aside
          class="uf-drawer"
          :class="{ collapsed: drawerMode === 'hidden', expanded: drawerMode === 'full', 'is-empty': !graphData }"
        >
          <GraphPanel
            :graphData="graphData"
            :loading="graphLoading"
            :currentPhase="2"
            @refresh="refreshGraph"
            @toggle-maximize="toggleDrawerFull"
          />
        </aside>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step2EnvSetup from '../components/Step2EnvSetup.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation, stopSimulation, getEnvStatus, closeSimulationEnv } from '../api/simulation'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n({ useScope: 'global' })
const route = useRoute()
const router = useRouter()

const props = defineProps({ simulationId: String })

const drawerMode = ref('side') // 'hidden' | 'side' | 'full'
const toggleDrawer = () => { drawerMode.value = drawerMode.value === 'hidden' ? 'side' : 'hidden' }
const toggleDrawerFull = () => { drawerMode.value = drawerMode.value === 'full' ? 'side' : 'full' }

const currentSimulationId = ref(route.params.simulationId)
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing')

const statusClass = computed(() => currentStatus.value)
const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Ready'
  return 'Preparing'
})

// 레일 5단 중 이 화면은 2단 → 상단 바 진행선
const stepProgressRatio = 2 / 5

// 배너 문구는 새로 쓰지 않는다: 실패 경로에서 이미 만든 로그 문구(=기존 i18n 키)를 그대로 보여준다
const errorText = ref('')
const bannerText = computed(() => errorText.value || systemLogs.value[systemLogs.value.length - 1]?.msg || '')

const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 100) systemLogs.value.shift()
}

const updateStatus = (status) => { currentStatus.value = status }

const handleGoBack = () => {
  if (projectData.value?.project_id) {
    router.push({ name: 'Process', params: { projectId: projectData.value.project_id } })
  } else {
    router.push('/')
  }
}

const handleNextStep = (params = {}) => {
  addLog(t('log.enterStep3'))
  if (params.maxRounds) addLog(t('log.customRoundsConfig', { rounds: params.maxRounds }))
  else addLog(t('log.useAutoRounds'))
  const routeParams = { name: 'SimulationRun', params: { simulationId: currentSimulationId.value } }
  if (params.maxRounds) routeParams.query = { maxRounds: params.maxRounds }
  router.push(routeParams)
}

const checkAndStopRunningSimulation = async () => {
  if (!currentSimulationId.value) return
  try {
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })
    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog(t('log.detectedSimEnvRunning'))
      try {
        const closeRes = await closeSimulationEnv({ simulation_id: currentSimulationId.value, timeout: 10 })
        if (closeRes.success) addLog(t('log.simEnvClosed'))
        else {
          addLog(t('log.closeSimEnvFailedWithError', { error: closeRes.error || t('common.unknownError') }))
          await forceStopSimulation()
        }
      } catch (closeErr) {
        addLog(t('log.closeSimEnvException', { error: closeErr.message }))
        await forceStopSimulation()
      }
    } else {
      const simRes = await getSimulation(currentSimulationId.value)
      if (simRes.success && simRes.data?.status === 'running') {
        addLog(t('log.detectedSimRunning'))
        await forceStopSimulation()
      }
    }
  } catch (err) {
    console.warn('Failed to check simulation status:', err)
  }
}

const forceStopSimulation = async () => {
  try {
    const stopRes = await stopSimulation({ simulation_id: currentSimulationId.value })
    if (stopRes.success) addLog(t('log.simForceStopSuccess'))
    else addLog(t('log.forceStopSimFailed', { error: stopRes.error || t('common.unknownError') }))
  } catch (err) {
    addLog(t('log.forceStopSimException', { error: err.message }))
  }
}

const loadSimulationData = async () => {
  try {
    addLog(t('log.loadingSimData', { id: currentSimulationId.value }))
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data
      if (simData.project_id) {
        const projRes = await getProject(simData.project_id)
        if (projRes.success && projRes.data) {
          projectData.value = projRes.data
          addLog(t('log.projectLoadSuccess', { id: projRes.data.project_id }))
          if (projRes.data.graph_id) await loadGraph(projRes.data.graph_id)
        }
      }
    } else {
      const msg = t('log.loadSimDataFailed', { error: simRes.error || t('common.unknownError') })
      addLog(msg)
      errorText.value = msg
      updateStatus('error')
    }
  } catch (err) {
    const msg = t('log.loadException', { error: err.message })
    addLog(msg)
    errorText.value = msg
    updateStatus('error')
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true
  try {
    const res = await getGraphData(graphId)
    if (res.success) { graphData.value = res.data; addLog(t('log.graphDataLoadSuccess')) }
  } catch (err) {
    addLog(t('log.graphLoadFailed', { error: err.message }))
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) loadGraph(projectData.value.graph_id)
}

onMounted(async () => {
  addLog(t('log.simViewInit'))
  await checkAndStopRunningSimulation()
  loadSimulationData()
})
</script>

<style>
@import '../assets/layout.css';
</style>

<style scoped>
/* 덱 상단 상태 배너 — 덱은 flex column 이므로 배너가 자리를 차지하고 패널이 남은 높이를 쓴다 */
.deck-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  flex-shrink: 0;
  margin: var(--wm-gutter) var(--wm-gutter) 0;
  padding: 11px 14px;
  border: 1px solid var(--wm-neg);
  border-radius: var(--wm-radius-md);
  background: var(--wm-neg-soft);
  color: var(--wm-text);
  font-size: 12px;
  line-height: 1.5;
}

.deck-banner-status {
  font-family: var(--wm-mono);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--wm-neg);
  flex-shrink: 0;
}

.deck-banner-msg {
  flex: 1 1 220px;
  min-width: 0;
  color: var(--wm-text-muted);
  word-break: break-word;
}

.deck-banner-action {
  flex-shrink: 0;
  padding: 6px 11px;
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-sm);
  background: var(--wm-surface);
  color: var(--wm-text);
  font-family: var(--wm-font);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.deck-banner-action:hover {
  border-color: var(--wm-accent-border);
  background: var(--wm-accent-soft);
  color: var(--wm-accent-text);
}

/* 데이터 없는 스테이지는 side 모드에서도 자리를 덜 차지한다(정직한 빈 상태).
   layout.css 의 `.uf-shell--deck-lead > .uf-main .uf-drawer`(0,3,0)가
   `.uf-drawer.is-empty`(0,2,0)를 이기므로 이 화면에서만 특이도를 올려 되찾는다.
   (접힘은 layout.css 가 `.uf-shell > .uf-main .uf-drawer.collapsed` 로 전역 처리한다.) */
.uf-shell--deck-lead > .uf-main .uf-drawer.is-empty:not(.collapsed) {
  flex: 0 1 clamp(240px, 24%, 340px);
}

/* 배너가 뜨면 설정 패널은 남은 높이를 쓴다(height:100% 로는 넘친다) */
.uf-content :deep(.env-setup-panel) {
  flex: 1 1 auto;
  min-height: 0;
  height: auto;
}
</style>