# World Model 전면 재설계 — 정본 스펙 (1단계 산출물)

작성 2026-07-30 · 대상 저장소 `world-model` (Vue 3 + Vite, `frontend/`)
1단계에서 **토큰 체계·전역 시트만** 구현했다. 화면 구현은 2단계(에이전트 3인) 소관.
**이 문서가 2단계의 유일한 정본이다. 여기서 벗어난 매핑을 하면 통일이 깨진다.**

---

## 0. 실측 현황 (2단계는 재조사하지 말 것)

| 라우트 | 뷰 | 조합 | 백엔드 데이터 유무(2026-07-30) |
|---|---|---|---|
| `/` | Home.vue | HistoryDatabase | 아카이브 비어 있음(`backend/uploads/simulations` 0건) |
| `/process/:projectId` | MainView.vue (`name: 'Process'`) | GraphPanel + Step1GraphBuild + Step2EnvSetup | `proj_c3035fef5ea9` 정상(graph_completed, 노드 7·엣지 8) |
| `/simulation/:simulationId` | SimulationView.vue | GraphPanel + Step2EnvSetup | **시뮬레이션 레코드 0건 → ERROR 상태만 재현 가능** |
| `/simulation/:simulationId/start` | SimulationRunView.vue | GraphPanel + Step3Simulation + Step4 | 동일 — 빈 상태만 재현 가능 |
| `/report/:reportId` | ReportView.vue | GraphPanel + Step4Report | `report_914df91bcab0` 완결본 정상 |
| `/interaction/:reportId` | InteractionView.vue | GraphPanel + Step5Interaction | 동일 리포트로 정상 |

- 백엔드 기동: `backend/.venv/Scripts/python.exe run.py` (Flask, 5001). 프론트 `cd frontend && npm run dev` (3000, vite proxy `/api`→5001).
- **`views/Process.vue`(2,030행) · `components/Step1TopicSetup.vue`(829행)는 어디서도 import 되지 않는 死코드다. 손대지 말고 삭제도 하지 말 것.**
- 임베드 폭: 메인 앱 `WorldModelModal.tsx` 는 모달 `max-w-[1600px] w-[95vw]` 과 패널(`asPanel`, 약 1080) 두 가지를 쓴다. **1080·1520 양쪽이 실사용 폭이다.**
- 부모가 보내는 테마는 `dark | light` 뿐이다(`contexts/ThemeContext.tsx` 의 `Theme` 타입). `ungdroo` 는 브리지에 남은 레거시 값 → light 로 근사.

---

## 1. 설계 논지 (design thesis)

1. **그래프는 곁다리 패널이 아니라 이 앱의 세계 그 자체다.** `GraphPanel` 은 이미 작동하는 5개 화면 전부에 들어 있었지만 우측 430px 서랍으로 취급돼, 사용자는 "세계를 만든다"가 아니라 "폼을 순서대로 채운다"를 경험했다. 캔버스를 **스테이지(stage)** 로 승격하고 단계 컨트롤을 **덱(deck)** 으로 재정의한다.
2. **단계는 없애지 않는다 — 화면이 아니라 상태로 바꾼다.** 그래프 없이 시뮬레이션이 불가능하고 시뮬레이션 없이 리포트가 불가능한 **실제 순서 의존**이 있다. 그래서 라우트·순서는 그대로 두고, 진행을 좌측 레일의 스파인(연결선+채움)과 상단 바의 선형 진행(`--wm-progress`)으로 표현한다.
3. **캔버스 비중은 화면마다 다르다.** 세계를 *만드는*(1) · *채우는*(2) · *돌리는*(3) 동안 스테이지는 상시 존재한다. *읽는*(4) · *묻는*(5) 동안은 긴 글과 대화가 주역이고 캔버스는 방해다 — 오버레이 시트로 물러난다. 이는 코드의 기존 기본값(`drawerMode`: side/side/side/hidden/hidden)과 일치하므로 로직과 싸우지 않는다.
4. **1080px에서 캔버스와 패널을 좌우로 나누는 건 실패한 접근이다.** 실측 결과 좌우 분할 시 스테이지 410px에 노드 라벨이 겹치고 잘렸다. 대안은 **band 모드** — 스테이지를 상단 전폭 띠(약 1016×300)로, 덱을 하단 전폭으로. 같은 화면적을 쓰면서 그래프의 가로폭이 2.5배가 된다.
5. **색은 하나의 의미 토큰 집합에서만 나온다.** `--c-*`/`--uf-*`/하드코딩 hex 세 계열이 서로 덮으며 싸우던 구조를 `--wm-*` 단일 정본 + 별칭으로 접었다. 강조색은 메인 앱과 동일한 에메랄드(`#1fcb6e` / `#05ad59`)다 — 인디고(`#6366f1`)는 부모 어디에도 근거가 없어 폐기한다.

---

## 2. 셸 구조와 배치 모드 (1단계에서 이미 구현·검증됨)

DOM 은 6개 뷰 공통이며 **변경하지 않는다**:

```
.uf-shell                       ← 뷰가 변형 클래스를 여기에 붙인다
  .uf-sidebar                   rail  (진행 레일, --wm-rail-w)
  .uf-main
    .uf-subheader               topbar (--wm-topbar-h, ::after 가 진행선)
    .uf-content-wrap
      .uf-content               DECK  (단계 컨트롤) ← DOM 1번째
      .uf-drawer                STAGE (GraphPanel) ← DOM 2번째
```

### 배치 모드 (`assets/layout.css`)

| 모드 | 조건 | 거동 | 실측 |
|---|---|---|---|
| side(기본·레거시) | 뷰폭 > 1180 & 변형 클래스 없음 | 덱 가변 좌 · 스테이지 고정 `--wm-stage-w`(=min(430px,38vw)) 우 | 1600폭: 덱 1086 / 스테이지 430 (기존과 동일) |
| side(스테이지 우위) | `.uf-shell--stage-lead` / `--balanced` | 덱 고정 `--wm-deck-w` 좌 · 스테이지가 남은 폭 전부 | 1600폭: 덱 380~500 / 스테이지 나머지 |
| side(덱 우위) | `.uf-shell--deck-lead` | 덱 가변 · 스테이지 `clamp(320px,34%,520px)` | — |
| **band** | **뷰폭 ≤ 1180 (임베드 패널 = 이 모드)** | `column-reverse` 로 스테이지가 위, 높이 `--wm-stage-band-h` | 1080폭: 스테이지 1016×301 · 덱 1016×583 |
| overlay | `.uf-shell.stage-overlay` | 스테이지가 덱 위 시트로 뜬다. >1180 우측 `min(760px,74%)`, ≤1180 하단 `min(76%,720px)`. 접힘 = `translate` 로 밀어냄 | 리포트·탐색용 |
| full | `.uf-shell.graph-fullscreen` (기존 로직) | 스테이지 단독, 덱 `display:none` | 검증됨 |

부가 훅:
- `.uf-drawer.is-empty` — `graphData` 가 없을 때 뷰가 붙인다. band 에서 띠 높이를 120~180px 로 줄여 **죽은 공간을 만들지 않는다**(정직한 빈 상태).
- `--wm-progress: 0~1` — 뷰가 `.uf-shell` 인라인 스타일로 지정. 상단 바 하단의 강조색 진행선 폭이 된다.

### 화면별 비중 (2단계가 뷰에 붙일 것)

| 라우트 | 셸 변형 클래스 | 기본 `drawerMode` | 근거 |
|---|---|---|---|
| `/process/:projectId` | `uf-shell--stage-lead` | side (유지) | 세계가 *생성되는* 화면. 그래프가 결과물 자체 |
| `/simulation/:simulationId` | `uf-shell--deck-lead` | side (유지) | Step2EnvSetup(2,585행) 설정이 작업 본체. 스테이지는 검증용 참조 |
| `/simulation/:simulationId/start` | `uf-shell--balanced` | side (유지) | 세계가 *움직이는* 유일한 화면. 스테이지가 공간을 벌 자격이 있다 |
| `/report/:reportId` | `uf-shell--deck-lead` + `stage-overlay` | hidden (유지) | 장문 독해. 캔버스가 본문 measure 를 깎으면 손해 |
| `/interaction/:reportId` | `uf-shell--deck-lead` + `stage-overlay` | hidden (유지) | 대화가 작업. 캔버스는 요청 시 근거로 소환 |

---

## 3. 화면별 레이아웃 스펙

공통 규칙 (전 워크벤치 화면):
- 레일: 슬롯 5개 유지. `data-label` 툴팁 문구는 i18n `main.stepNames` 그대로 — **새 문구 금지**. 완료=강조 테두리, 현재=강조 채움, 미도달=흐림.
- 상단 바: 좌 크럼(`World Model ▸ Step N ▸ 이름`), 우 상태 배지 + 스테이지 토글. **문구·DOM 변경 금지**, 스타일만.
- 로그 독: `.system-logs`(Step1/2/3) · `.console-logs`(Step4)는 **덱의 마지막 자식으로 in-flow**. `max-height: clamp(96px,18vh,180px)`(전역 시트가 이미 지정). 절대 위치 오버레이로 만들지 말 것.
- 덱 내부 좌우 여백은 `--wm-gutter`.
- band 모드에서 덱이 전폭(약 1016px)이 되므로, 기존에 1열이던 덱 내부 블록은 `repeat(auto-fit, minmax(320px,1fr))` 로 2열까지 펼 수 있다.

### R1 `/` Home — 세계 발사대
캔버스 비중 0 (그래프 없음: 이 시점엔 프로젝트가 존재하지 않으므로 가짜 그래프를 그리면 데이터 할루시네이션이다).
- 컨테이너 `max-width: 1180px`(1단계에서 1280→1180 조정 완료), 그리드 `minmax(0,1.4fr) minmax(340px,0.72fr)`.
- **Zone A 콜드오픈** (`grid-column: 1/-1`): 좌 hero 문구, 우 `entity-orbit`(장식). ≤1180 에서 orbit 은 하단 224px 띠로 내려간다.
  - 알려진 결함(2단계 처리): ≤1180 에서 `hero::before` 의 거대 텍스트와 orbit 이 같은 박스에 겹쳐 FED/MARKET 칩과 충돌한다. 좁은 폭에서는 `hero::before` 를 숨기거나 orbit 만 남길 것.
- **Zone B 컴포즈**: 좌열 = `.card`(시나리오 프롬프트), 우열 = `.time-config-card` + `.submit-wrap`. `flow-indicator` 는 Zone B 위 전폭 레일.
- **Zone C 아카이브**: `.history` + HistoryDatabase 전폭, 카드 `repeat(auto-fill, minmax(260px,1fr))`.
  - 결함(2단계 처리): 아카이브가 0건일 때 아무것도 안 나온다 → 기존 i18n `history.*` 키로 빈 상태를 표시할 것. **새 문구 작성 금지, 기존 키 재사용.**
- 1080: 1열. 1520: 2열.

### R2 `/process/:projectId` — 세계 생성
`uf-shell--stage-lead`.
- **스테이지 상시.** side: 덱 380~440 좌 / 스테이지 나머지. band: 스테이지 260~400 상단.
- 덱 = "빌드 원장(ledger)": Step1GraphBuild 의 3개 카드를 큰 카드에서 **상태 칩 + 한 줄 요약의 행(row)** 으로 압축. 노드/엣지/스키마 카운트는 스테이지 위 HUD(좌상단 오버레이 칩)로 올려도 좋다.
- 진행: `--wm-progress` = `(currentPhase+1)/3`. 레일 슬롯 01 활성.
- Step2 로 내부 전환(`currentStep===2`)될 때도 같은 셸 유지. 이때 `--wm-progress` = 1.

### R3 `/simulation/:simulationId` — 세계 객체 설정
`uf-shell--deck-lead`.
- 스테이지는 참조. `graphData` 없으면 `.uf-drawer.is-empty` 부여.
- 덱: 섹션 스택. band(전폭)에서는 2열 그리드 허용(프로필 카드·에이전트 카드가 대상).
- 결함(2단계 처리): 시뮬레이션 미존재 시 상태가 `ERROR` 로만 표시되고 복구 경로가 없다 → 기존 i18n 로그 키를 그대로 쓰되 덱 상단에 상태 배너를 둘 것.

### R4 `/simulation/:simulationId/start` — 상호작용 실행
`uf-shell--balanced`.
- 실행 중(`isSimulating`)에는 셸에 `is-running` 을 붙여 스테이지 그리드에 미세한 모션 + 상태 점 펄스(이미 `.uf-status.processing` 에 있음)를 준다.
- 덱: 상단 컨트롤 바(플랫폼 상태·통계) 고정 → 타임라인 스트림 스크롤 → 로그 독.
- band 에서 컨트롤 바는 `position: sticky; top: 0` 로 덱 상단에 붙인다.

### R5 `/report/:reportId` — 경로 분석 보고서
`uf-shell--deck-lead` + `stage-overlay`, 스테이지 기본 hidden(현행 유지).
- 덱 내부 2열: **본문(1fr, `max-width: min(72ch,100%)`)** + **에이전트 트레이스 레일(360px)**.
- ≤1180: 1열. 트레이스는 본문 아래로 내려가거나 기존 탭/토글 UI 로 접는다. **1080 실측에서 2열 유지 시 제목이 6줄로 깨진다 — 반드시 1열로.**
- 스테이지 토글을 누르면 오버레이 시트(우측 `min(760px,74%)`, 좁은 폭은 하단 76%). 본문 폭을 깎지 않는다.
- `--wm-progress` = 완료 섹션 / 전체 섹션.

### R6 `/interaction/:reportId` — 세계 탐색
`uf-shell--deck-lead` + `stage-overlay`, 스테이지 기본 hidden.
- 덱 내부 2열: 리포트(1fr, `max-width: min(68ch,100%)`) + 대화(480~560).
- ≤1180: **대화가 전폭**, 리포트는 기존 탭 필(`tab-pill`)로 접는다. 대화가 이 화면의 작업이다.
- 도구 카드 4장은 `repeat(auto-fit, minmax(240px,1fr))`.

---

## 4. 토큰 계약 (`--wm-*`)

정본 정의: `src/assets/market-world.css` (§1 dark = `:root`, §2 light = `html.waiker-light`, ungdroo).
부모 테마 전파 경로: `src/theme-bridge.js` 가 **이 집합 전체**를 `documentElement` 인라인으로 기록한다.
**새 색이 필요하면 (a) market-world.css 3블록, (b) theme-bridge.js 2팔레트에 같이 넣는다. 둘 중 하나만 넣으면 테마가 깨진다.**

### 4.1 배경 계층

| 토큰 | 의미 | dark | light | ungdroo | 사용 지침 |
|---|---|---|---|---|---|
| `--wm-bg` | 앱 바닥 | `#070a08` | `#f9fafb` | =light | 페이지·덱 배경. 메인 앱과 동일값 |
| `--wm-surface` | 패널·카드 1단 | `#0d120f` | `#ffffff` | =light | 카드/모달/드롭다운 |
| `--wm-surface-2` | 카드 안 블록 2단 | `#131a16` | `#f2f5f3` | =light | 입력창·칩·코드블록·인셋 |
| `--wm-surface-3` | hover/pressed 채움 | `#1b241e` | `#e8ece9` | =light | 상호작용 상태 채움, 트랙 |
| `--wm-stage` | 그래프 스테이지 우물 | `#040705` | `#fcfdfc` | =light | GraphPanel 캔버스·로그 독 |
| `--wm-chrome` | 셸 크롬 | `#050806` | `#ffffff` | =light | 레일·상단 바 |
| `--wm-chrome-active` | 크롬 선택/hover | `#13201a` | `#eaf4ee` | =light | 레일 슬롯 hover |

### 4.2 테두리 3단

| 토큰 | 의미 | dark | light | ungdroo | 지침 |
|---|---|---|---|---|---|
| `--wm-border` | 기본 헤어라인 | `#232e28` | `#dfe5e1` | =light | 카드·입력·구분선 기본 |
| `--wm-border-soft` | 내부 미세 구분 | `#161d19` | `#eef1ef` | =light | 카드 내부 dashed/dotted 분리 |
| `--wm-border-strong` | 강조/hover 테두리 | `#37483f` | `#b8c5bd` | =light | hover, 스크롤바 썸 |

### 4.3 텍스트 3단 + 반전

| 토큰 | 의미 | dark | light | ungdroo | 지침 |
|---|---|---|---|---|---|
| `--wm-text` | 본문·제목·값 | `#f3f4f6` | `#111827` | =light | 메인 앱과 동일값 |
| `--wm-text-muted` | 라벨·설명 | `#93a79c` | `#556158` | =light | 보조 설명, 2차 정보 |
| `--wm-text-dim` | 메타·타임스탬프·placeholder | `#5f7168` | `#8a958e` | =light | 3차 정보, 비활성 |
| `--wm-on-accent` | 강조 채움 위 텍스트 | `#04150c` | `#ffffff` | =light | **강조 솔리드 배경일 때만** |

### 4.4 강조 / 보조 강조

| 토큰 | 의미 | dark | light | ungdroo | 지침 |
|---|---|---|---|---|---|
| `--wm-accent` | 주 강조 | `#1fcb6e` | `#05ad59` | =light | 메인 앱 `--waiker-accent`(#1fcb6e)·Sidebar light(#05ad59) 기준 |
| `--wm-accent-hover` | 강조 hover | `#34d399` | `#048a47` | =light | 솔리드 버튼 hover |
| `--wm-accent-soft` | 강조 soft 채움 | `rgba(31,203,110,.14)` | `rgba(5,173,89,.10)` | =light | **soft 위 텍스트는 `--wm-accent`. `--wm-on-accent` 쓰면 안 읽힌다** |
| `--wm-accent-border` | 강조 테두리 | `rgba(31,203,110,.42)` | `rgba(5,173,89,.38)` | =light | soft 칩 테두리, focus |
| `--wm-alt` | 보조 강조(에이전트·도구·자기참조) | `#a78bfa` | `#7c3aed` | =light | 기존 보라(#7C3AED/#7B2D8E/#9b59b6) 자리 |
| `--wm-alt-soft` | 보조 soft | `rgba(167,139,250,.16)` | `rgba(124,58,237,.10)` | =light | |

### 4.5 양·음·경고·정보

| 토큰 | 의미 | dark | light | ungdroo |
|---|---|---|---|---|
| `--wm-pos` / `-soft` | 양(상승·성공) | `#2ee27f` / `rgba(46,226,127,.14)` | `#08a35a` / `rgba(8,163,90,.10)` | =light |
| `--wm-neg` / `-soft` | 음(하락·오류·삭제) | `#ff6b6b` / `rgba(255,107,107,.14)` | `#d92d20` / `rgba(217,45,32,.10)` | =light |
| `--wm-warn` / `-soft` | 경고·주의 | `#fbbf24` / `rgba(251,191,36,.14)` | `#b45309` / `rgba(180,83,9,.10)` | =light |
| `--wm-info` / `-soft` | 정보·진행·선택 하이라이트 | `#38bdf8` / `rgba(56,189,248,.14)` | `#0369a1` / `rgba(3,105,161,.10)` | =light |

`--wm-pos` 는 강조색과 **다른 값**이다. 상태 표시(성공/상승)에는 `pos`, 주 행동에는 `accent` 를 쓴다.

### 4.6 오버레이·그림자

| 토큰 | 의미 | dark | light | ungdroo |
|---|---|---|---|---|
| `--wm-overlay` | 모달 스크림 | `rgba(2,6,4,.82)` | `rgba(15,25,20,.42)` | =light |
| `--wm-scrim` | 스테이지 위 떠 있는 패널 배경(blur 동반) | `rgba(5,8,6,.72)` | `rgba(255,255,255,.86)` | =light |
| `--wm-shadow-1` | 낮은 고도(카드) | `0 1px 2px rgba(0,0,0,.5)` | `0 1px 2px rgba(15,25,20,.06)` | =light |
| `--wm-shadow-2` | 중간(드롭다운·hover) | `0 10px 30px rgba(0,0,0,.42)` | `0 8px 24px rgba(15,25,20,.08)` | =light |
| `--wm-shadow-3` | 높은(모달·오버레이 시트) | `0 28px 80px rgba(0,0,0,.6)` | `0 24px 64px rgba(15,25,20,.16)` | =light |
| `--wm-glow` | 강조 글로우 | `0 0 0 1px rgba(31,203,110,.35), 0 0 26px rgba(31,203,110,.18)` | `0 0 0 1px rgba(5,173,89,.28), 0 6px 20px rgba(5,173,89,.16)` | =light |

### 4.7 스테이지·차트 팔레트

| 토큰 | 의미 | dark | light |
|---|---|---|---|
| `--wm-grid` | 스테이지 격자선 | `rgba(120,152,138,.08)` | `rgba(13,26,19,.06)` |
| `--wm-edge` | 그래프 엣지 기본 | `#3d4f47` | `#b6c4bc` |
| `--wm-edge-strong` | 엣지 강조/hover | `#1fcb6e` | `#05ad59` |
| `--wm-node-stroke` | 노드 외곽선 | `#040705` | `#ffffff` |
| `--wm-cat-1..10` | 범주형(엔티티 타입) | `#4ecdc4 #ff8a5b #a78bfa #38bdf8 #fbbf24 #f472b6 #84cc16 #fb923c #22d3ee #c084fc` | `#0d9488 #ea580c #7c3aed #0369a1 #b45309 #be185d #4d7c0f #c2410c #0e7490 #7e22ce` |

`--wm-cat-*` 는 **순수 초록/순수 빨강을 피했다** — accent/pos/neg 의 의미와 섞이지 않게 하기 위함이다.
`GraphPanel.vue:286` 의 `colors` 배열을 `--wm-cat-1..10` 을 읽는 배열로 교체할 것(인덱스 순서 유지 = 기존 타입→색 대응 보존).

### 4.8 타이포·형태·기하

| 토큰 | 값 | 지침 |
|---|---|---|
| `--wm-font` | `"Pretendard","SUIT","Inter","Noto Sans KR",system-ui,sans-serif` | 본문 |
| `--wm-mono` | `"JetBrains Mono","IBM Plex Mono",Consolas,monospace` | ID·수치·로그·레일 번호 |
| `--wm-radius-sm/md/lg/pill` | `3px / 6px / 10px / 999px` | 칩·입력=sm, 카드=md, 모달=lg, 배지=pill |
| `--wm-rail-w` | `84px` (≤1180 `64px`) | 좌측 레일 |
| `--wm-topbar-h` | `56px` (≤720 `52px`) | 상단 바 |
| `--wm-stage-w` | `min(430px,38vw)` | side 기본 모드 스테이지 고정폭 |
| `--wm-deck-w` | `clamp(380px,30%,480px)` (변형 클래스가 재지정) | stage-lead/balanced 의 덱 고정폭 |
| `--wm-stage-band-h` | `clamp(240px,32vh,380px)` | band 모드 스테이지 띠 높이 |
| `--wm-gutter` | `clamp(16px,2vw,28px)` | 덱 내부 패딩·그리드 간격 |
| `--wm-logo-filter` | dark `grayscale(1) contrast(1.2) brightness(1.7)` / light `grayscale(1) contrast(1.05) brightness(.35)` | 컬러 로고 자산 중성화 |
| `--wm-progress` | `0~1` (뷰가 지정) | 상단 바 진행선 폭 |

### 4.9 레거시 별칭 (그대로 유지 — 지우지 말 것)

`market-world.css :root` 에서 재노출한다. 컴포넌트를 이관해도 별칭은 남긴다(死코드 `Process.vue` 가 참조).

| 레거시 | → | 레거시 | → |
|---|---|---|---|
| `--uf-bg` | `--wm-bg` | `--uf-accent-soft` | `--wm-accent-soft` |
| `--uf-surface` | `--wm-surface` | `--uf-border` | `--wm-border` |
| `--uf-sidebar-bg` | `--wm-chrome` | `--uf-border-light` | `--wm-border-soft` |
| `--uf-sidebar-active` | `--wm-chrome-active` | `--uf-green` | `--wm-pos` |
| `--uf-sidebar-text` | `--wm-text-dim` | `--uf-red` | `--wm-neg` |
| `--uf-sidebar-text-active` | `--wm-text` | `--uf-radius` / `-sm` | `--wm-radius-md` / `-sm` |
| `--uf-text` | `--wm-text` | `--uf-font` / `--uf-mono` | `--wm-font` / `--wm-mono` |
| `--uf-text-muted` | `--wm-text-muted` | `--uf-sidebar-w` | `--wm-rail-w` |
| `--uf-accent` | `--wm-accent` | `--uf-subheader-h` | `--wm-topbar-h` |
| `--uf-accent-hover` | `--wm-accent-hover` | `--uf-drawer-w` | `--wm-deck-w` |

Home 전용(`.home { ... !important }`, Home.vue scoped 선언을 덮기 위해 `!important` 필수):

| 레거시 | → | 레거시 | → |
|---|---|---|---|
| `--c-bg` | `--wm-bg` | `--c-accent-hover` | `--wm-accent-hover` |
| `--c-surface` | `--wm-surface` | `--c-accent-soft` | `--wm-accent-soft` |
| `--c-text` | `--wm-text` | `--c-navy` | `--wm-text` |
| `--c-text-muted` | `--wm-text-muted` | `--c-border` | `--wm-border` |
| `--c-text-dim` | `--wm-text-dim` | `--c-border-soft` | `--wm-surface-2` |
| `--c-accent` | `--wm-accent` | | |

`--c-border-soft` 는 Home 에서 **입력창/칩 배경**으로 쓰이므로 테두리가 아니라 `--wm-surface-2` 로 간다. Home.vue 의 `--c-*` 사용 77곳은 이 별칭으로 전부 살아 있다(실측 확인).

---

## 5. hex → 토큰 매핑 가이드 (2단계 필수 준수)

### 5.1 판정 순서 — **밝기가 아니라 역할로 정한다**
1. 그 hex 가 쓰인 **CSS 속성**을 본다: `background*` → 배경 계열, `border*`/`outline` → 테두리 계열, `color`/`fill`/`stroke` → 텍스트/그래픽 계열.
2. 배경이면 위치를 본다: 페이지=`--wm-bg`, 패널/카드=`--wm-surface`, 카드 안 블록·입력=`--wm-surface-2`, hover/pressed=`--wm-surface-3`, 그래프 캔버스·로그=`--wm-stage`, 레일/상단바=`--wm-chrome`.
3. 테두리면 단계를 본다: 기본=`--wm-border`, 카드 내부 미세 구분(dashed/dotted)=`--wm-border-soft`, hover/active=`--wm-border-strong`(단, 주 행동 요소면 `--wm-accent-border`).
4. 텍스트면 위계를 본다: 제목/값=`--wm-text`, 라벨/설명=`--wm-text-muted`, 메타/타임스탬프/placeholder/비활성=`--wm-text-dim`.
5. 의미색이면 의미로: 성공·상승=`--wm-pos`, 오류·하락·삭제=`--wm-neg`, 경고=`--wm-warn`, 정보·선택=`--wm-info`, 에이전트/도구=`--wm-alt`, 주 행동=`--wm-accent`.

### 5.2 계열별 일괄 매핑표

**A. 레거시 모노크롬** (GraphPanel · Step1GraphBuild · Step2EnvSetup · Step3Simulation · LanguageSwitcher)

| 원본 hex | 배경으로 쓰였을 때 | 테두리 | 텍스트 |
|---|---|---|---|
| `#FFF` `#FFFFFF` | `--wm-surface` | — | `--wm-on-accent`(강조 채움 위) / `--wm-text`(그 외) |
| `#FAFAFA` `#F9F9F9` `#F8F8F8` `#FAFBFC` | `--wm-surface` | — | — |
| `#F5F5F5` `#F0F0F0` `#F1F5F9` `#F8FAFC` | `--wm-surface-2` | — | — |
| `#EEEEEE` `#EEE` `#EAEAEA` `#E8E8E8` `#E5E5E5` `#E0E0E0` `#E2E8F0` | `--wm-surface-3` | `--wm-border` | — |
| `#DDD` `#D0D0D0` `#CCC` | `--wm-surface-3` | `--wm-border` | `--wm-text-dim` |
| `#BBB` `#AAA` `#999` `#888` | — | `--wm-border-strong` | `--wm-text-dim` |
| `#666` `#555` `#444` | — | — | `--wm-text-muted` |
| `#333` `#222` `#000` | `--wm-stage`(로그 패널) | `--wm-border` | `--wm-text` |

**B. Tailwind gray** (Step4Report · Step5Interaction · HistoryDatabase)

| 원본 hex | 배경 | 테두리 | 텍스트 |
|---|---|---|---|
| `#FFFFFF` | `--wm-surface` | — | `--wm-on-accent` / `--wm-text` |
| `#F9FAFB` | `--wm-bg` | — | — |
| `#F3F4F6` | `--wm-surface-2` | — | — |
| `#E5E7EB` | `--wm-surface-3` | `--wm-border` | — |
| `#D1D5DB` | — | `--wm-border` | `--wm-text-dim` |
| `#9CA3AF` `#94A3B8` | — | `--wm-border-strong` | `--wm-text-dim` |
| `#6B7280` `#64748B` `#4B5563` | — | `--wm-border-strong` | `--wm-text-muted` |
| `#374151` | `--wm-surface-3` | `--wm-border` | `--wm-text-muted` |
| `#1F2937` `#1E293B` `#111827` | `--wm-surface`(패널) / `--wm-stage`(로그) | `--wm-border-strong` | `--wm-text` |

**C. 의미·강조**

| 원본 hex | → |
|---|---|
| `#10B981` `#4CAF50` `#27ae60` `#1A936F` | `--wm-pos` (또는 주 행동이면 `--wm-accent`) |
| `#ECFDF5` `#E8F5E9` `#C8E6C9` `#A7F3D0` `#F1F8E9` | `--wm-pos-soft` |
| `#EF4444` `#C5283D` `#E91E63` `#FF4500` | `--wm-neg` |
| `#F59E0B` `#f39c12` `#FF5722` `#FF6B35` `#E9724C` | `--wm-warn` |
| `#3B82F6` `#3498db` `#004E89` | `--wm-info` |
| `#7C3AED` `#7B2D8E` `#9b59b6` | `--wm-alt` |
| `#6366F1` `#4F46E5` (구 인디고) | `--wm-accent` — **폐기색. 남기지 말 것** |
| `#b7f34a` `#cdfb78` (구 라임) | `--wm-accent` / `--wm-accent-hover` — **폐기색** |
| `#07100f` (라임 테마의 반전 텍스트) | `--wm-on-accent` |
| GraphPanel `colors[0..9]` | `--wm-cat-1..10` (인덱스 유지) |
| `rgba(0,0,0,α)` box-shadow | `--wm-shadow-1/2/3` (α·blur 크기로 등급 선택) |
| `rgba(255,255,255,.9x)` 떠 있는 패널 배경 | `--wm-scrim` (+ `backdrop-filter: blur()`) |
| `rgba(255,255,255,.0x~.1)` 다크용 미세 채움 | `--wm-surface-2` / `--wm-surface-3` |

### 5.3 애매할 때 규칙
1. **새 hex 를 만들지 않는다.** 맞는 토큰이 없으면 가장 가까운 역할 토큰을 쓰고 인수인계에 표시한다. 토큰을 임의로 추가하지 않는다(추가는 §4의 5곳 동시 수정을 요구한다).
2. **배경만 바꾸고 텍스트 색을 컴포넌트에 남기지 않는다.** 이 조합이 라이트에서 "흰 글씨가 사라지는" 결함의 원인이었다(실측: `.report-tag` · `.tab-pill.active` · 아바타류). **배경·텍스트는 항상 같은 규칙에서 한 쌍으로 지정한다.**
3. **`--wm-accent-soft` 위에는 절대 `--wm-on-accent` 를 쓰지 않는다.** 반드시 `--wm-accent`. (솔리드 `--wm-accent` 위에만 `--wm-on-accent`.)
4. 같은 hex가 한 파일에서 배경·테두리로 둘 다 쓰이면 **각각 다른 토큰으로 나눈다**. 일괄 치환 금지.
5. 스피너·진행 표시의 회전 세그먼트는 회색이 아니라 `--wm-accent`.
6. `mask-image`/`clip-path` 안의 `#000`·`black` 은 색이 아니라 알파 마스크다. 치환하지 않는다.
7. 컴포넌트를 토큰으로 이관하면 `theme-dark-overrides.css` 의 대응 규칙은 **무해한 중복**이 된다. 같은 커밋에서 해당 규칙 블록을 지워라(파일명·게이트는 유지).

---

## 6. 1단계에서 구현한 것 / 남긴 것

구현(전역만, 컴포넌트 미접촉):
- `src/assets/market-world.css` — 전면 재작성. `--wm-*` 정본 3테마 + `--uf-*`/`--c-*` 별칭 + Home 레이어 + 셸 질감 + 공용 표면. hex 는 토큰 정의 블록에만 존재.
- `src/assets/layout.css` — 토큰 선언 제거(정본 이관), 구조 전담. side/band/overlay/full 4모드 + 변형 클래스 3종 + `.is-empty` 훅 신설.
- `src/theme-dark-overrides.css` — 게이트를 `html.waiker-embed.waiker-dark` → `html.waiker-embed`(테마 무관)로. hex 516규칙 전량 토큰화(잔여 hex 0). 다크에서 흰색이 되던 버그(`.graph-legend`·`.panel-header`)와 라이트에서 사라지던 흰 텍스트(`.report-tag`·`.tab-pill.active`·아바타류) 수정.
- `src/App.vue` — `#app`·스크롤바·`:focus-visible` 토큰화.
- `src/theme-bridge.js` — dark/light/ungdroo 팔레트를 `--wm-*` 전체로 확장(13→54키). 인디고 하드코딩 글로우 주입 제거(토큰으로 대체). `waiker-embed`/`waiker-dark`/`waiker-light` 클래스 계약 유지 + `waiker-ungdroo` 추가.

2단계로 넘기는 결함(1단계 범위 밖 = 컴포넌트):
1. GraphPanel 노드 라벨이 다크에서 어두운 색이고 서로 겹친다. 엣지 라벨 칩도 하드코딩 흰색.
2. GraphPanel `colors` 배열 → `--wm-cat-*` 이관.
3. Home ≤1180 에서 `hero::before` 거대 텍스트와 orbit 충돌.
4. HistoryDatabase 0건일 때 빈 상태 표시 없음(기존 i18n 키 재사용).
5. 레일 하단 LanguageSwitcher 가 64px 레일에서 세로로 줄바꿈된다.
6. R5/R6 의 ≤1180 1열 전환(현재는 2열 유지로 제목이 6줄로 깨짐).
7. 각 뷰에 셸 변형 클래스 · `stage-overlay` · `.is-empty` · `--wm-progress` 부여.

절대 금지(재확인):
- 라우트 경로·파라미터, API 호출, 상태 로직, i18n **키**, 표시 **문구** 변경 금지.
- `views/Process.vue` · `components/Step1TopicSetup.vue` 수정·삭제 금지.
- 새 CSS 프레임워크/UI 라이브러리 금지. SFC `<style>` + CSS 변수 유지.
- 커밋·푸시 금지(사용자 지시 시에만).
- 검증은 `cd frontend && npm run build` 통과 + 다크/라이트 × 1080/1600 4조합 확인.

## 7. 스크린샷

- before: `.agents/world-model-redesign/before/` (standalone-1600-\*, embed1080-dark-\*, embed1080-light-\*)
- after(1단계): `.agents/world-model-redesign/after-tokens/` (동일 6라우트 × 3조합 + `interact-*` 토글/전체화면 검증)
