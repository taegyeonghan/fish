<template>
  <div class="uf-shell" :class="{ 'graph-fullscreen': drawerMode === 'full' }">
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
          <span class="uf-crumb">UngdrooFish</span>
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
          />
        </div>

        <aside class="uf-drawer" :class="{ collapsed: drawerMode === 'hidden', expanded: drawerMode === 'full' }">
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
</style>