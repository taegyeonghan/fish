<template>
  <!-- R4 상호작용 실행: 세계가 움직이는 유일한 화면 → 스테이지·덱 균형(balanced) -->
  <div
    class="uf-shell uf-shell--balanced"
    :class="{ 'graph-fullscreen': drawerMode === 'full', 'is-running': isSimulating }"
    :style="{ '--wm-progress': String(runProgress) }"
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
            'uf-step-active': 3 === idx + 1,
            'uf-step-completed': 3 > idx + 1,
            'uf-step-disabled': 3 < idx + 1
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
          <span class="uf-crumb">Step 3</span>
          <span class="uf-crumb-arrow">▸</span>
          <span class="uf-crumb-current">{{ $tm('main.stepNames')[2] }}</span>
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
          <Step3Simulation
            :simulationId="currentSimulationId"
            :maxRounds="maxRounds"
            :minutesPerRound="minutesPerRound"
            :projectData="projectData"
            :graphData="graphData"
            :systemLogs="systemLogs"
            @go-back="handleGoBack"
            @next-step="handleNextStep"
            @add-log="addLog"
            @update-status="updateStatus"
            @update-progress="updateProgress"
          />
        </div>

        <aside
          class="uf-drawer"
          :class="{ collapsed: drawerMode === 'hidden', expanded: drawerMode === 'full', 'is-empty': !hasGraph }"
        >
          <GraphPanel
            :graphData="graphData"
            :loading="graphLoading"
            :currentPhase="3"
            :isSimulating="isSimulating"
            @refresh="refreshGraph"
            @toggle-maximize="toggleDrawerFull"
          />
        </aside>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GraphPanel from '../components/GraphPanel.vue'
import Step3Simulation from '../components/Step3Simulation.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation, getSimulationConfig, stopSimulation, closeSimulationEnv, getEnvStatus } from '../api/simulation'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n({ useScope: 'global' })
const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  simulationId: String
})

// Layout State
const drawerMode = ref('side') // 'hidden' | 'side' | 'full'
const toggleDrawer = () => { drawerMode.value = drawerMode.value === 'hidden' ? 'side' : 'hidden' }
const toggleDrawerFull = () => { drawerMode.value = drawerMode.value === 'full' ? 'side' : 'full' }

// Data State
const currentSimulationId = ref(route.params.simulationId)
//  query  maxRounds，
const maxRounds = ref(route.query.maxRounds ? parseInt(route.query.maxRounds) : null)
const minutesPerRound = ref(30) // 30
const projectData = ref(null)
const graphData = ref(null)
const graphLoading = ref(false)
const systemLogs = ref([])
const currentStatus = ref('processing') // processing | completed | error

// --- Status Computed ---
const statusClass = computed(() => {
  return currentStatus.value
})

const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Completed'
  return 'Running'
})

const isSimulating = computed(() => currentStatus.value === 'processing')

// 그래프가 비었으면 스테이지 띠를 줄인다(죽은 공간 방지)
const hasGraph = computed(() => !!graphData.value?.nodes?.length)

// 상단 바 진행선 — Step3 이 라운드 진행도를 올려준다(0~1)
const runProgress = ref(0)
const updateProgress = (ratio) => {
  const n = Number(ratio)
  runProgress.value = Number.isFinite(n) ? Math.min(1, Math.max(0, n)) : 0
}

// --- Helpers ---
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }) + '.' + new Date().getMilliseconds().toString().padStart(3, '0')
  systemLogs.value.push({ time, msg })
  if (systemLogs.value.length > 200) {
    systemLogs.value.shift()
  }
}

const updateStatus = (status) => {
  currentStatus.value = status
}

const handleGoBack = async () => {
  //  Step 2 ，
  addLog(t('log.preparingGoBack'))

  stopGraphRefresh()

  try {
    const envStatusRes = await getEnvStatus({ simulation_id: currentSimulationId.value })

    if (envStatusRes.success && envStatusRes.data?.env_alive) {
      addLog(t('log.closingSimEnv'))
      try {
        await closeSimulationEnv({
          simulation_id: currentSimulationId.value,
          timeout: 10
        })
        addLog(t('log.simEnvClosed'))
      } catch (closeErr) {
        addLog(t('log.closeSimEnvFailed'))
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog(t('log.simForceStopSuccess'))
        } catch (stopErr) {
          addLog(t('log.forceStopFailed', { error: stopErr.message }))
        }
      }
    } else {
      // ，
      if (isSimulating.value) {
        addLog(t('log.stoppingSimProcess'))
        try {
          await stopSimulation({ simulation_id: currentSimulationId.value })
          addLog(t('log.simStopped'))
        } catch (err) {
          addLog(t('log.stopSimFailed', { error: err.message }))
        }
      }
    }
  } catch (err) {
    addLog(t('log.checkStatusFailed', { error: err.message }))
  }

  //  Step 2 ()
  router.push({ name: 'Simulation', params: { simulationId: currentSimulationId.value } })
}

const handleNextStep = () => {
  // Step3Simulation 
  addLog(t('log.enterStep4'))
}

// --- Data Logic ---
const loadSimulationData = async () => {
  try {
    addLog(t('log.loadingSimData', { id: currentSimulationId.value }))

    //  simulation 
    const simRes = await getSimulation(currentSimulationId.value)
    if (simRes.success && simRes.data) {
      const simData = simRes.data

      //  simulation config  minutes_per_round
      try {
        const configRes = await getSimulationConfig(currentSimulationId.value)
        if (configRes.success && configRes.data?.time_config?.minutes_per_round) {
          minutesPerRound.value = configRes.data.time_config.minutes_per_round
          addLog(t('log.timeConfig', { minutes: minutesPerRound.value }))
        }
      } catch (configErr) {
        addLog(t('log.timeConfigFetchFailed', { minutes: minutesPerRound.value }))
      }

      //  project 
      if (simData.project_id) {
        const projRes = await getProject(simData.project_id)
        if (projRes.success && projRes.data) {
          projectData.value = projRes.data
          addLog(t('log.projectLoadSuccess', { id: projRes.data.project_id }))

          //  graph 
          if (projRes.data.graph_id) {
            await loadGraph(projRes.data.graph_id)
          }
        }
      }
    } else {
      addLog(t('log.loadSimDataFailed', { error: simRes.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('log.loadException', { error: err.message }))
  }
}

const loadGraph = async (graphId) => {
  // ， loading，
  //  loading
  if (!isSimulating.value) {
    graphLoading.value = true
  }

  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      if (!isSimulating.value) {
        addLog(t('log.graphDataLoadSuccess'))
      }
    }
  } catch (err) {
    addLog(t('log.graphLoadFailed', { error: err.message }))
  } finally {
    graphLoading.value = false
  }
}

const refreshGraph = () => {
  if (projectData.value?.graph_id) {
    loadGraph(projectData.value.graph_id)
  }
}

// --- Auto Refresh Logic ---
let graphRefreshTimer = null

const startGraphRefresh = () => {
  if (graphRefreshTimer) return
  addLog(t('log.graphRealtimeRefreshStart'))
  // ，30
  graphRefreshTimer = setInterval(refreshGraph, 30000)
}

const stopGraphRefresh = () => {
  if (graphRefreshTimer) {
    clearInterval(graphRefreshTimer)
    graphRefreshTimer = null
    addLog(t('log.graphRealtimeRefreshStop'))
  }
}

watch(isSimulating, (newValue) => {
  if (newValue) {
    startGraphRefresh()
  } else {
    stopGraphRefresh()
  }
}, { immediate: true })

onMounted(() => {
  addLog(t('log.simRunViewInit'))

  //  maxRounds （ query ）
  if (maxRounds.value) {
    addLog(t('log.customRounds', { rounds: maxRounds.value }))
  }

  loadSimulationData()
})

onUnmounted(() => {
  stopGraphRefresh()
})
</script>

<style>
@import '../assets/layout.css';

/* balanced 모드는 스테이지에 남는 폭을 전부 주지만, 그래프가 아직 없으면
   빈 캔버스가 화면 절반을 먹는다. side 폭(>1180)에서만 스테이지를 줄이고 덱을 늘린다.
   (band 모드의 .is-empty 높이 규칙은 건드리지 않는다.) */
@media (min-width: 1181px) {
  /* 접혔을 때는 폭 0 이 우선이므로 :not(.collapsed) 로 빠진다
     (layout.css 의 접힘 규칙과 특이도가 같아 순서에 의존하지 않게 한다). */
  .uf-shell--balanced > .uf-main .uf-drawer.is-empty:not(.collapsed) {
    flex: 0 0 clamp(280px, 26%, 380px);
  }

  .uf-shell--balanced > .uf-main .uf-content:has(+ .uf-drawer.is-empty) {
    flex: 1 1 auto;
  }
}

/* 실행 중에는 스테이지 격자가 아주 느리게 흐른다(세계가 돌아가고 있다는 신호).
   .uf-shell.is-running 은 이 화면만 붙인다. prefers-reduced-motion 은 전역 시트가 처리. */
.uf-shell.is-running .graph-container {
  animation: wm-stage-drift 24s linear infinite;
}

@keyframes wm-stage-drift {
  to { background-position: 0 0, 28px 28px, 28px 28px, 0 0; }
}
</style>