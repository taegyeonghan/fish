/**
 * Temporary store for pending files + requirement + simulation config
 * Used for landing page → process page handoff
 */
import { reactive } from 'vue'

const state = reactive({
  files: [],
  simulationRequirement: '',
  simulationConfig: {
    timeUnit: 'day',          // 'hour' | 'day' | 'week' | 'month'
    forecastHorizon: 30,      // number of time units to simulate
  },
  isPending: false
})

export function setPendingUpload(files, requirement, config = null) {
  state.files = files
  state.simulationRequirement = requirement
  if (config) {
    state.simulationConfig = { ...state.simulationConfig, ...config }
  }
  state.isPending = true
}

export function getPendingUpload() {
  return {
    files: state.files,
    simulationRequirement: state.simulationRequirement,
    simulationConfig: state.simulationConfig,
    isPending: state.isPending
  }
}

export function clearPendingUpload() {
  state.files = []
  state.simulationRequirement = ''
  state.simulationConfig = { timeUnit: 'day', forecastHorizon: 30 }
  state.isPending = false
}

export default state