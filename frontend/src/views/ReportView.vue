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
            'uf-step-active': 4 === idx + 1,
            'uf-step-completed': 4 > idx + 1,
            'uf-step-disabled': 4 < idx + 1
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
          <span class="uf-crumb">Step 4</span>
          <span class="uf-crumb-arrow">▸</span>
          <span class="uf-crumb-current">{{ $tm('main.stepNames')[3] }}</span>
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
          <Step4Report
            :reportId="currentReportId"
            :simulationId="simulationId"
            :systemLogs="systemLogs"
            @add-log="addLog"
            @update-status="updateStatus"
          />
        </div>

        <aside class="uf-drawer" :class="{ collapsed: drawerMode === 'hidden', expanded: drawerMode === 'full' }">
          <GraphPanel
            :graphData="graphData"
            :loading="graphLoading"
            :currentPhase="4"
            :isSimulating="false"
            @refresh="refreshGraph"
            @toggle-maximize="toggleDrawerFull"
          />
        </aside>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import GraphPanel from '../components/GraphPanel.vue'
import Step4Report from '../components/Step4Report.vue'
import { getProject, getGraphData } from '../api/graph'
import { getSimulation } from '../api/simulation'
import { getReport } from '../api/report'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n({ useScope: 'global' })

// Props
const props = defineProps({
  reportId: String
})

// Layout State - ，
const drawerMode = ref('hidden') // 'hidden' | 'side' | 'full'
const toggleDrawer = () => { drawerMode.value = drawerMode.value === 'hidden' ? 'side' : 'hidden' }
const toggleDrawerFull = () => { drawerMode.value = drawerMode.value === 'full' ? 'side' : 'full' }

// Data State
const currentReportId = ref(route.params.reportId)
const simulationId = ref(null)
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
  return 'Generating'
})

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

// --- Data Logic ---
const loadReportData = async () => {
  try {
    addLog(t('log.loadReportData', { id: currentReportId.value }))

    //  report  simulation_id
    const reportRes = await getReport(currentReportId.value)
    if (reportRes.success && reportRes.data) {
      const reportData = reportRes.data
      simulationId.value = reportData.simulation_id

      if (simulationId.value) {
        //  simulation 
        const simRes = await getSimulation(simulationId.value)
        if (simRes.success && simRes.data) {
          const simData = simRes.data

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
        }
      }
    } else {
      addLog(t('log.getReportInfoFailed', { error: reportRes.error || t('common.unknownError') }))
    }
  } catch (err) {
    addLog(t('log.loadException', { error: err.message }))
  }
}

const loadGraph = async (graphId) => {
  graphLoading.value = true

  try {
    const res = await getGraphData(graphId)
    if (res.success) {
      graphData.value = res.data
      addLog(t('log.graphDataLoadSuccess'))
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

// Watch route params
watch(() => route.params.reportId, (newId) => {
  if (newId && newId !== currentReportId.value) {
    currentReportId.value = newId
    loadReportData()
  }
}, { immediate: true })

onMounted(() => {
  addLog(t('log.reportViewInit'))
  loadReportData()
})
</script>

<style>
@import '../assets/layout.css';
</style>