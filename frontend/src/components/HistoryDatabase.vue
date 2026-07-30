<template>
  <div 
    class="history-database"
    :class="{ 'no-projects': projects.length === 0 && !loading }"
    ref="historyContainer"
  >
    <!-- ：(설명 생략) -->
    <div v-if="projects.length > 0 || loading" class="tech-grid-bg">
      <div class="grid-pattern"></div>
      <div class="gradient-overlay"></div>
    </div>

    <!--  -->
    <div class="section-header">
      <div class="section-line"></div>
      <span class="section-title">{{ $t('history.title') }}</span>
      <div class="section-line"></div>
    </div>

    <!-- (설명 생략) -->
    <div v-if="projects.length > 0" class="cards-container" :class="{ expanded: isExpanded }">
      <div
        v-for="(project, index) in projects"
        :key="project.simulation_id"
        class="project-card"
        :class="{ expanded: isExpanded, hovering: hoveringCard === index }"
        @mouseenter="hoveringCard = index"
        @mouseleave="hoveringCard = null"
        @click="navigateToProject(project)"
      >
        <!-- ：simulation_id   -->
        <div class="card-header">
          <span class="card-id">{{ formatSimulationId(project.simulation_id) }}</span>
          <div class="card-status-icons">
            <span 
              class="status-icon" 
              :class="{ available: project.project_id, unavailable: !project.project_id }"
              :title="$t('history.graphBuild')"
            >◇</span>
            <span 
              class="status-icon available" 
              :title="$t('history.envSetup')"
            >◈</span>
            <span 
              class="status-icon" 
              :class="{ available: project.report_id, unavailable: !project.report_id }"
              :title="$t('history.analysisReport')"
            >◆</span>
          </div>
        </div>

        <!--  -->
        <div class="card-actions-row">
          <button
            class="card-delete-btn"
            :disabled="deletingSimulationId === project.simulation_id"
            @click.stop="deleteHistoryItem(project)"
          >
            {{ deletingSimulationId === project.simulation_id ? '...' : $t('history.deleteButton') }}
          </button>
        </div>

        <div class="card-files-wrapper">
          <!--  -  -->
          <div class="corner-mark top-left-only"></div>
          
          <!--  -->
          <div class="files-list" v-if="project.files && project.files.length > 0">
            <div 
              v-for="(file, fileIndex) in project.files.slice(0, 3)" 
              :key="fileIndex"
              class="file-item"
            >
              <span class="file-tag" :class="getFileType(file.filename)">{{ getFileTypeLabel(file.filename) }}</span>
              <span class="file-name">{{ truncateFilename(file.filename, 20) }}</span>
            </div>
            <!-- ， -->
            <div v-if="project.files.length > 3" class="files-more">
              {{ $t('history.moreFiles', { count: project.files.length - 3 }) }}
            </div>
          </div>
          <!--  -->
          <div class="files-empty" v-else>
            <span class="empty-file-icon">◇</span>
            <span class="empty-file-text">{{ $t('history.noFiles') }}</span>
          </div>
        </div>

        <!-- （20） -->
        <h3 class="card-title">{{ getSimulationTitle(project.simulation_requirement) }}</h3>

        <!-- (설명 생략) -->
        <p class="card-desc">{{ truncateText(project.simulation_requirement, 55) }}</p>

        <!--  -->
        <div class="card-footer">
          <div class="card-datetime">
            <span class="card-date">{{ formatDate(project.created_at) }}</span>
            <span class="card-time">{{ formatTime(project.created_at) }}</span>
          </div>
          <span class="card-progress" :class="getProgressClass(project)">
            <span class="status-dot">●</span> {{ formatRounds(project) }}
          </span>
        </div>
        
        <!--  (hover) -->
        <div class="card-bottom-line"></div>
      </div>
    </div>

    <!--  -->
    <div v-if="loading" class="loading-state">
      <span class="loading-spinner"></span>
      <span class="loading-text">{{ $t('history.loadingText') }}</span>
    </div>

    <!-- 아카이브 0건 — 기존 키(common.noData)로 정직하게 비었음을 표시 -->
    <div v-else-if="projects.length === 0" class="empty-state">
      <span class="empty-icon">◇</span>
      <span class="empty-text">{{ $t('common.noData') }}</span>
    </div>

    <!--  -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="selectedProject" class="modal-overlay" @click.self="closeModal">
          <div class="modal-content">
            <!--  -->
            <div class="modal-header">
              <div class="modal-title-section">
                <span class="modal-id">{{ formatSimulationId(selectedProject.simulation_id) }}</span>
                <span class="modal-progress" :class="getProgressClass(selectedProject)">
                  <span class="status-dot">●</span> {{ formatRounds(selectedProject) }}
                </span>
                <span class="modal-create-time">{{ formatDate(selectedProject.created_at) }} {{ formatTime(selectedProject.created_at) }}</span>
              </div>
              <button class="modal-close" @click="closeModal">×</button>
            </div>

            <!--  -->
            <div class="modal-body">
              <!--  -->
              <div class="modal-section">
                <div class="modal-label">{{ $t('history.simRequirement') }}</div>
                <div class="modal-requirement">{{ selectedProject.simulation_requirement || $t('common.none') }}</div>
              </div>

              <!--  -->
              <div class="modal-section">
                <div class="modal-label">{{ $t('history.relatedFiles') }}</div>
                <div class="modal-files" v-if="selectedProject.files && selectedProject.files.length > 0">
                  <div v-for="(file, index) in selectedProject.files" :key="index" class="modal-file-item">
                    <span class="file-tag" :class="getFileType(file.filename)">{{ getFileTypeLabel(file.filename) }}</span>
                    <span class="modal-file-name">{{ file.filename }}</span>
                  </div>
                </div>
                <div class="modal-empty" v-else>{{ $t('history.noRelatedFiles') }}</div>
              </div>
            </div>

            <!--  -->
            <div class="modal-divider">
              <span class="divider-line"></span>
              <span class="divider-text">{{ $t('history.replayTitle') }}</span>
              <span class="divider-line"></span>
            </div>

            <!--  -->
            <div class="modal-actions">
              <button
                class="modal-btn btn-delete"
                :disabled="deletingSimulationId === selectedProject.simulation_id"
                @click="deleteHistoryItem(selectedProject)"
              >
                <span class="btn-step">Delete</span>
                <span class="btn-icon">×</span>
                <span class="btn-text">
                  {{ deletingSimulationId === selectedProject.simulation_id ? $t('history.deleting') : $t('history.deleteButton') }}
                </span>
              </button>
              <button 
                class="modal-btn btn-project" 
                @click="goToProject"
                :disabled="!selectedProject.project_id"
              >
                <span class="btn-step">Step1</span>
                <span class="btn-icon">◇</span>
                <span class="btn-text">{{ $t('history.step1Button') }}</span>
              </button>
              <button 
                class="modal-btn btn-simulation" 
                @click="goToSimulation"
              >
                <span class="btn-step">Step2</span>
                <span class="btn-icon">◈</span>
                <span class="btn-text">{{ $t('history.step2Button') }}</span>
              </button>
              <button 
                class="modal-btn btn-report" 
                @click="goToReport"
                :disabled="!selectedProject.report_id"
              >
                <span class="btn-step">Step4</span>
                <span class="btn-icon">◆</span>
                <span class="btn-text">{{ $t('history.step4Button') }}</span>
              </button>
            </div>
            <!--  -->
            <div class="modal-playback-hint">
              <span class="hint-text">{{ $t('history.replayHint') }}</span>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, onActivated, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { deleteSimulation, getSimulationHistory } from '../api/simulation'

const router = useRouter()
const route = useRoute()
const { t } = useI18n({ useScope: 'global' })

const projects = ref([])
const deletingSimulationId = ref(null)
const loading = ref(true)
const isExpanded = ref(false)
const hoveringCard = ref(null)
const historyContainer = ref(null)
let observer = null
let pendingState = null
const selectedProject = ref(null)
let isAnimating = false
let expandDebounceTimer = null

// 카드 배치는 CSS 그리드가 정한다(.cards-container). 화면에 들어왔는지(isExpanded)는
// 인라인 transform 대신 .expanded 클래스의 등장 전이로만 쓴다.
const getProgressClass = (simulation) => {
  const current = simulation.current_round || 0
  const total = simulation.total_rounds || 0
  
  if (total === 0 || current === 0) {
    return 'not-started'
  } else if (current >= total) {
    return 'completed'
  } else {
    return 'in-progress'
  }
}

// (설명 생략)
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toISOString().slice(0, 10)
  } catch {
    return dateStr?.slice(0, 10) || ''
  }
}

// （:）
const formatTime = (dateStr) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    const hours = date.getHours().toString().padStart(2, '0')
    const minutes = date.getMinutes().toString().padStart(2, '0')
    return `${hours}:${minutes}`
  } catch {
    return ''
  }
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  return text.length > maxLength ? text.slice(0, maxLength) + '...' : text
}

// （20）
const getSimulationTitle = (requirement) => {
  if (!requirement) return t('history.untitledSimulation')
  const title = requirement.slice(0, 20)
  return requirement.length > 20 ? title + '...' : title
}

//  simulation_id （6）
const formatSimulationId = (simulationId) => {
  if (!simulationId) return 'SIM_UNKNOWN'
  const prefix = simulationId.replace('sim_', '').slice(0, 6)
  return `SIM_${prefix.toUpperCase()}`
}

// （/）
const formatRounds = (simulation) => {
  const current = simulation.current_round || 0
  const total = simulation.total_rounds || 0
  if (total === 0) return t('history.notStarted')
  return t('history.roundsProgress', { current, total })
}

// (설명 생략)
const getFileType = (filename) => {
  if (!filename) return 'other'
  const ext = filename.split('.').pop()?.toLowerCase()
  const typeMap = {
    'pdf': 'pdf',
    'doc': 'doc', 'docx': 'doc',
    'xls': 'xls', 'xlsx': 'xls', 'csv': 'xls',
    'ppt': 'ppt', 'pptx': 'ppt',
    'txt': 'txt', 'md': 'txt', 'json': 'code',
    'jpg': 'img', 'jpeg': 'img', 'png': 'img', 'gif': 'img',
    'zip': 'zip', 'rar': 'zip', '7z': 'zip'
  }
  return typeMap[ext] || 'other'
}

const getFileTypeLabel = (filename) => {
  if (!filename) return 'FILE'
  const ext = filename.split('.').pop()?.toUpperCase()
  return ext || 'FILE'
}

// (설명 생략)
const truncateFilename = (filename, maxLength) => {
  if (!filename) return t('history.unknownFile')
  if (filename.length <= maxLength) return filename
  
  const ext = filename.includes('.') ? '.' + filename.split('.').pop() : ''
  const nameWithoutExt = filename.slice(0, filename.length - ext.length)
  const truncatedName = nameWithoutExt.slice(0, maxLength - ext.length - 3) + '...'
  return truncatedName + ext
}

const navigateToProject = (simulation) => {
  selectedProject.value = simulation
}

const closeModal = () => {
  selectedProject.value = null
}

// （Project）
const goToProject = () => {
  if (selectedProject.value?.project_id) {
    router.push({
      name: 'Process',
      params: { projectId: selectedProject.value.project_id }
    })
    closeModal()
  }
}

// （Simulation）
const goToSimulation = () => {
  if (selectedProject.value?.simulation_id) {
    router.push({
      name: 'Simulation',
      params: { simulationId: selectedProject.value.simulation_id }
    })
    closeModal()
  }
}

// （Report）
const goToReport = () => {
  if (selectedProject.value?.report_id) {
    router.push({
      name: 'Report',
      params: { reportId: selectedProject.value.report_id }
    })
    closeModal()
  }
}

const deleteHistoryItem = async (simulation) => {
  if (!simulation?.simulation_id || deletingSimulationId.value) return

  const confirmed = window.confirm(t('history.deleteConfirm', {
    id: formatSimulationId(simulation.simulation_id)
  }))
  if (!confirmed) return

  deletingSimulationId.value = simulation.simulation_id

  try {
    const response = await deleteSimulation(simulation.simulation_id)
    if (response.success) {
      projects.value = projects.value.filter(
        item => item.simulation_id !== simulation.simulation_id
      )
      if (selectedProject.value?.simulation_id === simulation.simulation_id) {
        closeModal()
      }
    }
  } catch (error) {
    console.error('Delete simulation failed:', error)
    alert(t('history.deleteFailed', { error: error.message || error }))
  } finally {
    deletingSimulationId.value = null
  }
}

const loadHistory = async () => {
  try {
    loading.value = true
    const response = await getSimulationHistory(20)
    if (response.success) {
      projects.value = response.data || []
    }
  } catch (error) {
    console.error(':', error)
    projects.value = []
  } finally {
    loading.value = false
  }
}

//  IntersectionObserver
const initObserver = () => {
  if (observer) {
    observer.disconnect()
  }
  
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const shouldExpand = entry.isIntersecting
        
        // (설명 생략)
        pendingState = shouldExpand
        
        // (설명 생략)
        if (expandDebounceTimer) {
          clearTimeout(expandDebounceTimer)
          expandDebounceTimer = null
        }
        
        // ，，
        if (isAnimating) return
        
        // ，
        if (shouldExpand === isExpanded.value) {
          pendingState = null
          return
        }
        
        // ，
        // (50ms)，(200ms)
        const delay = shouldExpand ? 50 : 200
        
        expandDebounceTimer = setTimeout(() => {
          if (isAnimating) return
          
          // (설명 생략)
          if (pendingState === null || pendingState === isExpanded.value) return
          
          isAnimating = true
          isExpanded.value = pendingState
          pendingState = null
          
          // ，
          setTimeout(() => {
            isAnimating = false
            
            // ，
            if (pendingState !== null && pendingState !== isExpanded.value) {
              // ，
              expandDebounceTimer = setTimeout(() => {
                if (pendingState !== null && pendingState !== isExpanded.value) {
                  isAnimating = true
                  isExpanded.value = pendingState
                  pendingState = null
                  setTimeout(() => {
                    isAnimating = false
                  }, 750)
                }
              }, 100)
            }
          }, 750)
        }, delay)
      })
    },
    {
      // ，
      threshold: [0.4, 0.6, 0.8],
      //  rootMargin，，
      rootMargin: '0px 0px -150px 0px'
    }
  )
  
  if (historyContainer.value) {
    observer.observe(historyContainer.value)
  }
}

// ，
watch(() => route.path, (newPath) => {
  if (newPath === '/') {
    loadHistory()
  }
})

onMounted(async () => {
  //  DOM 
  await nextTick()
  await loadHistory()
  
  //  DOM 
  setTimeout(() => {
    initObserver()
  }, 100)
})

//  keep-alive，
onActivated(() => {
  loadHistory()
})

onUnmounted(() => {
  //  Intersection Observer
  if (observer) {
    observer.disconnect()
    observer = null
  }
  if (expandDebounceTimer) {
    clearTimeout(expandDebounceTimer)
    expandDebounceTimer = null
  }
})
</script>

<style scoped>
/* 색·형태는 --wm-* 정본 토큰만 쓴다(정의: assets/market-world.css).
   Zone C 아카이브: 카드는 부채꼴(절대 위치 + JS transform)에서 전폭 그리드로 바꿨다.
   1080 임베드에서 부채꼴은 컨테이너(약 1016px)를 넘어 좌우 카드가 잘려 나갔다(실측). */
.history-database {
  position: relative;
  width: 100%;
  margin-top: 24px;
  padding: 28px 0 8px;
  overflow: visible;
}

/*  */
.history-database.no-projects {
  min-height: auto;
  padding: 20px 0 4px;
}

/*  */
.tech-grid-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  pointer-events: none;
}

/* CSS */
.grid-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    linear-gradient(to right, var(--wm-grid) 1px, transparent 1px),
    linear-gradient(to bottom, var(--wm-grid) 1px, transparent 1px);
  background-size: 50px 50px;
  /* ，， */
  background-position: top left;
}

/* 격자 띠의 네 변을 배경색으로 페이드 — 다크/라이트 모두 바닥색을 따라간다 */
.gradient-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    linear-gradient(to right, var(--wm-bg) 0%, transparent 15%, transparent 85%, var(--wm-bg) 100%),
    linear-gradient(to bottom, var(--wm-bg) 0%, transparent 20%, transparent 80%, var(--wm-bg) 100%);
  pointer-events: none;
}

/*  */
.section-header {
  position: relative;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  margin-bottom: 20px;
  font-family: var(--wm-mono);
}

.section-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--wm-border), transparent);
  max-width: 300px;
}

.section-title {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--wm-text-dim);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  white-space: nowrap;
}

/* 아카이브 카드 — 전폭 그리드 */
.cards-container {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--wm-gutter);
}

/*  */
.project-card {
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--wm-surface);
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-md);
  padding: 14px;
  cursor: pointer;
  box-shadow: var(--wm-shadow-1);
  /* 아카이브가 화면에 들어오면(.expanded) 카드가 제자리로 올라온다.
     관찰자가 끝내 발화하지 않아도 카드는 그대로 읽힌다(가시성을 상태에 걸지 않는다). */
  transform: translateY(6px);
  transition: transform 600ms cubic-bezier(0.23, 1, 0.32, 1), box-shadow 0.3s ease, border-color 0.3s ease;
}

.cards-container.expanded .project-card {
  transform: none;
}

.project-card:hover {
  box-shadow: var(--wm-shadow-2);
  border-color: var(--wm-border-strong);
  z-index: 1000 !important;
}

.project-card.hovering {
  z-index: 1000 !important;
}

/*  */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--wm-border-soft);
  font-family: var(--wm-mono);
  font-size: 0.7rem;
}

.card-id {
  color: var(--wm-text-muted);
  letter-spacing: 0.5px;
  font-weight: 500;
}

/*  */
.card-status-icons {
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-actions-row {
  display: flex;
  justify-content: flex-end;
  margin: -6px 0 8px;
}

.card-delete-btn {
  border: 1px solid var(--wm-border);
  background: var(--wm-neg-soft);
  color: var(--wm-neg);
  border-radius: var(--wm-radius-sm);
  padding: 4px 8px;
  font-family: var(--wm-mono);
  font-size: 0.7rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}

.card-delete-btn:hover:not(:disabled) {
  border-color: var(--wm-neg);
}

.card-delete-btn:disabled {
  cursor: wait;
  opacity: 0.6;
}

.status-icon {
  font-size: 0.75rem;
  transition: all 0.2s ease;
  cursor: default;
}

.status-icon.available {
  opacity: 1;
}

/* 그래프 생성 / 환경 설정 / 분석 리포트 — 진행 단계 구분 */
.status-icon:nth-child(1).available { color: var(--wm-info); }
.status-icon:nth-child(2).available { color: var(--wm-warn); }
.status-icon:nth-child(3).available { color: var(--wm-pos); }

.status-icon.unavailable {
  color: var(--wm-text-dim);
  opacity: 0.5;
}

/*  */
.card-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  letter-spacing: 0.5px;
  font-weight: 600;
  font-size: 0.65rem;
}

.status-dot {
  font-size: 0.5rem;
}

/*  */
.card-progress.completed { color: var(--wm-pos); }
.card-progress.in-progress { color: var(--wm-warn); }
.card-progress.not-started { color: var(--wm-text-dim); }
.card-status.pending { color: var(--wm-text-dim); }

/*  */
.card-files-wrapper {
  position: relative;
  width: 100%;
  min-height: 48px;
  /* 파일 3건 + "+N개 파일" 줄까지 잘리지 않는 높이(110px 에서는 마지막 줄이 잘렸다) */
  max-height: 132px;
  margin-bottom: 12px;
  padding: 8px 10px;
  background: var(--wm-surface-2);
  border-radius: var(--wm-radius-sm);
  border: 1px solid var(--wm-border);
  overflow: hidden;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/*  */
.files-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3px 6px;
  font-family: var(--wm-mono);
  font-size: 0.6rem;
  color: var(--wm-text-muted);
  background: var(--wm-surface);
  border-radius: var(--wm-radius-sm);
  letter-spacing: 0.3px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 6px;
  background: var(--wm-surface);
  border: 1px solid transparent;
  border-radius: var(--wm-radius-sm);
  transition: all 0.2s ease;
}

.file-item:hover {
  background: var(--wm-surface-3);
  transform: translateX(2px);
  border-color: var(--wm-border);
}

/* 파일 종류 라벨 — 정본은 중성 배지(색 구분 없음, market-world.css .file-tag) */
.file-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 16px;
  padding: 0 4px;
  color: var(--wm-text-muted);
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-sm);
  font-family: var(--wm-mono);
  font-size: 0.55rem;
  font-weight: 600;
  line-height: 1;
  text-transform: uppercase;
  letter-spacing: 0.2px;
  flex-shrink: 0;
  min-width: 28px;
}

.file-name {
  font-family: var(--wm-font);
  font-size: 0.7rem;
  color: var(--wm-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: 0.1px;
}

/*  */
.files-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 48px;
  color: var(--wm-text-dim);
}

.empty-file-icon {
  font-size: 1rem;
  opacity: 0.5;
}

.empty-file-text {
  font-family: var(--wm-mono);
  font-size: 0.7rem;
  letter-spacing: 0.5px;
}

/*  */
.project-card:hover .card-files-wrapper {
  border-color: var(--wm-border-strong);
}

/*  */
.corner-mark.top-left-only {
  position: absolute;
  top: 6px;
  left: 6px;
  width: 8px;
  height: 8px;
  border-top: 1.5px solid var(--wm-border-strong);
  border-left: 1.5px solid var(--wm-border-strong);
  pointer-events: none;
  z-index: 10;
}

/*  */
.card-title {
  font-family: var(--wm-font);
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--wm-text);
  margin: 0 0 6px 0;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.3s ease;
}

/* 전역 시트가 .card-title 색을 !important 로 고정하므로 hover 는 같은 무게로 덮는다 */
.project-card:hover .card-title {
  color: var(--wm-accent-text) !important;
}

/*  */
.card-desc {
  font-family: var(--wm-font);
  font-size: 0.75rem;
  color: var(--wm-text-muted);
  margin: 0 0 16px 0;
  line-height: 1.5;
  height: 34px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* 같은 행의 카드 높이를 맞추고(그리드 stretch) 푸터는 카드 밑단에 붙인다 */
.card-footer {
  position: relative;
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--wm-border-soft);
  font-family: var(--wm-mono);
  font-size: 0.65rem;
  color: var(--wm-text-dim);
  font-weight: 500;
}

/*  */
.card-datetime {
  display: flex;
  align-items: center;
  gap: 8px;
}

/*  */
.card-footer .card-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  letter-spacing: 0.5px;
  font-weight: 600;
  font-size: 0.65rem;
}

.card-footer .status-dot {
  font-size: 0.5rem;
}

/*  -  */
.card-footer .card-progress.completed { color: var(--wm-pos); }
.card-footer .card-progress.in-progress { color: var(--wm-warn); }
.card-footer .card-progress.not-started { color: var(--wm-text-dim); }

/*  */
.card-bottom-line {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  width: 0;
  background-color: var(--wm-accent);
  transition: width 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  z-index: 20;
}

.project-card:hover .card-bottom-line {
  width: 100%;
}

/* 0건·로딩 상태 */
.empty-state, .loading-state {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 36px;
  color: var(--wm-text-dim);
}

.empty-state {
  border: 1px dashed var(--wm-border);
  border-radius: var(--wm-radius-md);
  background: var(--wm-surface);
}

.empty-icon {
  font-size: 2rem;
  opacity: 0.5;
}

.empty-text {
  font-family: var(--wm-mono);
  font-size: 0.72rem;
  letter-spacing: 0.08em;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--wm-border);
  border-top-color: var(--wm-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* =====  ===== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--wm-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: var(--wm-surface);
  width: 560px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-lg);
  box-shadow: var(--wm-shadow-3);
}

/*  */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-content {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-leave-active .modal-content {
  transition: all 0.2s ease-in;
}

.modal-enter-from .modal-content {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}

.modal-leave-to .modal-content {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}

/*  */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 32px;
  border-bottom: 1px solid var(--wm-border);
  background: var(--wm-surface);
}

.modal-title-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.modal-id {
  font-family: var(--wm-mono);
  font-size: 1rem;
  font-weight: 600;
  color: var(--wm-text);
  letter-spacing: 0.5px;
}

.modal-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--wm-mono);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: var(--wm-radius-sm);
  background: var(--wm-surface-2);
}

.modal-progress.completed { color: var(--wm-pos); background: var(--wm-pos-soft); }
.modal-progress.in-progress { color: var(--wm-warn); background: var(--wm-warn-soft); }
.modal-progress.not-started { color: var(--wm-text-dim); background: var(--wm-surface-2); }

.modal-create-time {
  font-family: var(--wm-mono);
  font-size: 0.75rem;
  color: var(--wm-text-dim);
  letter-spacing: 0.3px;
}

.modal-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 1.5rem;
  color: var(--wm-text-dim);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  border-radius: var(--wm-radius-sm);
}

.modal-close:hover {
  background: var(--wm-surface-2);
  color: var(--wm-text);
}

/*  */
.modal-body {
  padding: 24px 32px;
}

.modal-section {
  margin-bottom: 24px;
}

.modal-section:last-child {
  margin-bottom: 0;
}

.modal-label {
  font-family: var(--wm-mono);
  font-size: 0.7rem;
  color: var(--wm-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 10px;
  font-weight: 500;
}

.modal-requirement {
  font-size: 0.95rem;
  color: var(--wm-text);
  line-height: 1.6;
  padding: 16px;
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-sm);
}

.modal-files {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 200px;
  overflow-y: auto;
  padding-right: 4px;
}

/*  */
.modal-files::-webkit-scrollbar {
  width: 4px;
}

.modal-files::-webkit-scrollbar-track {
  background: var(--wm-surface-2);
  border-radius: 2px;
}

.modal-files::-webkit-scrollbar-thumb {
  background: var(--wm-border-strong);
  border-radius: 2px;
}

.modal-files::-webkit-scrollbar-thumb:hover {
  background: var(--wm-text-dim);
}

.modal-file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: var(--wm-surface);
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-sm);
  transition: all 0.2s ease;
}

.modal-file-item:hover {
  border-color: var(--wm-border-strong);
  box-shadow: var(--wm-shadow-1);
}

.modal-file-name {
  font-size: 0.85rem;
  color: var(--wm-text-muted);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.modal-empty {
  font-size: 0.85rem;
  color: var(--wm-text-dim);
  padding: 16px;
  background: var(--wm-surface-2);
  border: 1px dashed var(--wm-border);
  border-radius: var(--wm-radius-sm);
  text-align: center;
}

/*  */
.modal-divider {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 32px 0;
  background: var(--wm-surface);
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--wm-border), transparent);
}

.divider-text {
  font-family: var(--wm-mono);
  font-size: 0.7rem;
  color: var(--wm-text-dim);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  white-space: nowrap;
}

/*  */
.modal-actions {
  display: flex;
  gap: 12px;
  padding: 20px 32px;
  background: var(--wm-surface);
}

.modal-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-sm);
  background: var(--wm-surface-2);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.modal-btn:hover:not(:disabled) {
  border-color: var(--wm-accent-border);
  transform: translateY(-2px);
  box-shadow: var(--wm-shadow-2);
}

.modal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--wm-surface-2);
}

.btn-step {
  font-family: var(--wm-mono);
  font-size: 0.6rem;
  font-weight: 500;
  color: var(--wm-text-dim);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.btn-icon {
  font-size: 1.4rem;
  line-height: 1;
  transition: color 0.2s ease;
}

.btn-text {
  font-family: var(--wm-mono);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: var(--wm-text-muted);
}

.modal-btn.btn-project .btn-icon { color: var(--wm-info); }
.modal-btn.btn-simulation .btn-icon { color: var(--wm-warn); }
.modal-btn.btn-report .btn-icon { color: var(--wm-pos); }
.modal-btn.btn-delete .btn-icon,
.modal-btn.btn-delete .btn-text { color: var(--wm-neg); }
.modal-btn.btn-delete:hover:not(:disabled) {
  border-color: var(--wm-neg);
  background: var(--wm-neg-soft);
}

.modal-btn:hover:not(:disabled) .btn-text {
  color: var(--wm-text);
}

/*  */
.modal-playback-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 32px 20px;
  background: var(--wm-surface);
}

.hint-text {
  font-family: var(--wm-mono);
  font-size: 0.7rem;
  color: var(--wm-text-dim);
  letter-spacing: 0.3px;
  text-align: center;
  line-height: 1.5;
}
</style>
