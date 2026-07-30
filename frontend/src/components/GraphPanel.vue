<template>
  <div class="graph-panel">
    <div class="panel-header">
      <!-- 스테이지 HUD: 제목 + 세계 규모(노드/엣지) — 문구는 기존 i18n 키 재사용 -->
      <div class="header-lead">
        <span class="panel-title">{{ $t('graph.panelTitle') }}</span>
        <div v-if="graphData" class="stage-hud">
          <span class="hud-chip">
            <span class="hud-value">{{ nodeCount }}</span>
            <span class="hud-label">{{ $t('step1.entityNodes') }}</span>
          </span>
          <span class="hud-chip">
            <span class="hud-value">{{ edgeCount }}</span>
            <span class="hud-label">{{ $t('step1.relationEdges') }}</span>
          </span>
        </div>
      </div>
      <!--  (Internal Top Right) -->
      <div class="header-tools">
        <button class="tool-btn" @click="$emit('refresh')" :disabled="loading" :title="$t('graph.refreshGraph')">
          <span class="icon-refresh" :class="{ 'spinning': loading }">↻</span>
          <span class="btn-text">Refresh</span>
        </button>
        <button class="tool-btn" @click="$emit('toggle-maximize')" :title="$t('graph.toggleMaximize')">
          <span class="icon-maximize">⛶</span>
        </button>
      </div>
    </div>
    
    <div class="graph-container" ref="graphContainer">
      <!--  -->
      <div v-if="graphData" class="graph-view">
        <svg ref="graphSvg" class="graph-svg"></svg>
        
        <!-- / -->
        <div v-if="currentPhase === 1 || isSimulating" class="graph-building-hint">
          <div class="memory-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="memory-icon">
              <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 4.44-4.04z" />
              <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-4.44-4.04z" />
            </svg>
          </div>
          {{ isSimulating ? $t('graph.graphMemoryRealtime') : $t('graph.realtimeUpdating') }}
        </div>
        
        <!--  -->
        <div v-if="showSimulationFinishedHint" class="graph-building-hint finished-hint">
          <div class="hint-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="hint-icon">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          </div>
          <span class="hint-text">{{ $t('graph.pendingContentHint') }}</span>
          <button class="hint-close-btn" @click="dismissFinishedHint" :title="$t('graph.closeHint')">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        
        <!-- / -->
        <div v-if="selectedItem" class="detail-panel">
          <div class="detail-panel-header">
            <span class="detail-title">{{ selectedItem.type === 'node' ? $t('graph.nodeDetails') : $t('graph.relationship') }}</span>
            <span v-if="selectedItem.type === 'node'" class="detail-type-badge" :style="{ background: selectedItem.color, color: 'var(--wm-on-accent)' }">
              {{ selectedItem.entityType }}
            </span>
            <button class="detail-close" @click="closeDetailPanel">×</button>
          </div>
          
          <!--  -->
          <div v-if="selectedItem.type === 'node'" class="detail-content">
            <div class="detail-row">
              <span class="detail-label">Name:</span>
              <span class="detail-value">{{ selectedItem.data.name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">UUID:</span>
              <span class="detail-value uuid-text">{{ selectedItem.data.uuid }}</span>
            </div>
            <div class="detail-row" v-if="selectedItem.data.created_at">
              <span class="detail-label">Created:</span>
              <span class="detail-value">{{ formatDateTime(selectedItem.data.created_at) }}</span>
            </div>
            
            <!-- Properties -->
            <div class="detail-section" v-if="selectedItem.data.attributes && Object.keys(selectedItem.data.attributes).length > 0">
              <div class="section-title">Properties:</div>
              <div class="properties-list">
                <div v-for="(value, key) in selectedItem.data.attributes" :key="key" class="property-item">
                  <span class="property-key">{{ key }}:</span>
                  <span class="property-value">{{ value || 'None' }}</span>
                </div>
              </div>
            </div>
            
            <!-- Summary -->
            <div class="detail-section" v-if="selectedItem.data.summary">
              <div class="section-title">Summary:</div>
              <div class="summary-text">{{ selectedItem.data.summary }}</div>
            </div>
            
            <!-- Labels -->
            <div class="detail-section" v-if="selectedItem.data.labels && selectedItem.data.labels.length > 0">
              <div class="section-title">Labels:</div>
              <div class="labels-list">
                <span v-for="label in selectedItem.data.labels" :key="label" class="label-tag">
                  {{ label }}
                </span>
              </div>
            </div>
          </div>
          
          <!--  -->
          <div v-else class="detail-content">
            <!--  -->
            <template v-if="selectedItem.data.isSelfLoopGroup">
              <div class="edge-relation-header self-loop-header">
                {{ selectedItem.data.source_name }} - Self Relations
                <span class="self-loop-count">{{ selectedItem.data.selfLoopCount }} items</span>
              </div>
              
              <div class="self-loop-list">
                <div 
                  v-for="(loop, idx) in selectedItem.data.selfLoopEdges" 
                  :key="loop.uuid || idx" 
                  class="self-loop-item"
                  :class="{ expanded: expandedSelfLoops.has(loop.uuid || idx) }"
                >
                  <div 
                    class="self-loop-item-header"
                    @click="toggleSelfLoop(loop.uuid || idx)"
                  >
                    <span class="self-loop-index">#{{ idx + 1 }}</span>
                    <span class="self-loop-name">{{ loop.name || loop.fact_type || 'RELATED' }}</span>
                    <span class="self-loop-toggle">{{ expandedSelfLoops.has(loop.uuid || idx) ? '−' : '+' }}</span>
                  </div>
                  
                  <div class="self-loop-item-content" v-show="expandedSelfLoops.has(loop.uuid || idx)">
                    <div class="detail-row" v-if="loop.uuid">
                      <span class="detail-label">UUID:</span>
                      <span class="detail-value uuid-text">{{ loop.uuid }}</span>
                    </div>
                    <div class="detail-row" v-if="loop.fact">
                      <span class="detail-label">Fact:</span>
                      <span class="detail-value fact-text">{{ loop.fact }}</span>
                    </div>
                    <div class="detail-row" v-if="loop.fact_type">
                      <span class="detail-label">Type:</span>
                      <span class="detail-value">{{ loop.fact_type }}</span>
                    </div>
                    <div class="detail-row" v-if="loop.created_at">
                      <span class="detail-label">Created:</span>
                      <span class="detail-value">{{ formatDateTime(loop.created_at) }}</span>
                    </div>
                    <div v-if="loop.episodes && loop.episodes.length > 0" class="self-loop-episodes">
                      <span class="detail-label">Episodes:</span>
                      <div class="episodes-list compact">
                        <span v-for="ep in loop.episodes" :key="ep" class="episode-tag small">{{ ep }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>
            
            <!--  -->
            <template v-else>
              <div class="edge-relation-header">
                {{ selectedItem.data.source_name }} → {{ selectedItem.data.name || 'RELATED_TO' }} → {{ selectedItem.data.target_name }}
              </div>
              
              <div class="detail-row">
                <span class="detail-label">UUID:</span>
                <span class="detail-value uuid-text">{{ selectedItem.data.uuid }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Label:</span>
                <span class="detail-value">{{ selectedItem.data.name || 'RELATED_TO' }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Type:</span>
                <span class="detail-value">{{ selectedItem.data.fact_type || 'Unknown' }}</span>
              </div>
              <div class="detail-row" v-if="selectedItem.data.fact">
                <span class="detail-label">Fact:</span>
                <span class="detail-value fact-text">{{ selectedItem.data.fact }}</span>
              </div>
              
              <!-- Episodes -->
              <div class="detail-section" v-if="selectedItem.data.episodes && selectedItem.data.episodes.length > 0">
                <div class="section-title">Episodes:</div>
                <div class="episodes-list">
                  <span v-for="ep in selectedItem.data.episodes" :key="ep" class="episode-tag">
                    {{ ep }}
                  </span>
                </div>
              </div>
              
              <div class="detail-row" v-if="selectedItem.data.created_at">
                <span class="detail-label">Created:</span>
                <span class="detail-value">{{ formatDateTime(selectedItem.data.created_at) }}</span>
              </div>
              <div class="detail-row" v-if="selectedItem.data.valid_at">
                <span class="detail-label">Valid From:</span>
                <span class="detail-value">{{ formatDateTime(selectedItem.data.valid_at) }}</span>
              </div>
            </template>
          </div>
        </div>
      </div>
      
      <!--  -->
      <div v-else-if="loading" class="graph-state">
        <div class="loading-spinner"></div>
        <p>{{ $t('graph.graphDataLoading') }}</p>
      </div>
      
      <!-- / -->
      <div v-else class="graph-state">
        <div class="empty-icon">❖</div>
        <p class="empty-text">{{ $t('graph.waitingOntology') }}</p>
      </div>
    </div>

    <!--  (Bottom Left) -->
    <div v-if="graphData && entityTypes.length" class="graph-legend">
      <span class="legend-title">Entity Types</span>
      <div class="legend-items">
        <div class="legend-item" v-for="type in entityTypes" :key="type.name">
          <span class="legend-dot" :style="{ background: type.color }"></span>
          <span class="legend-label">{{ type.name }}</span>
        </div>
      </div>
    </div>
    
    <!--  -->
    <div v-if="graphData" class="edge-labels-toggle">
      <label class="toggle-switch">
        <input type="checkbox" v-model="showEdgeLabels" />
        <span class="slider"></span>
      </label>
      <span class="toggle-label">Show Edge Labels</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  graphData: Object,
  loading: Boolean,
  currentPhase: Number,
  isSimulating: Boolean
})

const emit = defineEmits(['refresh', 'toggle-maximize'])

const graphContainer = ref(null)
const graphSvg = ref(null)
const selectedItem = ref(null)
const showEdgeLabels = ref(true) // 
const expandedSelfLoops = ref(new Set()) // 
const showSimulationFinishedHint = ref(false) // 
const wasSimulating = ref(false) // 

const dismissFinishedHint = () => {
  showSimulationFinishedHint.value = false
}

//  isSimulating ，
watch(() => props.isSimulating, (newValue, oldValue) => {
  if (wasSimulating.value && !newValue) {
    // ，
    showSimulationFinishedHint.value = true
  }
  wasSimulating.value = newValue
}, { immediate: true })

// /
const toggleSelfLoop = (id) => {
  const newSet = new Set(expandedSelfLoops.value)
  if (newSet.has(id)) {
    newSet.delete(id)
  } else {
    newSet.add(id)
  }
  expandedSelfLoops.value = newSet
}

// 스테이지 규모(HUD). 백엔드가 count 를 주면 그것을, 없으면 배열 길이를 쓴다.
const nodeCount = computed(() => props.graphData?.node_count ?? props.graphData?.nodes?.length ?? 0)
const edgeCount = computed(() => props.graphData?.edge_count ?? props.graphData?.edges?.length ?? 0)

// 범주형 팔레트 정본은 --wm-cat-1..10 (market-world.css). 인덱스 순서 = 기존 타입→색 대응 보존.
// var() 문자열을 그대로 쓰면 부모 테마 전환 시 재렌더 없이 색이 따라온다.
const CAT_COLORS = [
  'var(--wm-cat-1)', 'var(--wm-cat-2)', 'var(--wm-cat-3)', 'var(--wm-cat-4)', 'var(--wm-cat-5)',
  'var(--wm-cat-6)', 'var(--wm-cat-7)', 'var(--wm-cat-8)', 'var(--wm-cat-9)', 'var(--wm-cat-10)'
]

const entityTypes = computed(() => {
  if (!props.graphData?.nodes) return []
  const typeMap = {}
  const colors = CAT_COLORS

  props.graphData.nodes.forEach(node => {
    const type = node.labels?.find(l => l !== 'Entity') || 'Entity'
    if (!typeMap[type]) {
      typeMap[type] = { name: type, count: 0, color: colors[Object.keys(typeMap).length % colors.length] }
    }
    typeMap[type].count++
  })
  return Object.values(typeMap)
})

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true 
    })
  } catch {
    return dateStr
  }
}

const closeDetailPanel = () => {
  selectedItem.value = null
  expandedSelfLoops.value = new Set() // 
}

let currentSimulation = null
let linkLabelsRef = null
let linkLabelBgRef = null

const renderGraph = () => {
  if (!graphSvg.value || !props.graphData) return
  
  if (currentSimulation) {
    currentSimulation.stop()
  }
  
  const container = graphContainer.value
  const width = container.clientWidth
  const height = container.clientHeight
  
  const svg = d3.select(graphSvg.value)
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
    
  svg.selectAll('*').remove()
  
  const nodesData = props.graphData.nodes || []
  const edgesData = props.graphData.edges || []
  
  if (nodesData.length === 0) return

  // Prep data
  const nodeMap = {}
  nodesData.forEach(n => nodeMap[n.uuid] = n)
  
  const nodes = nodesData.map(n => ({
    id: n.uuid,
    name: n.name || 'Unnamed',
    type: n.labels?.find(l => l !== 'Entity') || 'Entity',
    rawData: n
  }))
  
  const nodeIds = new Set(nodes.map(n => n.id))
  
  // ，
  const edgePairCount = {}
  const selfLoopEdges = {} // 
  const tempEdges = edgesData
    .filter(e => nodeIds.has(e.source_node_uuid) && nodeIds.has(e.target_node_uuid))
  
  // ，
  tempEdges.forEach(e => {
    if (e.source_node_uuid === e.target_node_uuid) {
      //  - 
      if (!selfLoopEdges[e.source_node_uuid]) {
        selfLoopEdges[e.source_node_uuid] = []
      }
      selfLoopEdges[e.source_node_uuid].push({
        ...e,
        source_name: nodeMap[e.source_node_uuid]?.name,
        target_name: nodeMap[e.target_node_uuid]?.name
      })
    } else {
      const pairKey = [e.source_node_uuid, e.target_node_uuid].sort().join('_')
      edgePairCount[pairKey] = (edgePairCount[pairKey] || 0) + 1
    }
  })
  
  const edgePairIndex = {}
  const processedSelfLoopNodes = new Set() // 
  
  const edges = []
  
  tempEdges.forEach(e => {
    const isSelfLoop = e.source_node_uuid === e.target_node_uuid
    
    if (isSelfLoop) {
      //  - 
      if (processedSelfLoopNodes.has(e.source_node_uuid)) {
        return // ，
      }
      processedSelfLoopNodes.add(e.source_node_uuid)
      
      const allSelfLoops = selfLoopEdges[e.source_node_uuid]
      const nodeName = nodeMap[e.source_node_uuid]?.name || 'Unknown'
      
      edges.push({
        source: e.source_node_uuid,
        target: e.target_node_uuid,
        type: 'SELF_LOOP',
        name: `Self Relations (${allSelfLoops.length})`,
        curvature: 0,
        isSelfLoop: true,
        rawData: {
          isSelfLoopGroup: true,
          source_name: nodeName,
          target_name: nodeName,
          selfLoopCount: allSelfLoops.length,
          selfLoopEdges: allSelfLoops // 
        }
      })
      return
    }
    
    const pairKey = [e.source_node_uuid, e.target_node_uuid].sort().join('_')
    const totalCount = edgePairCount[pairKey]
    const currentIndex = edgePairIndex[pairKey] || 0
    edgePairIndex[pairKey] = currentIndex + 1
    
    // （UUID < UUID）
    const isReversed = e.source_node_uuid > e.target_node_uuid
    
    // ：，
    let curvature = 0
    if (totalCount > 1) {
      // ，
      // ，
      const curvatureRange = Math.min(1.2, 0.6 + totalCount * 0.15)
      curvature = ((currentIndex / (totalCount - 1)) - 0.5) * curvatureRange * 2
      
      // ，
      // ，
      if (isReversed) {
        curvature = -curvature
      }
    }
    
    edges.push({
      source: e.source_node_uuid,
      target: e.target_node_uuid,
      type: e.fact_type || e.name || 'RELATED',
      name: e.name || e.fact_type || 'RELATED',
      curvature,
      isSelfLoop: false,
      pairIndex: currentIndex,
      pairTotal: totalCount,
      rawData: {
        ...e,
        source_name: nodeMap[e.source_node_uuid]?.name,
        target_name: nodeMap[e.target_node_uuid]?.name
      }
    })
  })
    
  // Color scale
  const colorMap = {}
  entityTypes.value.forEach(t => colorMap[t.name] = t.color)
  const getColor = (type) => colorMap[type] || 'var(--wm-text-dim)'

  // ===== 레이아웃을 스테이지 경계로 구속한다 =====
  // 스테이지는 배치 모드에 따라 약 1090×844(side) ~ 1016×215(band) 까지 변한다.
  // 고정 파라미터(링크 150 · 충돌 66)는 짧은 띠에서 노드를 컨테이너 밖으로 밀어내
  // 잘림을 만들었다. 크롬(상단 HUD · 하단 범례/토글)과 라벨 폭을 뺀 가용 박스를
  // 실제 컨테이너 크기에서 파생하고, tick 에서 좌표를 그 박스 안으로 접는다
  // (초기 렌더 · 리사이즈 · 토글 재배치 · 드래그 전부 같은 규칙을 통과한다).
  const NODE_R = 10
  const clampTo = (v, lo, hi) => (v < lo ? lo : (v > hi ? hi : v))
  const chromeTop = Math.min(50, height * 0.22)     // 상단 HUD 바
  const chromeBottom = Math.min(46, height * 0.22)  // 하단 범례 · 엣지라벨 토글
  const chromeX = Math.min(28, width * 0.06)
  const labelRoom = Math.min(70, width * 0.12)      // 라벨은 노드 오른쪽으로 뻗는다(dx 14 + 8자)
  const box = {
    x0: chromeX + NODE_R,
    x1: Math.max(chromeX + NODE_R + 1, width - chromeX - NODE_R - labelRoom),
    y0: chromeTop + NODE_R,
    y1: Math.max(chromeTop + NODE_R + 1, height - chromeBottom - NODE_R),
  }
  const boxW = box.x1 - box.x0
  const boxH = box.y1 - box.y0
  const boxCx = (box.x0 + box.x1) / 2
  const boxCy = (box.y0 + box.y1) / 2
  // 노드 1개가 쓸 수 있는 정사각 한 변 ÷ 기존 기본 링크 거리(150). 좁을 때만 줄인다
  // → 넓은 폭에서는 fit === 1 이라 기존 배치가 그대로다(회귀 방지).
  const fit = Math.min(1, Math.sqrt((boxW * boxH) / nodes.length) / 150)
  // 박스가 한 축으로 납작하면(밴드) 그 축의 되당김을 키운다 — clamp 에만 맡기면 경계에 쌓인다.
  // 박스 비율이 2배 이내면 1 이라 넓은 폭에서는 기존 강도(0.04)가 유지된다.
  const pullX = Math.min(6, Math.max(1, boxH / boxW / 2))
  const pullY = Math.min(6, Math.max(1, boxW / boxH / 2))

  // Simulation -
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(d => {
      //  150， 40
      const baseDistance = 150
      const edgeCount = d.pairTotal || 1
      return (baseDistance + (edgeCount - 1) * 50) * fit
    }))
    .force('charge', d3.forceManyBody().strength(-400 * fit))
    .force('center', d3.forceCenter(boxCx, boxCy))
    // 라벨이 노드 오른쪽으로 뻗으므로 충돌 반경을 라벨 폭까지 넓힌다(라벨 겹침 완화)
    .force('collide', d3.forceCollide(66 * fit))
    // ，
    .force('x', d3.forceX(boxCx).strength(0.04 * pullX))
    .force('y', d3.forceY(boxCy).strength(0.04 * pullY))
  
  currentSimulation = simulation

  const g = svg.append('g')
  
  // Zoom
  svg.call(d3.zoom().extent([[0, 0], [width, height]]).scaleExtent([0.1, 4]).on('zoom', (event) => {
    g.attr('transform', event.transform)
  }))

  // Links -  path 
  const linkGroup = g.append('g').attr('class', 'links')
  
  const getLinkPath = (d) => {
    const sx = d.source.x, sy = d.source.y
    const tx = d.target.x, ty = d.target.y
    
    if (d.isSelfLoop) {
      // ：
      const loopRadius = 30
      // ，
      const x1 = sx + 8  // 
      const y1 = sy - 4
      const x2 = sx + 8  // 
      const y2 = sy + 4
      // （sweep-flag=1 ）
      return `M${x1},${y1} A${loopRadius},${loopRadius} 0 1,1 ${x2},${y2}`
    }
    
    if (d.curvature === 0) {
      return `M${sx},${sy} L${tx},${ty}`
    }
    
    //  - 
    const dx = tx - sx, dy = ty - sy
    const dist = Math.sqrt(dx * dx + dy * dy)
    // 두 노드가 한 점에 겹칠 수 있다(초기 tick 의 경계 clamp · 같은 모서리로 드래그 ·
    // 컨테이너 크기 0). dist 가 0 이면 -dy/dist 가 NaN 이 되어 d 속성 자체가 깨지므로
    // 직선으로 폴백한다 — 겹친 동안은 길이 0 이고, 떨어지는 즉시 곡선으로 돌아온다.
    if (!(dist > 1e-6)) {
      return `M${sx},${sy} L${tx},${ty}`
    }
    // ，，
    // ，
    const pairTotal = d.pairTotal || 1
    const offsetRatio = 0.25 + pairTotal * 0.05 // 25%，5%
    const baseOffset = Math.max(35, dist * offsetRatio)
    const offsetX = -dy / dist * d.curvature * baseOffset
    const offsetY = dx / dist * d.curvature * baseOffset
    const cx = (sx + tx) / 2 + offsetX
    const cy = (sy + ty) / 2 + offsetY
    
    return `M${sx},${sy} Q${cx},${cy} ${tx},${ty}`
  }
  
  // (설명 생략)
  const getLinkMidpoint = (d) => {
    const sx = d.source.x, sy = d.source.y
    const tx = d.target.x, ty = d.target.y
    
    if (d.isSelfLoop) {
      // ：
      return { x: sx + 70, y: sy }
    }
    
    if (d.curvature === 0) {
      return { x: (sx + tx) / 2, y: (sy + ty) / 2 }
    }
    
    //  t=0.5
    const dx = tx - sx, dy = ty - sy
    const dist = Math.sqrt(dx * dx + dy * dy)
    // getLinkPath 와 같은 이유 — 겹친 노드에서 NaN 좌표(x/y)가 나오지 않게 중점으로 폴백한다.
    if (!(dist > 1e-6)) {
      return { x: (sx + tx) / 2, y: (sy + ty) / 2 }
    }
    const pairTotal = d.pairTotal || 1
    const offsetRatio = 0.25 + pairTotal * 0.05
    const baseOffset = Math.max(35, dist * offsetRatio)
    const offsetX = -dy / dist * d.curvature * baseOffset
    const offsetY = dx / dist * d.curvature * baseOffset
    const cx = (sx + tx) / 2 + offsetX
    const cy = (sy + ty) / 2 + offsetY
    
    //  B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2, t=0.5
    const midX = 0.25 * sx + 0.5 * cx + 0.25 * tx
    const midY = 0.25 * sy + 0.5 * cy + 0.25 * ty
    
    return { x: midX, y: midY }
  }
  
  const link = linkGroup.selectAll('path')
    .data(edges)
    .enter().append('path')
    .style('stroke', 'var(--wm-edge)')
    .attr('stroke-width', 1.5)
    .attr('fill', 'none')
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      event.stopPropagation()
      resetPaint()
      d3.select(event.target).style('stroke', 'var(--wm-edge-strong)').attr('stroke-width', 3)

      selectedItem.value = {
        type: 'edge',
        data: d.rawData
      }
    })

  // Link labels background ()
  const linkLabelBg = linkGroup.selectAll('rect')
    .data(edges)
    .enter().append('rect')
    .style('fill', 'var(--wm-surface)')
    .style('stroke', 'var(--wm-border)')
    .attr('rx', 3)
    .attr('ry', 3)
    .style('cursor', 'pointer')
    .style('pointer-events', 'all')
    .style('display', showEdgeLabels.value ? 'block' : 'none')
    .on('click', (event, d) => {
      event.stopPropagation()
      resetPaint()
      link.filter(l => l === d).style('stroke', 'var(--wm-edge-strong)').attr('stroke-width', 3)
      d3.select(event.target).style('fill', 'var(--wm-accent-soft)').style('stroke', 'var(--wm-accent-border)')

      selectedItem.value = {
        type: 'edge',
        data: d.rawData
      }
    })

  // Link labels
  const linkLabels = linkGroup.selectAll('text')
    .data(edges)
    .enter().append('text')
    .text(d => d.name)
    .attr('font-size', '9px')
    .style('fill', 'var(--wm-text-muted)')
    .attr('text-anchor', 'middle')
    .attr('dominant-baseline', 'middle')
    .style('cursor', 'pointer')
    .style('pointer-events', 'all')
    .style('font-family', 'var(--wm-mono)')
    .style('display', showEdgeLabels.value ? 'block' : 'none')
    .on('click', (event, d) => {
      event.stopPropagation()
      resetPaint()
      link.filter(l => l === d).style('stroke', 'var(--wm-edge-strong)').attr('stroke-width', 3)
      d3.select(event.target).style('fill', 'var(--wm-edge-strong)')

      selectedItem.value = {
        type: 'edge',
        data: d.rawData
      }
    })
  
  linkLabelsRef = linkLabels
  linkLabelBgRef = linkLabelBg

  // Nodes group
  const nodeGroup = g.append('g').attr('class', 'nodes')
  
  // Node circles
  const node = nodeGroup.selectAll('circle')
    .data(nodes)
    .enter().append('circle')
    .attr('r', 10)
    .style('fill', d => getColor(d.type))
    .style('stroke', 'var(--wm-node-stroke)')
    .attr('stroke-width', 2.5)
    .style('cursor', 'pointer')
    .call(d3.drag()
      .on('start', (event, d) => {
        // ，(설명 생략)
        d.fx = d.x
        d.fy = d.y
        d._dragStartX = event.x
        d._dragStartY = event.y
        d._isDragging = false
      })
      .on('drag', (event, d) => {
        // (설명 생략)
        const dx = event.x - d._dragStartX
        const dy = event.y - d._dragStartY
        const distance = Math.sqrt(dx * dx + dy * dy)
        
        if (!d._isDragging && distance > 3) {
          // ，
          d._isDragging = true
          simulation.alphaTarget(0.3).restart()
        }
        
        if (d._isDragging) {
          d.fx = event.x
          d.fy = event.y
        }
      })
      .on('end', (event, d) => {
        if (d._isDragging) {
          simulation.alphaTarget(0)
        }
        d.fx = null
        d.fy = null
        d._isDragging = false
      })
    )
    .on('click', (event, d) => {
      event.stopPropagation()
      resetPaint()
      d3.select(event.target).style('stroke', 'var(--wm-accent)').attr('stroke-width', 4)
      link.filter(l => l.source.id === d.id || l.target.id === d.id)
        .style('stroke', 'var(--wm-edge-strong)')
        .attr('stroke-width', 2.5)

      selectedItem.value = {
        type: 'node',
        data: d.rawData,
        entityType: d.type,
        color: getColor(d.type)
      }
    })
    .on('mouseenter', (event, d) => {
      if (!selectedItem.value || selectedItem.value.data?.uuid !== d.rawData.uuid) {
        d3.select(event.target).style('stroke', 'var(--wm-border-strong)').attr('stroke-width', 3)
      }
    })
    .on('mouseleave', (event, d) => {
      if (!selectedItem.value || selectedItem.value.data?.uuid !== d.rawData.uuid) {
        d3.select(event.target).style('stroke', 'var(--wm-node-stroke)').attr('stroke-width', 2.5)
      }
    })

  // Node Labels — 스테이지 배경색 후광(paint-order)으로 격자·엣지 위에서도 읽히게 한다
  const nodeLabels = nodeGroup.selectAll('text')
    .data(nodes)
    .enter().append('text')
    .text(d => d.name.length > 8 ? d.name.substring(0, 8) + '…' : d.name)
    .attr('font-size', '11px')
    .style('fill', 'var(--wm-text)')
    .style('stroke', 'var(--wm-stage)')
    .style('stroke-width', '3px')
    .style('stroke-linejoin', 'round')
    .style('paint-order', 'stroke')
    .attr('font-weight', '500')
    .attr('dx', 14)
    .attr('dy', 4)
    .style('pointer-events', 'none')
    .style('font-family', 'var(--wm-font)')

  // 선택 해제 시 원래 도색으로 되돌린다(엣지·라벨·노드 한 곳에서 관리)
  const resetPaint = () => {
    linkGroup.selectAll('path').style('stroke', 'var(--wm-edge)').attr('stroke-width', 1.5)
    linkLabelBg.style('fill', 'var(--wm-surface)').style('stroke', 'var(--wm-border)')
    linkLabels.style('fill', 'var(--wm-text-muted)')
    node.style('stroke', 'var(--wm-node-stroke)').attr('stroke-width', 2.5)
  }

  simulation.on('tick', () => {
    // 경계 구속 — force 결과를 스테이지 박스 안으로 접는다. 엣지·라벨은 이 좌표를 읽으므로
    // 노드·엣지·라벨이 함께 안쪽에 남는다. 드래그(fx/fy)도 같은 한계를 넘지 못한다.
    nodes.forEach(d => {
      d.x = clampTo(d.x, box.x0, box.x1)
      d.y = clampTo(d.y, box.y0, box.y1)
    })

    link.attr('d', d => getLinkPath(d))
    
    // （，）
    linkLabels.each(function(d) {
      const mid = getLinkMidpoint(d)
      d3.select(this)
        .attr('x', mid.x)
        .attr('y', mid.y)
        .attr('transform', '') // ，
    })
    
    linkLabelBg.each(function(d, i) {
      const mid = getLinkMidpoint(d)
      const textEl = linkLabels.nodes()[i]
      const bbox = textEl.getBBox()
      d3.select(this)
        .attr('x', mid.x - bbox.width / 2 - 4)
        .attr('y', mid.y - bbox.height / 2 - 2)
        .attr('width', bbox.width + 8)
        .attr('height', bbox.height + 4)
        .attr('transform', '') // 
    })

    node
      .attr('cx', d => d.x)
      .attr('cy', d => d.y)

    nodeLabels
      .attr('x', d => d.x)
      .attr('y', d => d.y)
  })
  
  svg.on('click', () => {
    selectedItem.value = null
    resetPaint()
  })
}

watch(() => props.graphData, () => {
  nextTick(renderGraph)
}, { deep: true })

watch(showEdgeLabels, (newVal) => {
  if (linkLabelsRef) {
    linkLabelsRef.style('display', newVal ? 'block' : 'none')
  }
  if (linkLabelBgRef) {
    linkLabelBgRef.style('display', newVal ? 'block' : 'none')
  }
})

// 스테이지 크기는 창 크기뿐 아니라 배치 모드(side/band/전체화면)·접힘으로도 바뀐다.
// 컨테이너 크기를 직접 관찰해 다시 그린다(연속 변화는 디바운스로 한 번만).
let resizeObserver = null
let resizeTimer = null

const scheduleRender = () => {
  if (resizeTimer) clearTimeout(resizeTimer)
  resizeTimer = setTimeout(() => {
    const el = graphContainer.value
    if (!el || el.clientWidth < 40 || el.clientHeight < 40) return
    nextTick(renderGraph)
  }, 160)
}

const handleResize = () => {
  scheduleRender()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  if (graphContainer.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(scheduleRender)
    resizeObserver.observe(graphContainer.value)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (resizeTimer) clearTimeout(resizeTimer)
  if (currentSimulation) {
    currentSimulation.stop()
  }
})
</script>

<style scoped>
/* ===== 스테이지(stage) =====
 * 이 컴포넌트는 곁다리 서랍이 아니라 앱의 주 캔버스다.
 * 크롬 배치: 상단 HUD 바(제목·규모·도구) / 하단 좌 범례 · 하단 우 엣지라벨 토글 /
 *            우측 상세 시트(상·하 크롬을 침범하지 않도록 top·bottom 을 비워둔다).
 * 색은 --wm-* 토큰만 쓴다. 떠 있는 패널의 표면색은 전역 정본(market-world.css)이
 * !important 로 지정하므로 여기서는 기하와 전역이 안 다루는 색만 지정한다.
 */
.graph-panel {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: var(--wm-stage);
  background-image: radial-gradient(var(--wm-grid) 1.5px, transparent 1.5px);
  background-size: 24px 24px;
  overflow: hidden;
}

/* ===== 상단 HUD 바 ===== */
.panel-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 9px 14px;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--wm-border);
  background: linear-gradient(to bottom, var(--wm-scrim), transparent);
  pointer-events: none;
}

.header-lead {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
  overflow: hidden;
  pointer-events: auto;
}

.panel-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--wm-text);
  letter-spacing: 0.02em;
  white-space: nowrap;
  pointer-events: auto;
}

/* 세계 규모 칩 — 스테이지가 스스로 크기를 말한다 */
.stage-hud {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.hud-chip {
  display: inline-flex;
  align-items: baseline;
  gap: 5px;
  padding: 3px 9px;
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-pill);
  background: var(--wm-surface-2);
  white-space: nowrap;
}

.hud-value {
  font-family: var(--wm-mono);
  font-size: 12px;
  font-weight: 700;
  color: var(--wm-accent-text);
}

.hud-label {
  font-size: 10px;
  color: var(--wm-text-muted);
}

.header-tools {
  pointer-events: auto;
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

.tool-btn {
  height: 28px;
  padding: 0 10px;
  border: 1px solid var(--wm-border);
  background: var(--wm-surface-2);
  border-radius: var(--wm-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  color: var(--wm-text-muted);
  transition: all 0.2s;
  box-shadow: var(--wm-shadow-1);
  font-size: 12px;
}

.tool-btn:hover {
  background: var(--wm-accent-soft);
  color: var(--wm-accent-text);
  border-color: var(--wm-accent-border);
}

.tool-btn .btn-text {
  font-size: 11px;
  font-family: var(--wm-mono);
  letter-spacing: 0.03em;
}

.icon-refresh.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.graph-container {
  width: 100%;
  height: 100%;
}

.graph-view, .graph-svg {
  width: 100%;
  height: 100%;
  display: block;
}

.graph-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: var(--wm-text-dim);
  font-size: 13px;
  padding: 0 16px;
}

.empty-icon {
  font-size: 40px;
  margin-bottom: 10px;
  opacity: 0.25;
  color: var(--wm-accent-text);
}

.empty-text {
  margin: 0;
}

/* ===== 하단 좌: Entity Types 범례 ===== */
.graph-legend {
  position: absolute;
  bottom: 12px;
  left: 12px;
  max-width: min(46%, 320px);
  max-height: 40%;
  overflow: auto;
  padding: 9px 12px;
  border: 1px solid var(--wm-border);
  z-index: 10;
}

.legend-title {
  display: block;
  font-family: var(--wm-mono);
  font-size: 9px;
  font-weight: 700;
  color: var(--wm-text-dim);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--wm-text-muted);
}

.legend-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-label {
  white-space: nowrap;
}

/* ===== 하단 우: 엣지 라벨 토글 (상세 시트와 겹치지 않게 하단으로 내렸다) ===== */
.edge-labels-toggle {
  position: absolute;
  bottom: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 6px 12px;
  border-radius: var(--wm-radius-pill);
  border: 1px solid var(--wm-border);
  box-shadow: var(--wm-shadow-1);
  z-index: 10;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 34px;
  height: 18px;
  flex-shrink: 0;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--wm-surface-3);
  border-radius: var(--wm-radius-pill);
  transition: 0.3s;
}

.slider:before {
  position: absolute;
  content: "";
  height: 12px;
  width: 12px;
  left: 3px;
  bottom: 3px;
  background-color: var(--wm-text);
  border-radius: 50%;
  transition: 0.3s;
}

/* 전역 임베드 시트가 .slider 배경을 !important 로 고정하므로 활성 상태는 여기서 되찾는다 */
input:checked + .slider {
  background-color: var(--wm-accent) !important;
}

input:checked + .slider:before {
  transform: translateX(16px);
  background-color: var(--wm-on-accent);
}

.toggle-label {
  font-size: 11px;
  color: var(--wm-text-muted);
  white-space: nowrap;
}

/* ===== 우측 상세 시트 ===== */
.detail-panel {
  position: absolute;
  top: 54px;
  right: 12px;
  bottom: 54px;
  width: clamp(240px, 32%, 340px);
  border: 1px solid var(--wm-border);
  box-shadow: var(--wm-shadow-2);
  overflow: hidden;
  font-family: var(--wm-font);
  font-size: 13px;
  z-index: 20;
  display: flex;
  flex-direction: column;
}

.detail-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 11px 14px;
  border-bottom: 1px solid var(--wm-border);
  flex-shrink: 0;
}

.detail-title {
  font-weight: 600;
  color: var(--wm-text);
  font-size: 13px;
}

.detail-type-badge {
  padding: 3px 9px;
  border-radius: var(--wm-radius-pill);
  font-size: 10px;
  font-weight: 600;
  margin-left: auto;
  margin-right: 10px;
}

.detail-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--wm-text-dim);
  line-height: 1;
  padding: 0;
  transition: color 0.2s;
}

.detail-close:hover {
  color: var(--wm-text);
}

.detail-content {
  padding: 14px;
  overflow-y: auto;
  flex: 1;
}

.detail-row {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.detail-label {
  color: var(--wm-text-muted);
  font-size: 11px;
  font-weight: 500;
  min-width: 74px;
}

.detail-value {
  color: var(--wm-text);
  flex: 1;
  word-break: break-word;
}

.detail-value.uuid-text {
  font-family: var(--wm-mono);
  font-size: 11px;
  color: var(--wm-text-muted);
}

.detail-value.fact-text {
  line-height: 1.5;
  color: var(--wm-text-muted);
}

.detail-section {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--wm-border-soft);
}

.section-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--wm-text-muted);
  margin-bottom: 9px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.properties-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.property-item {
  display: flex;
  gap: 8px;
}

.property-key {
  color: var(--wm-text-muted);
  font-weight: 500;
  min-width: 86px;
}

.property-value {
  color: var(--wm-text);
  flex: 1;
}

.summary-text {
  line-height: 1.6;
  color: var(--wm-text-muted);
  font-size: 12px;
}

.labels-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.label-tag {
  display: inline-block;
  padding: 3px 10px;
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-pill);
  font-size: 11px;
  color: var(--wm-text-muted);
}

.episodes-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.episode-tag {
  display: inline-block;
  padding: 5px 9px;
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-sm);
  font-family: var(--wm-mono);
  font-size: 10px;
  color: var(--wm-text-muted);
  word-break: break-all;
}

/* Edge relation header */
.edge-relation-header {
  padding: 11px 12px;
  border: 1px solid var(--wm-border);
  margin-bottom: 14px;
  font-size: 12px;
  font-weight: 500;
  color: var(--wm-text);
  line-height: 1.5;
  word-break: break-word;
}

/* ===== 상태 힌트(하단 중앙) ===== */
.graph-building-hint {
  position: absolute;
  bottom: 58px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--wm-scrim);
  backdrop-filter: blur(8px);
  color: var(--wm-text);
  padding: 8px 16px;
  border-radius: var(--wm-radius-pill);
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 9px;
  box-shadow: var(--wm-shadow-2);
  border: 1px solid var(--wm-border);
  font-weight: 500;
  letter-spacing: 0.02em;
  max-width: calc(100% - 32px);
  z-index: 30;
}

.memory-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  animation: breathe 2s ease-in-out infinite;
}

.memory-icon {
  width: 16px;
  height: 16px;
  color: var(--wm-accent-text);
}

@keyframes breathe {
  0%, 100% { opacity: 0.7; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.15); }
}

.graph-building-hint.finished-hint {
  background: var(--wm-scrim);
  border: 1px solid var(--wm-border);
}

.finished-hint .hint-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.finished-hint .hint-icon {
  width: 16px;
  height: 16px;
  color: var(--wm-warn);
}

.finished-hint .hint-text {
  flex: 1;
  min-width: 0;
}

.hint-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: var(--wm-surface-3);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  color: var(--wm-text-muted);
  transition: all 0.2s;
  margin-left: 6px;
  flex-shrink: 0;
}

.hint-close-btn:hover {
  background: var(--wm-accent-soft);
  color: var(--wm-accent-text);
}

/* Loading spinner */
.loading-spinner {
  width: 34px;
  height: 34px;
  border: 3px solid var(--wm-border);
  border-top-color: var(--wm-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 14px;
}

/* ===== 자기참조 관계(self-loop) — 보조 강조 --wm-alt 계열 ===== */
.self-loop-header {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--wm-alt-soft);
  border: 1px solid var(--wm-border);
}

.self-loop-count {
  margin-left: auto;
  font-size: 11px;
  color: var(--wm-text-muted);
  background: var(--wm-surface-2);
  padding: 2px 8px;
  border-radius: var(--wm-radius-pill);
}

.self-loop-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.self-loop-item {
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-sm);
}

.self-loop-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 11px;
  background: var(--wm-surface-2);
  cursor: pointer;
  transition: background 0.2s;
}

.self-loop-item-header:hover {
  background: var(--wm-surface-3);
}

.self-loop-item.expanded .self-loop-item-header {
  background: var(--wm-surface-3);
}

.self-loop-index {
  font-family: var(--wm-mono);
  font-size: 10px;
  font-weight: 600;
  color: var(--wm-text-muted);
  background: var(--wm-surface-3);
  padding: 2px 6px;
  border-radius: var(--wm-radius-sm);
}

.self-loop-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--wm-text);
  flex: 1;
}

.self-loop-toggle {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--wm-text-muted);
  background: var(--wm-surface-3);
  border-radius: var(--wm-radius-sm);
  transition: all 0.2s;
}

.self-loop-item.expanded .self-loop-toggle {
  color: var(--wm-accent-text);
  background: var(--wm-accent-soft);
}

.self-loop-item-content {
  padding: 11px;
  border-top: 1px solid var(--wm-border-soft);
}

.self-loop-item-content .detail-row {
  margin-bottom: 8px;
}

.self-loop-item-content .detail-label {
  font-size: 11px;
  min-width: 58px;
}

.self-loop-item-content .detail-value {
  font-size: 12px;
}

.self-loop-episodes {
  margin-top: 8px;
}

.episodes-list.compact {
  flex-direction: row;
  flex-wrap: wrap;
  gap: 4px;
}

.episode-tag.small {
  padding: 3px 6px;
  font-size: 9px;
}

/* ===== band 모드(≤1180 = 임베드 패널): 스테이지가 낮고 넓은 띠가 된다 ===== */
@media (max-width: 1180px) {
  .panel-header {
    padding: 7px 10px;
    gap: 8px;
  }

  .header-lead {
    gap: 10px;
  }

  .tool-btn {
    height: 26px;
    padding: 0 8px;
  }

  .graph-legend {
    bottom: 10px;
    left: 10px;
    max-width: min(52%, 300px);
    max-height: 44%;
    padding: 7px 10px;
  }

  .graph-legend .legend-items {
    gap: 5px 10px;
  }

  .edge-labels-toggle {
    bottom: 10px;
    right: 10px;
    padding: 5px 10px;
  }

  .detail-panel {
    top: 46px;
    bottom: 46px;
    right: 10px;
    width: clamp(220px, 34%, 300px);
  }

  .graph-building-hint {
    bottom: 50px;
    font-size: 11px;
    padding: 7px 13px;
  }

  .empty-icon {
    font-size: 28px;
    margin-bottom: 6px;
  }

  .graph-state {
    font-size: 12px;
  }
}

@media (max-width: 720px) {
  .hud-label,
  .toggle-label {
    display: none;
  }

  .tool-btn .btn-text {
    display: none;
  }
}
</style>
