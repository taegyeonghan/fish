<template>
  <div class="workbench-panel">
    <div class="scroll-container">
      <!-- Step 01: Ontology -->
      <div class="step-card" :class="{ 'active': currentPhase === 0, 'completed': currentPhase > 0 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">01</span>
            <span class="step-title">{{ $t('step1.ontologyGeneration') }}</span>
          </div>
          <div class="step-status">
            <span v-if="currentPhase > 0" class="badge success">{{ $t('step1.ontologyCompleted') }}</span>
            <span v-else-if="currentPhase === 0" class="badge processing">{{ $t('step1.ontologyGenerating') }}</span>
            <span v-else class="badge pending">{{ $t('step1.ontologyPending') }}</span>
          </div>
        </div>
        
        <div class="card-content">
          <p class="api-note">POST /api/graph/ontology/generate</p>
          <p class="description">
            {{ $t('step1.ontologyDesc') }}
          </p>

          <!-- Loading / Progress -->
          <div v-if="currentPhase === 0 && ontologyProgress" class="progress-section">
            <div class="spinner-sm"></div>
            <span>{{ ontologyProgress.message || $t('step1.analyzingDocs') }}</span>
          </div>

          <!-- Detail Overlay -->
          <div v-if="selectedOntologyItem" class="ontology-detail-overlay">
            <div class="detail-header">
               <div class="detail-title-group">
                  <span class="detail-type-badge">{{ selectedOntologyItem.itemType === 'entity' ? 'ENTITY' : 'RELATION' }}</span>
                  <span class="detail-name">{{ selectedOntologyItem.name }}</span>
               </div>
               <button class="close-btn" @click="selectedOntologyItem = null">×</button>
            </div>
            <div class="detail-body">
               <div class="detail-desc">{{ selectedOntologyItem.description }}</div>
               
               <!-- Attributes -->
               <div class="detail-section" v-if="selectedOntologyItem.attributes?.length">
                  <span class="section-label">ATTRIBUTES</span>
                  <div class="attr-list">
                     <div v-for="attr in selectedOntologyItem.attributes" :key="attr.name" class="attr-item">
                        <span class="attr-name">{{ attr.name }}</span>
                        <span class="attr-type">({{ attr.type }})</span>
                        <span class="attr-desc">{{ attr.description }}</span>
                     </div>
                  </div>
               </div>

               <!-- Examples (Entity) -->
               <div class="detail-section" v-if="selectedOntologyItem.examples?.length">
                  <span class="section-label">EXAMPLES</span>
                  <div class="example-list">
                     <span v-for="ex in selectedOntologyItem.examples" :key="ex" class="example-tag">{{ ex }}</span>
                  </div>
               </div>

               <!-- Source/Target (Relation) -->
               <div class="detail-section" v-if="selectedOntologyItem.source_targets?.length">
                  <span class="section-label">CONNECTIONS</span>
                  <div class="conn-list">
                     <div v-for="(conn, idx) in selectedOntologyItem.source_targets" :key="idx" class="conn-item">
                        <span class="conn-node">{{ conn.source }}</span>
                        <span class="conn-arrow">→</span>
                        <span class="conn-node">{{ conn.target }}</span>
                     </div>
                  </div>
               </div>
            </div>
          </div>

          <!-- Generated Entity Tags -->
          <div v-if="projectData?.ontology?.entity_types" class="tags-container" :class="{ 'dimmed': selectedOntologyItem }">
            <span class="tag-label">GENERATED ENTITY TYPES</span>
            <div class="tags-list">
              <span 
                v-for="entity in projectData.ontology.entity_types" 
                :key="entity.name" 
                class="entity-tag clickable"
                @click="selectOntologyItem(entity, 'entity')"
              >
                {{ entity.name }}
              </span>
            </div>
          </div>

          <!-- Generated Relation Tags -->
          <div v-if="projectData?.ontology?.edge_types" class="tags-container" :class="{ 'dimmed': selectedOntologyItem }">
            <span class="tag-label">GENERATED RELATION TYPES</span>
            <div class="tags-list">
              <span 
                v-for="rel in projectData.ontology.edge_types" 
                :key="rel.name" 
                class="entity-tag clickable"
                @click="selectOntologyItem(rel, 'relation')"
              >
                {{ rel.name }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 02: Graph Build -->
      <div class="step-card" :class="{ 'active': currentPhase === 1, 'completed': currentPhase > 1 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">02</span>
            <span class="step-title">{{ $t('step1.graphRagBuild') }}</span>
          </div>
          <div class="step-status">
            <span v-if="currentPhase > 1" class="badge success">{{ $t('step1.ontologyCompleted') }}</span>
            <span v-else-if="currentPhase === 1" class="badge processing">{{ buildProgress?.progress || 0 }}%</span>
            <span v-else class="badge pending">{{ $t('step1.ontologyPending') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="api-note">POST /api/graph/build</p>
          <p class="description">
            {{ $t('step1.graphRagDesc') }}
          </p>
          
          <!-- Stats Cards -->
          <div class="stats-grid">
            <div class="stat-card">
              <span class="stat-value">{{ graphStats.nodes }}</span>
              <span class="stat-label">{{ $t('step1.entityNodes') }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ graphStats.edges }}</span>
              <span class="stat-label">{{ $t('step1.relationEdges') }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ graphStats.types }}</span>
              <span class="stat-label">{{ $t('step1.schemaTypes') }}</span>
            </div>
          </div>

          <!-- Live build progress: 진행 메시지 + 소요시간 안내(행처럼 안 보이게) -->
          <div v-if="currentPhase === 1" class="progress-section">
            <div class="spinner-sm"></div>
            <span>{{ buildProgress?.message || $t('step1.graphRagBuilding') }}</span>
          </div>
          <p v-if="currentPhase === 1" class="build-note">{{ $t('step1.graphRagBuildNote') }}</p>
        </div>
      </div>

      <!-- Step 03: Complete -->
      <div class="step-card" :class="{ 'active': currentPhase === 2, 'completed': currentPhase >= 2 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">03</span>
            <span class="step-title">{{ $t('step1.buildComplete') }}</span>
          </div>
          <div class="step-status">
            <span v-if="currentPhase >= 2" class="badge accent">{{ $t('step1.inProgress') }}</span>
          </div>
        </div>
        
        <div class="card-content">
          <p class="api-note">POST /api/simulation/create</p>
          <p class="description">{{ $t('step1.buildCompleteDesc') }}</p>
          <button 
            class="action-btn" 
            :disabled="currentPhase < 2 || creatingSimulation"
            @click="handleEnterEnvSetup"
          >
            <span v-if="creatingSimulation" class="spinner-sm"></span>
            {{ creatingSimulation ? $t('step1.creating') : $t('step1.enterEnvSetup') + ' ➝' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Bottom Info / Logs -->
    <div class="system-logs">
      <div class="log-header">
        <span class="log-title">SYSTEM DASHBOARD</span>
        <span class="log-id">{{ projectData?.project_id || 'NO_PROJECT' }}</span>
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
import { computed, ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { createSimulation } from '../api/simulation'

const router = useRouter()
const { t } = useI18n({ useScope: 'global' })

const props = defineProps({
  currentPhase: { type: Number, default: 0 },
  projectData: Object,
  ontologyProgress: Object,
  buildProgress: Object,
  graphData: Object,
  systemLogs: { type: Array, default: () => [] }
})

defineEmits(['next-step'])

const selectedOntologyItem = ref(null)
const logContent = ref(null)
const creatingSimulation = ref(false)

//  -  simulation 
const handleEnterEnvSetup = async () => {
  if (!props.projectData?.project_id || !props.projectData?.graph_id) {
    console.error('')
    return
  }
  
  creatingSimulation.value = true
  
  try {
    const res = await createSimulation({
      project_id: props.projectData.project_id,
      graph_id: props.projectData.graph_id,
      enable_twitter: true,
      enable_reddit: true
    })
    
    if (res.success && res.data?.simulation_id) {
      //  simulation 
      router.push({
        name: 'Simulation',
        params: { simulationId: res.data.simulation_id }
      })
    } else {
      console.error(':', res.error)
      alert(t('step1.createSimulationFailed', { error: res.error || t('common.unknownError') }))
    }
  } catch (err) {
    console.error(':', err)
    alert(t('step1.createSimulationException', { error: err.message }))
  } finally {
    creatingSimulation.value = false
  }
}

const selectOntologyItem = (item, type) => {
  selectedOntologyItem.value = { ...item, itemType: type }
}

const graphStats = computed(() => {
  // 빌드 중엔 폴링 증분 카운트(buildProgress.node_count/edge_count = task.progress_detail)를,
  // 완료 후엔 전체 graphData 를 표시한다. 둘 중 큰 값으로 안전하게(구 백엔드=progress_detail 없음 → 0 폴백).
  const g = props.graphData || {}
  const bp = props.buildProgress || {}
  const gNodes = g.node_count ?? g.nodes?.length ?? 0
  const gEdges = g.edge_count ?? g.edges?.length ?? 0
  const nodes = Math.max(Number(gNodes) || 0, Number(bp.node_count) || 0)
  const edges = Math.max(Number(gEdges) || 0, Number(bp.edge_count) || 0)
  const types = props.projectData?.ontology?.entity_types?.length || 0
  return { nodes, edges, types }
})

const formatDate = (dateStr) => {
  if (!dateStr) return '--:--:--'
  const d = new Date(dateStr)
  return d.toLocaleTimeString('en-US', { hour12: false }) + '.' + d.getMilliseconds()
}

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
/* ===== 덱(deck) = 빌드 원장(ledger) =====
 * 스테이지가 주 캔버스가 됐으므로 이 패널은 "큰 카드 3장"이 아니라
 * 상태 칩 + 요약이 붙은 행(row) 묶음으로 압축한다.
 * 덱이 전폭이 되는 band 모드(≤1180)에서는 auto-fit 으로 2열까지 펼친다.
 * 색은 --wm-* 토큰만 쓴다(표면·배지 색 일부는 전역 정본이 !important 로 지정).
 */
.workbench-panel {
  height: 100%;
  background: var(--wm-bg);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

.scroll-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  align-content: start;
  gap: 12px;
}

/* 원장 행 */
.step-card {
  background: var(--wm-surface);
  border-radius: var(--wm-radius-md);
  padding: 13px 15px;
  box-shadow: var(--wm-shadow-1);
  border: 1px solid var(--wm-border);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  position: relative; /* For absolute overlay */
  align-self: start;
}

.step-card.active {
  border-color: var(--wm-accent-border);
  box-shadow: inset 3px 0 var(--wm-accent), var(--wm-shadow-2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 9px;
}

.step-info {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
}

.step-num {
  font-family: var(--wm-mono);
  font-size: 11px;
  font-weight: 700;
  color: var(--wm-text-dim);
  padding: 3px 7px;
  border-radius: var(--wm-radius-sm);
  background: var(--wm-surface-2);
  flex-shrink: 0;
}

.step-card.active .step-num,
.step-card.completed .step-num {
  color: var(--wm-accent-text);
  background: var(--wm-accent-soft);
}

.step-title {
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.01em;
  color: var(--wm-text);
}

.badge {
  font-size: 9px;
  padding: 3px 7px;
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-sm);
  font-family: var(--wm-mono);
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  white-space: nowrap;
}

.badge.success,
.badge.processing,
.badge.accent {
  background: var(--wm-accent-soft);
  color: var(--wm-accent-text);
  border-color: var(--wm-accent-border);
}

.badge.pending { background: var(--wm-surface-2); color: var(--wm-text-dim); }

.api-note {
  font-family: var(--wm-mono);
  font-size: 9px;
  color: var(--wm-text-dim);
  letter-spacing: 0.02em;
  margin: 0 0 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.description {
  font-size: 12px;
  color: var(--wm-text-muted);
  line-height: 1.55;
  margin: 0 0 12px;
}

/* 진행 중이 아닌 행은 요약만 남긴다(현재 행은 전문 유지) */
.step-card:not(.active) .description {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Step 01 Tags */
.tags-container {
  margin-top: 10px;
  transition: opacity 0.3s;
}

.tags-container.dimmed {
    opacity: 0.3;
    pointer-events: none;
}

.tag-label {
  display: block;
  font-family: var(--wm-mono);
  font-size: 9px;
  letter-spacing: 0.08em;
  color: var(--wm-text-dim);
  margin-bottom: 7px;
  font-weight: 700;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.entity-tag {
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border);
  padding: 3px 8px;
  border-radius: var(--wm-radius-sm);
  font-size: 10px;
  color: var(--wm-text-muted);
  font-family: var(--wm-mono);
  transition: all 0.2s;
}

.entity-tag.clickable {
    cursor: pointer;
}

.entity-tag.clickable:hover {
    background: var(--wm-accent-soft);
    border-color: var(--wm-accent-border);
    color: var(--wm-accent-text);
}

/* Ontology Detail Overlay */
.ontology-detail-overlay {
    position: absolute;
    top: 48px;
    left: 14px;
    right: 14px;
    bottom: 14px;
    background: var(--wm-surface);
    backdrop-filter: blur(4px);
    z-index: 10;
    border: 1px solid var(--wm-border);
    box-shadow: var(--wm-shadow-2);
    border-radius: var(--wm-radius-md);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }

.detail-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 13px;
    border-bottom: 1px solid var(--wm-border);
    background: var(--wm-surface-2);
}

.detail-title-group {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
}

.detail-type-badge {
    font-size: 8px;
    font-weight: 700;
    letter-spacing: 0.06em;
    color: var(--wm-on-accent);
    background: var(--wm-accent);
    padding: 2px 6px;
    border-radius: var(--wm-radius-sm);
    text-transform: uppercase;
    flex-shrink: 0;
}

.detail-name {
    font-size: 13px;
    font-weight: 700;
    color: var(--wm-text);
    font-family: var(--wm-mono);
    overflow: hidden;
    text-overflow: ellipsis;
}

.close-btn {
    background: none;
    border: none;
    font-size: 18px;
    color: var(--wm-text-dim);
    cursor: pointer;
    line-height: 1;
}

.close-btn:hover {
    color: var(--wm-text);
}

.detail-body {
    flex: 1;
    overflow-y: auto;
    padding: 14px;
}

.detail-desc {
    font-size: 12px;
    color: var(--wm-text-muted);
    line-height: 1.55;
    margin-bottom: 14px;
    padding-bottom: 11px;
    border-bottom: 1px dashed var(--wm-border-soft);
}

.detail-section {
    margin-bottom: 14px;
}

.section-label {
    display: block;
    font-family: var(--wm-mono);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--wm-text-dim);
    margin-bottom: 7px;
}

.attr-list, .conn-list {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.attr-item {
    font-size: 11px;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: baseline;
    padding: 5px 7px;
    background: var(--wm-surface-2);
    border-radius: var(--wm-radius-sm);
}

.attr-name {
    font-family: var(--wm-mono);
    font-weight: 600;
    color: var(--wm-text);
}

.attr-type {
    color: var(--wm-text-dim);
    font-size: 10px;
}

.attr-desc {
    color: var(--wm-text-muted);
    flex: 1;
    min-width: 150px;
}

.example-list {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.example-tag {
    font-size: 10px;
    background: var(--wm-surface-2);
    border: 1px solid var(--wm-border);
    padding: 3px 8px;
    border-radius: var(--wm-radius-pill);
    color: var(--wm-text-muted);
}

.conn-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 10px;
    padding: 5px 7px;
    background: var(--wm-surface-2);
    border-radius: var(--wm-radius-sm);
    font-family: var(--wm-mono);
}

.conn-node {
    font-weight: 600;
    color: var(--wm-text);
}

.conn-arrow {
    color: var(--wm-accent-text);
}

/* Step 02 Stats — 원장 한 줄에 붙는 수치 묶음 */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border-soft);
  padding: 10px 12px;
  border-radius: var(--wm-radius-sm);
}

.stat-card {
  text-align: center;
  min-width: 0;
}

.stat-value {
  display: block;
  font-size: 17px;
  font-weight: 700;
  color: var(--wm-text);
  font-family: var(--wm-mono);
  line-height: 1.2;
}

.stat-label {
  font-size: 8.5px;
  color: var(--wm-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 3px;
  display: block;
}

/* Step 03 Button */
.action-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: var(--wm-accent);
  color: var(--wm-on-accent);
  border: 1px solid var(--wm-accent);
  padding: 12px;
  border-radius: var(--wm-radius-sm);
  font-family: var(--wm-font);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover:not(:disabled) {
  background: var(--wm-accent-hover);
}

.action-btn:disabled {
  background: var(--wm-surface-2);
  border-color: var(--wm-border);
  color: var(--wm-text-dim);
  cursor: not-allowed;
}

.progress-section {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 12px;
  color: var(--wm-accent-text);
  margin-bottom: 10px;
  margin-top: 10px;
}

.build-note {
  font-size: 11px;
  color: var(--wm-text-dim);
  line-height: 1.5;
  margin-top: 4px;
}

.spinner-sm {
  width: 13px;
  height: 13px;
  border: 2px solid var(--wm-border);
  border-top-color: var(--wm-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* ===== 로그 독 — 덱 마지막 자식으로 in-flow(오버레이 금지) ===== */
.system-logs {
  background: var(--wm-stage);
  color: var(--wm-text-muted);
  padding: 10px 14px;
  font-family: var(--wm-mono);
  border-top: 1px solid var(--wm-border);
  flex-shrink: 0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  border-bottom: 1px solid var(--wm-border);
  padding-bottom: 7px;
  margin-bottom: 7px;
  font-size: 9px;
  letter-spacing: 0.06em;
  color: var(--wm-text-dim);
}

.log-id {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
  height: auto;
  max-height: 108px;
  overflow-y: auto;
  padding-right: 4px;
}

.log-content::-webkit-scrollbar {
  width: 4px;
}

.log-content::-webkit-scrollbar-thumb {
  background: var(--wm-border-strong);
  border-radius: 2px;
}

.log-line {
  font-size: 10.5px;
  display: flex;
  gap: 10px;
  line-height: 1.5;
}

.log-time {
  color: var(--wm-text-dim);
  min-width: 70px;
}

.log-msg {
  color: var(--wm-text-muted);
  word-break: break-all;
}

@media (max-width: 1180px) {
  .scroll-container {
    gap: 10px;
  }

  .log-content {
    max-height: 88px;
  }
}
</style>
