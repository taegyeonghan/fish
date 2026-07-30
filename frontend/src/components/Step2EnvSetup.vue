<template>
  <div class="env-setup-panel">
    <div class="scroll-container">
      <!-- Step 01:  -->
      <div class="step-card" :class="{ 'active': phase === 0, 'completed': phase > 0 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">01</span>
            <span class="step-title">{{ $t('step2.simInstanceInit') }}</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 0" class="badge success">{{ $t('common.completed') }}</span>
            <span v-else class="badge processing">{{ $t('step2.initializing') }}</span>
          </div>
        </div>
        
        <div class="card-content">
          <p class="api-note">POST /api/simulation/create</p>
          <p class="description">
            {{ $t('step2.simInstanceDesc') }}
          </p>

          <div v-if="simulationId" class="info-card">
            <div class="info-row">
              <span class="info-label">Project ID</span>
              <span class="info-value mono">{{ projectData?.project_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Graph ID</span>
              <span class="info-value mono">{{ projectData?.graph_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Simulation ID</span>
              <span class="info-value mono">{{ simulationId }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">Task ID</span>
              <span class="info-value mono">{{ taskId || $t('step2.asyncTaskDone') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 02:  Agent  -->
      <div class="step-card" :class="{ 'active': phase === 1, 'completed': phase > 1 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">02</span>
            <span class="step-title">{{ $t('step2.generateAgentPersona') }}</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 1" class="badge success">{{ $t('common.completed') }}</span>
            <span v-else-if="phase === 1" class="badge processing">{{ prepareProgress }}%</span>
            <span v-else class="badge pending">{{ $t('common.pending') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="api-note">POST /api/simulation/prepare</p>
          <p class="description">
            {{ $t('step2.generateAgentPersonaDesc') }}
          </p>

          <!-- Profiles Stats -->
          <div v-if="profiles.length > 0" class="stats-grid">
            <div class="stat-card">
              <span class="stat-value">{{ profiles.length }}</span>
              <span class="stat-label">{{ $t('step2.currentAgentCount') }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ expectedTotal || '-' }}</span>
              <span class="stat-label">{{ $t('step2.expectedAgentTotal') }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ totalTopicsCount }}</span>
              <span class="stat-label">{{ $t('step2.relatedTopicsCount') }}</span>
            </div>
          </div>

          <!-- Profiles List Preview -->
          <div v-if="profiles.length > 0" class="profiles-preview">
            <div class="preview-header">
              <span class="preview-title">{{ $t('step2.generatedAgentPersonas') }}</span>
            </div>
            <div class="profiles-list">
              <div 
                v-for="(profile, idx) in profiles" 
                :key="idx" 
                class="profile-card"
                @click="selectProfile(profile)"
              >
                <div class="profile-header">
                  <span class="profile-realname">{{ profile.username || 'Unknown' }}</span>
                  <span class="profile-username">@{{ profile.name || `agent_${idx}` }}</span>
                </div>
                <div class="profile-meta">
                  <span class="profile-profession">{{ profile.profession || $t('step2.unknownProfession') }}</span>
                </div>
                <p class="profile-bio">{{ profile.bio || $t('step2.noBio') }}</p>
                <div v-if="profile.interested_topics?.length" class="profile-topics">
                  <span 
                    v-for="topic in profile.interested_topics.slice(0, 3)" 
                    :key="topic" 
                    class="topic-tag"
                  >{{ topic }}</span>
                  <span v-if="profile.interested_topics.length > 3" class="topic-more">
                    +{{ profile.interested_topics.length - 3 }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 03:  -->
      <div class="step-card" :class="{ 'active': phase === 2, 'completed': phase > 2 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">03</span>
            <span class="step-title">{{ $t('step2.dualPlatformConfig') }}</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 2" class="badge success">{{ $t('common.completed') }}</span>
            <span v-else-if="phase === 2" class="badge processing">{{ $t('step2.generating') }}</span>
            <span v-else class="badge pending">{{ $t('common.pending') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="api-note">POST /api/simulation/prepare</p>
          <p class="description">
            {{ $t('step2.dualPlatformConfigDesc') }}
          </p>
          
          <!-- Config Preview -->
          <div v-if="simulationConfig" class="config-detail-panel">
            <!--  -->
            <div class="config-block">
              <div class="config-grid">
                <div class="config-item">
                  <span class="config-item-label">{{ $t('step2.simulationDuration') }}</span>
                  <span class="config-item-value">{{ simulationConfig.time_config?.total_simulation_hours || '-' }} {{ $t('common.hours') }}</span>
                </div>
                <div class="config-item">
                  <span class="config-item-label">{{ $t('step2.roundDuration') }}</span>
                  <span class="config-item-value">{{ simulationConfig.time_config?.minutes_per_round || '-' }} {{ $t('common.minutes') }}</span>
                </div>
                <div class="config-item">
                  <span class="config-item-label">{{ $t('step2.totalRounds') }}</span>
                  <span class="config-item-value">{{ Math.floor((simulationConfig.time_config?.total_simulation_hours * 60 / simulationConfig.time_config?.minutes_per_round)) || '-' }} {{ $t('common.rounds') }}</span>
                </div>
                <div class="config-item">
                  <span class="config-item-label">{{ $t('step2.activePerHour') }}</span>
                  <span class="config-item-value">{{ simulationConfig.time_config?.agents_per_hour_min }}-{{ simulationConfig.time_config?.agents_per_hour_max }}</span>
                </div>
              </div>
              <div class="time-periods">
                <div class="period-item">
                  <span class="period-label">{{ $t('step2.peakHours') }}</span>
                  <span class="period-hours">{{ simulationConfig.time_config?.peak_hours?.join(':00, ') }}:00</span>
                  <span class="period-multiplier">×{{ simulationConfig.time_config?.peak_activity_multiplier }}</span>
                </div>
                <div class="period-item">
                  <span class="period-label">{{ $t('step2.workHours') }}</span>
                  <span class="period-hours">{{ simulationConfig.time_config?.work_hours?.[0] }}:00-{{ simulationConfig.time_config?.work_hours?.slice(-1)[0] }}:00</span>
                  <span class="period-multiplier">×{{ simulationConfig.time_config?.work_activity_multiplier }}</span>
                </div>
                <div class="period-item">
                  <span class="period-label">{{ $t('step2.morningHours') }}</span>
                  <span class="period-hours">{{ simulationConfig.time_config?.morning_hours?.[0] }}:00-{{ simulationConfig.time_config?.morning_hours?.slice(-1)[0] }}:00</span>
                  <span class="period-multiplier">×{{ simulationConfig.time_config?.morning_activity_multiplier }}</span>
                </div>
                <div class="period-item">
                  <span class="period-label">{{ $t('step2.offPeakHours') }}</span>
                  <span class="period-hours">{{ simulationConfig.time_config?.off_peak_hours?.[0] }}:00-{{ simulationConfig.time_config?.off_peak_hours?.slice(-1)[0] }}:00</span>
                  <span class="period-multiplier">×{{ simulationConfig.time_config?.off_peak_activity_multiplier }}</span>
                </div>
              </div>
            </div>

            <!-- Agent  -->
            <div class="config-block">
              <div class="config-block-header">
                <span class="config-block-title">{{ $t('step2.agentConfig') }}</span>
                <span class="config-block-badge">{{ simulationConfig.agent_configs?.length || 0 }} {{ $t('common.items') }}</span>
              </div>
              <div class="agents-cards">
                <div 
                  v-for="agent in simulationConfig.agent_configs" 
                  :key="agent.agent_id" 
                  class="agent-card"
                >
                  <!--  -->
                  <div class="agent-card-header">
                    <div class="agent-identity">
                      <span class="agent-id">Agent {{ agent.agent_id }}</span>
                      <span class="agent-name">{{ agent.entity_name }}</span>
                    </div>
                    <div class="agent-tags">
                      <span class="agent-type">{{ agent.entity_type }}</span>
                      <span class="agent-stance" :class="'stance-' + agent.stance">{{ agent.stance }}</span>
                    </div>
                  </div>
                  
                  <!--  -->
                  <div class="agent-timeline">
                    <span class="timeline-label">{{ $t('step2.activeTimePeriod') }}</span>
                    <div class="mini-timeline">
                      <div 
                        v-for="hour in 24" 
                        :key="hour - 1" 
                        class="timeline-hour"
                        :class="{ 'active': agent.active_hours?.includes(hour - 1) }"
                        :title="`${hour - 1}:00`"
                      ></div>
                    </div>
                    <div class="timeline-marks">
                      <span>0</span>
                      <span>6</span>
                      <span>12</span>
                      <span>18</span>
                      <span>24</span>
                    </div>
                  </div>

                  <!--  -->
                  <div class="agent-params">
                    <div class="param-group">
                      <div class="param-item">
                        <span class="param-label">{{ $t('step2.postsPerHour') }}</span>
                        <span class="param-value">{{ agent.posts_per_hour }}</span>
                      </div>
                      <div class="param-item">
                        <span class="param-label">{{ $t('step2.commentsPerHour') }}</span>
                        <span class="param-value">{{ agent.comments_per_hour }}</span>
                      </div>
                      <div class="param-item">
                        <span class="param-label">{{ $t('step2.responseDelay') }}</span>
                        <span class="param-value">{{ agent.response_delay_min }}-{{ agent.response_delay_max }}min</span>
                      </div>
                    </div>
                    <div class="param-group">
                      <div class="param-item">
                        <span class="param-label">{{ $t('step2.activityLevel') }}</span>
                        <span class="param-value with-bar">
                          <span class="mini-bar" :style="{ width: (agent.activity_level * 100) + '%' }"></span>
                          {{ (agent.activity_level * 100).toFixed(0) }}%
                        </span>
                      </div>
                      <div class="param-item">
                        <span class="param-label">{{ $t('step2.sentimentBias') }}</span>
                        <span class="param-value" :class="agent.sentiment_bias > 0 ? 'positive' : agent.sentiment_bias < 0 ? 'negative' : 'neutral'">
                          {{ agent.sentiment_bias > 0 ? '+' : '' }}{{ agent.sentiment_bias?.toFixed(1) }}
                        </span>
                      </div>
                      <div class="param-item">
                        <span class="param-label">{{ $t('step2.influenceWeight') }}</span>
                        <span class="param-value highlight">{{ agent.influence_weight?.toFixed(1) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!--  -->
            <div class="config-block">
              <div class="config-block-header">
                <span class="config-block-title">{{ $t('step2.recommendAlgoConfig') }}</span>
              </div>
              <div class="platforms-grid">
                <div v-if="simulationConfig.twitter_config" class="platform-card">
                  <div class="platform-card-header">
                    <span class="platform-name">{{ $t('step2.platform1Name') }}</span>
                  </div>
                  <div class="platform-params">
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.recencyWeight') }}</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.recency_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.popularityWeight') }}</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.popularity_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.relevanceWeight') }}</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.relevance_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.viralThreshold') }}</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.viral_threshold }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.echoChamberStrength') }}</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.echo_chamber_strength }}</span>
                    </div>
                  </div>
                </div>
                <div v-if="simulationConfig.reddit_config" class="platform-card">
                  <div class="platform-card-header">
                    <span class="platform-name">{{ $t('step2.platform2Name') }}</span>
                  </div>
                  <div class="platform-params">
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.recencyWeight') }}</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.recency_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.popularityWeight') }}</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.popularity_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.relevanceWeight') }}</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.relevance_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.viralThreshold') }}</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.viral_threshold }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.echoChamberStrength') }}</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.echo_chamber_strength }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- LLM  -->
            <div v-if="simulationConfig.generation_reasoning" class="config-block">
              <div class="config-block-header">
                <span class="config-block-title">{{ $t('step2.llmConfigReasoning') }}</span>
              </div>
              <div class="reasoning-content">
                <div 
                  v-for="(reason, idx) in simulationConfig.generation_reasoning.split('|').slice(0, 2)" 
                  :key="idx" 
                  class="reasoning-item"
                >
                  <p class="reasoning-text">{{ reason.trim() }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 04:  -->
      <div class="step-card" :class="{ 'active': phase === 3, 'completed': phase > 3 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">04</span>
            <span class="step-title">{{ $t('step2.initialActivation') }}</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 3" class="badge success">{{ $t('common.completed') }}</span>
            <span v-else-if="phase === 3" class="badge processing">{{ $t('step2.orchestrating') }}</span>
            <span v-else class="badge pending">{{ $t('common.pending') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="api-note">POST /api/simulation/prepare</p>
          <p class="description">
            {{ $t('step2.initialActivationDesc') }}
          </p>

          <div v-if="simulationConfig?.event_config" class="orchestration-content">
            <!--  -->
            <div class="narrative-box">
              <span class="box-label narrative-label">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="special-icon">
                  <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="url(#paint0_linear)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M16.24 7.76L14.12 14.12L7.76 16.24L9.88 9.88L16.24 7.76Z" fill="url(#paint0_linear)" stroke="url(#paint0_linear)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <defs>
                    <linearGradient id="paint0_linear" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                      <!-- 그라디언트 스톱은 presentation attribute 로는 var() 를 못 받으므로 style 로 준다 -->
                      <stop style="stop-color: var(--wm-accent)"/>
                      <stop offset="1" style="stop-color: var(--wm-accent-hover)"/>
                    </linearGradient>
                  </defs>
                </svg>
                {{ $t('step2.narrativeDirection') }}
              </span>
              <p class="narrative-text">{{ simulationConfig.event_config.narrative_direction }}</p>
            </div>

            <!--  -->
            <div class="topics-section">
              <span class="box-label">{{ $t('step2.initialHotTopics') }}</span>
              <div class="hot-topics-grid">
                <span v-for="topic in simulationConfig.event_config.hot_topics" :key="topic" class="hot-topic-tag">
                  # {{ topic }}
                </span>
              </div>
            </div>

            <!--  -->
            <div class="initial-posts-section">
              <span class="box-label">{{ $t('step2.initialActivationSeq', { count: simulationConfig.event_config.initial_posts.length }) }}</span>
              <div class="posts-timeline">
                <div v-for="(post, idx) in simulationConfig.event_config.initial_posts" :key="idx" class="timeline-item">
                  <div class="timeline-marker"></div>
                  <div class="timeline-content">
                    <div class="post-header">
                      <span class="post-role">{{ post.poster_type }}</span>
                      <span class="post-agent-info">
                        <span class="post-id">Agent {{ post.poster_agent_id }}</span>
                        <span class="post-username">@{{ getAgentUsername(post.poster_agent_id) }}</span>
                      </span>
                    </div>
                    <p class="post-text">{{ post.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 05:  -->
      <div class="step-card" :class="{ 'active': phase === 4 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">05</span>
            <span class="step-title">{{ $t('step2.setupComplete') }}</span>
          </div>
          <div class="step-status">
            <span v-if="phase >= 4" class="badge processing">{{ $t('step1.inProgress') }}</span>
            <span v-else class="badge pending">{{ $t('common.pending') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="api-note">POST /api/simulation/start</p>
          <p class="description">{{ $t('step2.setupCompleteDesc') }}</p>
          
          <!--  -  -->
          <div v-if="simulationConfig && autoGeneratedRounds" class="rounds-config-section">
            <div class="rounds-header">
              <div class="header-left">
                <span class="section-title">{{ $t('step2.roundsConfig') }}</span>
                <span class="section-desc">{{ $t('step2.roundsConfigDesc', { hours: simulationConfig?.time_config?.total_simulation_hours || '-', minutesPerRound: simulationConfig?.time_config?.minutes_per_round || '-' }) }}</span>
              </div>
              <label class="switch-control">
                <input type="checkbox" v-model="useCustomRounds">
                <span class="switch-track"></span>
                <span class="switch-label">{{ $t('step2.customToggle') }}</span>
              </label>
            </div>
            
            <Transition name="fade" mode="out-in">
              <div v-if="useCustomRounds" class="rounds-content custom" key="custom">
                <div class="slider-display">
                  <div class="slider-main-value">
                    <span class="val-num">{{ customMaxRounds }}</span>
                    <span class="val-unit">{{ $t('step2.roundsUnit') }}</span>
                  </div>
                  <div class="slider-meta-info">
                    <span>{{ $t('step2.estimatedDuration', { minutes: Math.round(customMaxRounds * 0.6) }) }}</span>
                  </div>
                </div>

                <div class="range-wrapper">
                  <input 
                    type="range" 
                    v-model.number="customMaxRounds" 
                    min="10" 
                    :max="autoGeneratedRounds"
                    step="5"
                    class="minimal-slider"
                    :style="{ '--percent': ((customMaxRounds - 10) / (autoGeneratedRounds - 10)) * 100 + '%' }"
                  />
                  <div class="range-marks">
                    <span>10</span>
                    <span 
                      class="mark-recommend" 
                      :class="{ active: customMaxRounds === 40 }"
                      @click="customMaxRounds = 40"
                      :style="{ position: 'absolute', left: `calc(${(40 - 10) / (autoGeneratedRounds - 10) * 100}% - 30px)` }"
                    >{{ $t('step2.recommendedRounds', { rounds: 40 }) }}</span>
                    <span>{{ autoGeneratedRounds }}</span>
                  </div>
                </div>
              </div>
              
              <div v-else class="rounds-content auto" key="auto">
                <div class="auto-info-card">
                  <div class="auto-value">
                    <span class="val-num">{{ autoGeneratedRounds }}</span>
                    <span class="val-unit">{{ $t('step2.roundsUnit') }}</span>
                  </div>
                  <div class="auto-content">
                    <div class="auto-meta-row">
                      <span class="duration-badge">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <circle cx="12" cy="12" r="10"></circle>
                          <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        {{ $t('step2.estimatedDurationFull', { minutes: Math.round(autoGeneratedRounds * 0.6) }) }}
                      </span>
                    </div>
                    <div class="auto-desc">
                      <p class="highlight-tip" @click="useCustomRounds = true">{{ $t('step2.customTip') }} ➝</p>
                    </div>
                  </div>
                </div>
              </div>
            </Transition>
          </div>

          <div class="action-group dual">
            <button 
              class="action-btn secondary"
              @click="$emit('go-back')"
            >
              ← {{ $t('step2.backToGraphBuild') }}
            </button>
            <button 
              class="action-btn primary"
              :disabled="phase < 4"
              @click="handleStartSimulation"
            >
              {{ $t('step2.startDualWorldSim') }} ➝
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Profile Detail Modal -->
    <Transition name="modal">
      <div v-if="selectedProfile" class="profile-modal-overlay" @click.self="selectedProfile = null">
        <div class="profile-modal">
          <div class="modal-header">
          <div class="modal-header-info">
            <div class="modal-name-row">
              <span class="modal-realname">{{ selectedProfile.username }}</span>
              <span class="modal-username">@{{ selectedProfile.name }}</span>
            </div>
            <span class="modal-profession">{{ selectedProfile.profession }}</span>
          </div>
          <button class="close-btn" @click="selectedProfile = null">×</button>
        </div>
        
        <div class="modal-body">
          <!--  -->
          <div class="modal-info-grid">
            <div class="info-item">
              <span class="info-label">{{ $t('step2.profileModalAge') }}</span>
              <span class="info-value">{{ selectedProfile.age || '-' }} {{ $t('step2.yearsOld') }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('step2.profileModalGender') }}</span>
              <span class="info-value">{{ { male: $t('step2.genderMale'), female: $t('step2.genderFemale'), other: $t('step2.genderOther') }[selectedProfile.gender] || selectedProfile.gender }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('step2.profileModalCountry') }}</span>
              <span class="info-value">{{ selectedProfile.country || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('step2.profileModalMbti') }}</span>
              <span class="info-value mbti">{{ selectedProfile.mbti || '-' }}</span>
            </div>
          </div>

          <!--  -->
          <div class="modal-section">
            <span class="section-label">{{ $t('step2.profileModalBio') }}</span>
            <p class="section-bio">{{ selectedProfile.bio || $t('step2.noBio') }}</p>
          </div>

          <!--  -->
          <div class="modal-section" v-if="selectedProfile.interested_topics?.length">
            <span class="section-label">{{ $t('step2.profileModalTopics') }}</span>
            <div class="topics-grid">
              <span 
                v-for="topic in selectedProfile.interested_topics" 
                :key="topic" 
                class="topic-item"
              >{{ topic }}</span>
            </div>
          </div>

          <!--  -->
          <div class="modal-section" v-if="selectedProfile.persona">
            <span class="section-label">{{ $t('step2.profileModalPersona') }}</span>
            
            <!--  -->
            <div class="persona-dimensions">
              <div class="dimension-card">
                <span class="dim-title">{{ $t('step2.personaDimExperience') }}</span>
                <span class="dim-desc">{{ $t('step2.personaDimExperienceDesc') }}</span>
              </div>
              <div class="dimension-card">
                <span class="dim-title">{{ $t('step2.personaDimBehavior') }}</span>
                <span class="dim-desc">{{ $t('step2.personaDimBehaviorDesc') }}</span>
              </div>
              <div class="dimension-card">
                <span class="dim-title">{{ $t('step2.personaDimMemory') }}</span>
                <span class="dim-desc">{{ $t('step2.personaDimMemoryDesc') }}</span>
              </div>
              <div class="dimension-card">
                <span class="dim-title">{{ $t('step2.personaDimSocial') }}</span>
                <span class="dim-desc">{{ $t('step2.personaDimSocialDesc') }}</span>
              </div>
            </div>

            <div class="persona-content">
              <p class="section-persona">{{ selectedProfile.persona }}</p>
            </div>
          </div>
        </div>
      </div>
      </div>
    </Transition>

    <!-- Bottom Info / Logs -->
    <div class="system-logs">
      <div class="log-header">
        <span class="log-title">SYSTEM DASHBOARD</span>
        <span class="log-id">{{ simulationId || 'NO_SIMULATION' }}</span>
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
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  prepareSimulation,
  getPrepareStatus,
  getSimulationProfilesRealtime,
  getSimulationConfig,
  getSimulationConfigRealtime
} from '../api/simulation'

const { t } = useI18n({ useScope: 'global' })

const props = defineProps({
  simulationId: String,  // 
  projectData: Object,
  graphData: Object,
  systemLogs: Array
})

const emit = defineEmits(['go-back', 'next-step', 'add-log', 'update-status'])

// State
const phase = ref(0) // 0: , 1: , 2: , 3: 
const taskId = ref(null)
const prepareProgress = ref(0)
const currentStage = ref('')
const progressMessage = ref('')
const profiles = ref([])
const entityTypes = ref([])
const expectedTotal = ref(null)
const simulationConfig = ref(null)
const selectedProfile = ref(null)
const showProfilesDetail = ref(true)

// ：
let lastLoggedMessage = ''
let lastLoggedProfileCount = 0
let lastLoggedConfigStage = ''

const useCustomRounds = ref(false) // 
const customMaxRounds = ref(40)   // 40

// Watch stage to update phase
watch(currentStage, (newStage) => {
  if (newStage === 'Agent' || newStage === 'generating_profiles') {
    phase.value = 1
  } else if (newStage === '' || newStage === 'generating_config') {
    phase.value = 2
    // ，
    if (!configTimer) {
      addLog(t('log.startGeneratingConfig'))
      startConfigPolling()
    }
  } else if (newStage === '' || newStage === 'copying_scripts') {
    phase.value = 2 // 
  }
})

// (설명 생략)
const autoGeneratedRounds = computed(() => {
  if (!simulationConfig.value?.time_config) {
    return null //  null
  }
  const totalHours = simulationConfig.value.time_config.total_simulation_hours
  const minutesPerRound = simulationConfig.value.time_config.minutes_per_round
  if (!totalHours || !minutesPerRound) {
    return null //  null
  }
  const calculatedRounds = Math.floor((totalHours * 60) / minutesPerRound)
  // 40(설명 생략)，
  return Math.max(calculatedRounds, 40)
})

// Polling timer
let pollTimer = null
let profilesTimer = null
let configTimer = null

// Computed
const displayProfiles = computed(() => {
  if (showProfilesDetail.value) {
    return profiles.value
  }
  return profiles.value.slice(0, 6)
})

// agent_idusername
const getAgentUsername = (agentId) => {
  if (profiles.value && profiles.value.length > agentId && agentId >= 0) {
    const profile = profiles.value[agentId]
    return profile?.username || `agent_${agentId}`
  }
  return `agent_${agentId}`
}

const totalTopicsCount = computed(() => {
  return profiles.value.reduce((sum, p) => {
    return sum + (p.interested_topics?.length || 0)
  }, 0)
})

// Methods
const addLog = (msg) => {
  emit('add-log', msg)
}

const handleStartSimulation = () => {
  const params = {}
  
  if (useCustomRounds.value) {
    // ， max_rounds 
    params.maxRounds = customMaxRounds.value
    addLog(t('log.startSimCustomRounds', { rounds: customMaxRounds.value }))
  } else {
    // ， max_rounds 
    addLog(t('log.startSimAutoRounds', { rounds: autoGeneratedRounds.value }))
  }
  
  emit('next-step', params)
}

const truncateBio = (bio) => {
  if (bio.length > 80) {
    return bio.substring(0, 80) + '...'
  }
  return bio
}

const selectProfile = (profile) => {
  selectedProfile.value = profile
}

const startPrepareSimulation = async () => {
  if (!props.simulationId) {
    addLog(t('log.errorMissingSimId'))
    emit('update-status', 'error')
    return
  }
  
  // ，
  phase.value = 1
  addLog(t('log.simInstanceCreated', { id: props.simulationId }))
  addLog(t('log.preparingSimEnv'))
  emit('update-status', 'processing')
  
  try {
    const res = await prepareSimulation({
      simulation_id: props.simulationId,
      use_llm_for_profiles: true,
      parallel_profile_count: 5
    })
    
    if (res.success && res.data) {
      if (res.data.already_prepared) {
        addLog(t('log.detectedExistingPrep'))
        await loadPreparedData()
        return
      }
      
      taskId.value = res.data.task_id
      addLog(t('log.prepareTaskStarted'))
      addLog(t('log.prepareTaskId', { taskId: res.data.task_id }))
      
      // Agent（prepare）
      if (res.data.expected_entities_count) {
        expectedTotal.value = res.data.expected_entities_count
        addLog(t('log.zepEntitiesFound', { count: res.data.expected_entities_count }))
        if (res.data.entity_types && res.data.entity_types.length > 0) {
          addLog(t('log.entityTypes', { types: res.data.entity_types.join(', ') }))
        }
      }
      
      addLog(t('log.startPollingProgress'))
      startPolling()
      //  Profiles
      startProfilesPolling()
    } else {
      addLog(t('log.prepareFailed', { error: res.error || t('common.unknownError') }))
      emit('update-status', 'error')
    }
  } catch (err) {
    addLog(t('log.prepareException', { error: err.message }))
    emit('update-status', 'error')
  }
}

const startPolling = () => {
  pollTimer = setInterval(pollPrepareStatus, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const startProfilesPolling = () => {
  profilesTimer = setInterval(fetchProfilesRealtime, 3000)
}

const stopProfilesPolling = () => {
  if (profilesTimer) {
    clearInterval(profilesTimer)
    profilesTimer = null
  }
}

const pollPrepareStatus = async () => {
  if (!taskId.value && !props.simulationId) return
  
  try {
    const res = await getPrepareStatus({
      task_id: taskId.value,
      simulation_id: props.simulationId
    })
    
    if (res.success && res.data) {
      const data = res.data
      
      prepareProgress.value = data.progress || 0
      progressMessage.value = data.message || ''
      
      if (data.progress_detail) {
        currentStage.value = data.progress_detail.current_stage_name || ''
        
        // (설명 생략)
        const detail = data.progress_detail
        const logKey = `${detail.current_stage}-${detail.current_item}-${detail.total_items}`
        if (logKey !== lastLoggedMessage && detail.item_description) {
          lastLoggedMessage = logKey
          const stageInfo = `[${detail.stage_index}/${detail.total_stages}]`
          if (detail.total_items > 0) {
            addLog(`${stageInfo} ${detail.current_stage_name}: ${detail.current_item}/${detail.total_items} - ${detail.item_description}`)
          } else {
            addLog(`${stageInfo} ${detail.current_stage_name}: ${detail.item_description}`)
          }
        }
      } else if (data.message) {
        const match = data.message.match(/\[(\d+)\/(\d+)\]\s*([^:]+)/)
        if (match) {
          currentStage.value = match[3].trim()
        }
        // (설명 생략)
        if (data.message !== lastLoggedMessage) {
          lastLoggedMessage = data.message
          addLog(data.message)
        }
      }
      
      if (data.status === 'completed' || data.status === 'ready' || data.already_prepared) {
        addLog(t('log.prepareComplete'))
        stopPolling()
        stopProfilesPolling()
        await loadPreparedData()
      } else if (data.status === 'failed') {
        addLog(t('log.prepareFailedWithError', { error: data.error || t('common.unknownError') }))
        stopPolling()
        stopProfilesPolling()
      }
    }
  } catch (err) {
    console.warn(':', err)
  }
}

const fetchProfilesRealtime = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getSimulationProfilesRealtime(props.simulationId, 'reddit')
    
    if (res.success && res.data) {
      const prevCount = profiles.value.length
      profiles.value = res.data.profiles || []
      //  API ，
      if (res.data.total_expected) {
        expectedTotal.value = res.data.total_expected
      }
      
      const types = new Set()
      profiles.value.forEach(p => {
        if (p.entity_type) types.add(p.entity_type)
      })
      entityTypes.value = Array.from(types)
      
      //  Profile (설명 생략)
      const currentCount = profiles.value.length
      if (currentCount > 0 && currentCount !== lastLoggedProfileCount) {
        lastLoggedProfileCount = currentCount
        const total = expectedTotal.value || '?'
        const latestProfile = profiles.value[currentCount - 1]
        const profileName = latestProfile?.name || latestProfile?.username || `Agent_${currentCount}`
        if (currentCount === 1) {
          addLog(t('log.startGeneratingAgentProfiles'))
        }
        addLog(t('log.agentProfile', { current: currentCount, total: total, name: profileName, profession: latestProfile?.profession || t('step2.unknownProfession') }))

        if (expectedTotal.value && currentCount >= expectedTotal.value) {
          addLog(t('log.allProfilesComplete', { count: currentCount }))
        }
      }
    }
  } catch (err) {
    console.warn(' Profiles :', err)
  }
}

const startConfigPolling = () => {
  configTimer = setInterval(fetchConfigRealtime, 2000)
}

const stopConfigPolling = () => {
  if (configTimer) {
    clearInterval(configTimer)
    configTimer = null
  }
}

const fetchConfigRealtime = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getSimulationConfigRealtime(props.simulationId)
    
    if (res.success && res.data) {
      const data = res.data
      
      // (설명 생략)
      if (data.generation_stage && data.generation_stage !== lastLoggedConfigStage) {
        lastLoggedConfigStage = data.generation_stage
        if (data.generation_stage === 'generating_profiles') {
          addLog(t('log.generatingAgentProfileConfig'))
        } else if (data.generation_stage === 'generating_config') {
          addLog(t('log.generatingLLMConfig'))
        }
      }
      
      if (data.config_generated && data.config) {
        simulationConfig.value = data.config
        addLog(t('log.configComplete'))

        if (data.summary) {
          addLog(t('log.configSummaryAgents', { count: data.summary.total_agents }))
          addLog(t('log.configSummaryHours', { hours: data.summary.simulation_hours }))
          addLog(t('log.configSummaryPosts', { count: data.summary.initial_posts_count }))
          addLog(t('log.configSummaryTopics', { count: data.summary.hot_topics_count }))
          addLog(t('log.configSummaryPlatforms', { twitter: data.summary.has_twitter_config ? '✓' : '✗', reddit: data.summary.has_reddit_config ? '✓' : '✗' }))
        }
        
        if (data.config.time_config) {
          const tc = data.config.time_config
          addLog(t('log.timeConfigDetail', { minutes: tc.minutes_per_round, rounds: Math.floor((tc.total_simulation_hours * 60) / tc.minutes_per_round) }))
        }
        
        if (data.config.event_config?.narrative_direction) {
          const narrative = data.config.event_config.narrative_direction
          addLog(t('log.narrativeDirection', { direction: narrative.length > 50 ? narrative.substring(0, 50) + '...' : narrative }))
        }
        
        stopConfigPolling()
        phase.value = 4
        addLog(t('log.envSetupComplete'))
        emit('update-status', 'completed')
      }
    }
  } catch (err) {
    console.warn(' Config :', err)
  }
}

const loadPreparedData = async () => {
  phase.value = 2
  addLog(t('log.loadingExistingConfig'))

  //  Profiles
  await fetchProfilesRealtime()
  addLog(t('log.loadedAgentProfiles', { count: profiles.value.length }))

  // (설명 생략)
  try {
    const res = await getSimulationConfigRealtime(props.simulationId)
    if (res.success && res.data) {
      if (res.data.config_generated && res.data.config) {
        simulationConfig.value = res.data.config
        addLog(t('log.configLoadSuccess'))

        if (res.data.summary) {
          addLog(t('log.configSummaryAgents', { count: res.data.summary.total_agents }))
          addLog(t('log.configSummaryHours', { hours: res.data.summary.simulation_hours }))
          addLog(t('log.configSummaryPostsAlt', { count: res.data.summary.initial_posts_count }))
        }

        addLog(t('log.envSetupComplete'))
        phase.value = 4
        emit('update-status', 'completed')
      } else {
        // ，
        addLog(t('log.configGenerating'))
        startConfigPolling()
      }
    }
  } catch (err) {
    addLog(t('log.loadConfigFailed', { error: err.message }))
    emit('update-status', 'error')
  }
}

// Scroll log to bottom
const logContent = ref(null)
watch(() => props.systemLogs?.length, () => {
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
})

onMounted(() => {
  if (props.simulationId) {
    addLog(t('log.step2Init'))
    startPrepareSimulation()
  }
})

onUnmounted(() => {
  stopPolling()
  stopProfilesPolling()
  stopConfigPolling()
})
</script>

<style scoped>
/* ===== 덱(deck) = 세계 객체 설정 =====
 * /simulation 은 이 설정이 작업 본체이므로 덱 우위(uf-shell--deck-lead)다.
 * 섹션은 세로 스택으로 두고, 덱이 전폭이 되는 band 모드에서는 카드 묶음만
 * auto-fit 으로 열을 늘린다(프로필·에이전트·플랫폼 카드).
 * 색은 --wm-* 토큰만 쓴다(일부 표면색은 전역 정본이 !important 로 지정).
 */
.env-setup-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--wm-bg);
  font-family: var(--wm-font);
}

.scroll-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Step Card */
.step-card {
  background: var(--wm-surface);
  border-radius: var(--wm-radius-md);
  padding: 15px 16px;
  box-shadow: var(--wm-shadow-1);
  border: 1px solid var(--wm-border);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  position: relative;
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
  margin-bottom: 10px;
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

.card-content {
  /* No extra padding - uses step-card's padding */
}

.api-note {
  font-family: var(--wm-mono);
  font-size: 9px;
  letter-spacing: 0.02em;
  color: var(--wm-text-dim);
  margin: 0 0 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.description {
  font-size: 12px;
  color: var(--wm-text-muted);
  line-height: 1.55;
  margin: 0 0 14px;
}

.step-card:not(.active) .description {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Action Section */
.action-section {
  margin-top: 16px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  font-family: var(--wm-font);
  font-size: 12px;
  font-weight: 700;
  border: 1px solid transparent;
  border-radius: var(--wm-radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn.primary {
  background: var(--wm-accent);
  border-color: var(--wm-accent);
  color: var(--wm-on-accent);
}

.action-btn.primary:hover:not(:disabled) {
  background: var(--wm-accent-hover);
}

.action-btn.secondary {
  background: var(--wm-surface-2);
  border-color: var(--wm-border);
  color: var(--wm-text);
}

.action-btn.secondary:hover:not(:disabled) {
  background: var(--wm-surface-3);
  border-color: var(--wm-border-strong);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-group {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.action-group.dual {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.action-group.dual .action-btn {
  width: 100%;
}

/* Info Card */
.info-card {
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border-soft);
  border-radius: var(--wm-radius-sm);
  padding: 12px 14px;
  margin-top: 14px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 7px 0;
  border-bottom: 1px dashed var(--wm-border-soft);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 11px;
  color: var(--wm-text-muted);
}

.info-value {
  font-size: 12px;
  font-weight: 500;
  color: var(--wm-text);
  word-break: break-all;
  text-align: right;
}

.info-value.mono {
  font-family: var(--wm-mono);
  font-size: 11px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
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

/* Profiles Preview */
.profiles-preview {
  margin-top: 16px;
  border-top: 1px solid var(--wm-border-soft);
  padding-top: 14px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.preview-title {
  font-family: var(--wm-mono);
  font-size: 10px;
  font-weight: 700;
  color: var(--wm-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* band(전폭)에서 2열 이상으로 펼쳐진다 */
.profiles-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 10px;
  max-height: 320px;
  overflow-y: auto;
  padding-right: 4px;
}

.profiles-list::-webkit-scrollbar {
  width: 4px;
}

.profiles-list::-webkit-scrollbar-thumb {
  background: var(--wm-border-strong);
  border-radius: 2px;
}

.profile-card {
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-sm);
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.profile-card:hover {
  border-color: var(--wm-accent-border);
}

.profile-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 5px;
  flex-wrap: wrap;
}

.profile-realname {
  font-size: 13px;
  font-weight: 700;
  color: var(--wm-text);
}

.profile-username {
  font-family: var(--wm-mono);
  font-size: 10px;
  color: var(--wm-text-dim);
}

.profile-meta {
  margin-bottom: 7px;
}

.profile-profession {
  font-size: 10px;
  color: var(--wm-text-muted);
  background: var(--wm-surface-3);
  padding: 2px 7px;
  border-radius: var(--wm-radius-sm);
}

.profile-bio {
  font-size: 11.5px;
  color: var(--wm-text-muted);
  line-height: 1.6;
  margin: 0 0 9px 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.profile-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.topic-tag {
  font-size: 9.5px;
  color: var(--wm-text-muted);
  background: var(--wm-surface-3);
  border: 1px solid var(--wm-border);
  padding: 2px 7px;
  border-radius: var(--wm-radius-pill);
}

.topic-more {
  font-size: 9.5px;
  color: var(--wm-text-dim);
  padding: 2px 6px;
}

/* Config Detail Panel */
.config-detail-panel {
  margin-top: 14px;
}

.config-block {
  margin-top: 14px;
  border-top: 1px solid var(--wm-border-soft);
  padding-top: 12px;
}

.config-block:first-child {
  margin-top: 0;
  border-top: none;
  padding-top: 0;
}

.config-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.config-block-title {
  font-family: var(--wm-mono);
  font-size: 10px;
  font-weight: 700;
  color: var(--wm-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.config-block-badge {
  font-family: var(--wm-mono);
  font-size: 10px;
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border);
  color: var(--wm-text-muted);
  padding: 2px 8px;
  border-radius: var(--wm-radius-pill);
  white-space: nowrap;
}

/* Config Grid */
.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
}

.config-item {
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border-soft);
  padding: 10px 12px;
  border-radius: var(--wm-radius-sm);
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.config-item-label {
  font-size: 10px;
  color: var(--wm-text-dim);
}

.config-item-value {
  font-family: var(--wm-mono);
  font-size: 15px;
  font-weight: 600;
  color: var(--wm-text);
}

/* Time Periods */
.time-periods {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.period-item {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 7px 11px;
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border-soft);
  border-radius: var(--wm-radius-sm);
}

.period-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--wm-text-muted);
  min-width: 66px;
}

.period-hours {
  font-family: var(--wm-mono);
  font-size: 10.5px;
  color: var(--wm-text-muted);
  flex: 1;
}

.period-multiplier {
  font-family: var(--wm-mono);
  font-size: 10.5px;
  font-weight: 700;
  color: var(--wm-accent-text);
  background: var(--wm-accent-soft);
  border: 1px solid var(--wm-accent-border);
  padding: 2px 6px;
  border-radius: var(--wm-radius-sm);
}

/* Agents Cards — band 에서 2열 이상 */
.agents-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 10px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 4px;
}

.agents-cards::-webkit-scrollbar {
  width: 4px;
}

.agents-cards::-webkit-scrollbar-thumb {
  background: var(--wm-border-strong);
  border-radius: 2px;
}

.agent-card {
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-sm);
  padding: 12px;
  transition: all 0.2s ease;
  min-width: 0;
}

.agent-card:hover {
  border-color: var(--wm-accent-border);
}

/* Agent Card Header */
.agent-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--wm-border-soft);
}

.agent-identity {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.agent-id {
  font-family: var(--wm-mono);
  font-size: 9.5px;
  color: var(--wm-text-dim);
}

.agent-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--wm-text);
}

.agent-tags {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.agent-type {
  font-size: 9.5px;
  color: var(--wm-text-muted);
  background: var(--wm-surface-3);
  padding: 2px 7px;
  border-radius: var(--wm-radius-sm);
}

.agent-stance {
  font-size: 9.5px;
  font-weight: 600;
  text-transform: uppercase;
  padding: 2px 7px;
  border-radius: var(--wm-radius-sm);
}

.stance-neutral {
  background: var(--wm-surface-3);
  color: var(--wm-text-muted);
}

.stance-supportive {
  background: var(--wm-pos-soft);
  color: var(--wm-pos);
}

.stance-opposing {
  background: var(--wm-neg-soft);
  color: var(--wm-neg);
}

.stance-observer {
  background: var(--wm-warn-soft);
  color: var(--wm-warn);
}

/* Agent Timeline */
.agent-timeline {
  margin-bottom: 12px;
}

.timeline-label {
  display: block;
  font-family: var(--wm-mono);
  font-size: 9px;
  color: var(--wm-text-dim);
  margin-bottom: 5px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.mini-timeline {
  display: flex;
  gap: 2px;
  height: 16px;
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border-soft);
  border-radius: var(--wm-radius-sm);
  padding: 3px;
}

.timeline-hour {
  flex: 1;
  background: var(--wm-surface-3);
  border-radius: 1px;
  transition: all 0.2s;
}

.timeline-hour.active {
  background: var(--wm-accent);
}

.timeline-marks {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-family: var(--wm-mono);
  font-size: 8.5px;
  color: var(--wm-text-dim);
}

/* Agent Params */
.agent-params {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.param-group {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

/* 라벨은 3차 메타가 아니라 2차 정보다 → muted (dim 은 9.5px 에서 AA 미달이었다) */
.param-item .param-label {
  font-size: 9.5px;
  color: var(--wm-text-muted);
}

.param-item .param-value {
  font-family: var(--wm-mono);
  font-size: 11.5px;
  font-weight: 600;
  color: var(--wm-text-muted);
}

.param-value.with-bar {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mini-bar {
  height: 4px;
  background: var(--wm-accent);
  border-radius: 2px;
  min-width: 4px;
  max-width: 40px;
}

.param-value.positive {
  color: var(--wm-pos);
}

.param-value.negative {
  color: var(--wm-neg);
}

.param-value.neutral {
  color: var(--wm-text-muted);
}

.param-value.highlight {
  color: var(--wm-accent-text);
}

/* Platforms Grid */
.platforms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 10px;
}

.platform-card {
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border-soft);
  padding: 12px;
  border-radius: var(--wm-radius-sm);
  min-width: 0;
}

.platform-card-header {
  margin-bottom: 9px;
  padding-bottom: 7px;
  border-bottom: 1px solid var(--wm-border);
}

.platform-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--wm-text);
}

.platform-params {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.param-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.param-label {
  font-size: 11px;
  color: var(--wm-text-muted);
}

.param-value {
  font-family: var(--wm-mono);
  font-size: 11.5px;
  font-weight: 600;
  color: var(--wm-text);
}

/* Reasoning Content */
.reasoning-content {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.reasoning-item {
  padding: 11px 13px;
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border-soft);
  border-radius: var(--wm-radius-sm);
}

.reasoning-text {
  font-size: 12px;
  color: var(--wm-text-muted);
  line-height: 1.7;
  margin: 0;
}

/* Profile Modal */
.profile-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--wm-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.profile-modal {
  background: var(--wm-surface);
  border: 1px solid var(--wm-border);
  border-radius: var(--wm-radius-lg);
  width: 90%;
  max-width: 600px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--wm-shadow-3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 20px;
  background: var(--wm-surface);
  border-bottom: 1px solid var(--wm-border);
}

.modal-header-info {
  flex: 1;
  min-width: 0;
}

.modal-name-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 7px;
}

.modal-realname {
  font-size: 19px;
  font-weight: 700;
  color: var(--wm-text);
}

.modal-username {
  font-family: var(--wm-mono);
  font-size: 12px;
  color: var(--wm-text-dim);
}

.modal-profession {
  font-size: 11px;
  color: var(--wm-text-muted);
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border);
  padding: 3px 9px;
  border-radius: var(--wm-radius-sm);
  display: inline-block;
  font-weight: 500;
}

.close-btn {
  width: 30px;
  height: 30px;
  border: none;
  background: none;
  color: var(--wm-text-dim);
  border-radius: 50%;
  font-size: 22px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  transition: color 0.2s;
  padding: 0;
  flex-shrink: 0;
}

.close-btn:hover {
  color: var(--wm-text);
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.modal-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 18px 16px;
  margin-bottom: 26px;
  padding: 0;
  background: transparent;
  border-radius: 0;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-family: var(--wm-mono);
  font-size: 9.5px;
  color: var(--wm-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700;
}

.info-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--wm-text);
}

.info-value.mbti {
  font-family: var(--wm-mono);
  color: var(--wm-alt);
}

.modal-section {
  margin-bottom: 24px;
}

.section-label {
  display: block;
  font-family: var(--wm-mono);
  font-size: 9.5px;
  font-weight: 700;
  color: var(--wm-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 10px;
}

.section-bio {
  font-size: 13px;
  color: var(--wm-text);
  line-height: 1.65;
  margin: 0;
  padding: 14px;
  background: var(--wm-surface-2);
  border-radius: var(--wm-radius-sm);
  border-left: 3px solid var(--wm-border-strong);
}

.topics-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.topic-item {
  font-size: 10.5px;
  color: var(--wm-text-muted);
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border);
  padding: 4px 10px;
  border-radius: var(--wm-radius-pill);
  transition: all 0.2s;
}

.topic-item:hover {
  background: var(--wm-accent-soft);
  border-color: var(--wm-accent-border);
  color: var(--wm-accent-text);
}

.persona-dimensions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.dimension-card {
  background: var(--wm-surface-2);
  padding: 11px;
  border-radius: var(--wm-radius-sm);
  border-left: 3px solid var(--wm-border-strong);
  transition: all 0.2s;
}

.dimension-card:hover {
  background: var(--wm-surface-3);
  border-left-color: var(--wm-accent);
}

.dim-title {
  display: block;
  font-size: 11.5px;
  font-weight: 700;
  color: var(--wm-text);
  margin-bottom: 4px;
}

.dim-desc {
  display: block;
  font-size: 10px;
  color: var(--wm-text-dim);
  line-height: 1.45;
}

.persona-content {
  max-height: none;
  overflow: visible;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
}

.persona-content::-webkit-scrollbar {
  width: 4px;
}

.persona-content::-webkit-scrollbar-thumb {
  background: var(--wm-border-strong);
  border-radius: 2px;
}

.section-persona {
  font-size: 12.5px;
  color: var(--wm-text-muted);
  line-height: 1.8;
  margin: 0;
  text-align: justify;
}

/* ===== 로그 독 — 덱 마지막 자식으로 in-flow ===== */
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

/* Spinner */
.spinner-sm {
  width: 15px;
  height: 15px;
  border: 2px solid var(--wm-border);
  border-top-color: var(--wm-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Orchestration Content */
.orchestration-content {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-top: 14px;
}

.box-label {
  display: block;
  font-family: var(--wm-mono);
  font-size: 10px;
  font-weight: 700;
  color: var(--wm-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 10px;
}

.narrative-box {
  background: var(--wm-surface-2);
  padding: 16px 18px;
  border-radius: var(--wm-radius-md);
  border: 1px solid var(--wm-border);
  box-shadow: var(--wm-shadow-1);
  transition: all 0.3s ease;
}

.narrative-box .box-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--wm-text-muted);
  font-size: 11px;
  letter-spacing: 0.06em;
  margin-bottom: 10px;
  font-weight: 700;
}

.special-icon {
  filter: drop-shadow(0 2px 6px var(--wm-accent-soft));
  transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.narrative-box:hover .special-icon {
  transform: rotate(180deg);
}

.narrative-text {
  font-family: var(--wm-font);
  font-size: 13px;
  color: var(--wm-text);
  line-height: 1.8;
  margin: 0;
  text-align: justify;
  letter-spacing: 0.01em;
}

.topics-section {
  background: transparent;
}

.hot-topics-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.hot-topic-tag {
  font-size: 11px;
  color: var(--wm-warn);
  background: var(--wm-warn-soft);
  border: 1px solid var(--wm-border);
  padding: 3px 9px;
  border-radius: var(--wm-radius-pill);
  font-weight: 600;
}

.hot-topic-more {
  font-size: 10.5px;
  color: var(--wm-text-dim);
  padding: 4px 6px;
}

.initial-posts-section {
  border-top: 1px solid var(--wm-border-soft);
  padding-top: 14px;
}

.posts-timeline {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-left: 8px;
  border-left: 2px solid var(--wm-border);
  margin-top: 12px;
}

.timeline-item {
  position: relative;
  padding-left: 18px;
}

.timeline-marker {
  position: absolute;
  left: 0;
  top: 14px;
  width: 12px;
  height: 2px;
  background: var(--wm-border-strong);
}

.timeline-content {
  background: var(--wm-surface-2);
  padding: 11px;
  border-radius: var(--wm-radius-sm);
  border: 1px solid var(--wm-border-soft);
}

.post-header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.post-role {
  font-family: var(--wm-mono);
  font-size: 10px;
  font-weight: 700;
  color: var(--wm-text);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.post-agent-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.post-id,
.post-username {
  font-family: var(--wm-mono);
  font-size: 9.5px;
  color: var(--wm-text-dim);
  line-height: 1;
  vertical-align: baseline;
}

.post-username {
  margin-right: 6px;
}

.post-text {
  font-size: 11.5px;
  color: var(--wm-text-muted);
  line-height: 1.55;
  margin: 0;
}

/* 라운드 설정 */
.rounds-config-section {
  margin: 18px 0;
  padding-top: 18px;
  border-top: 1px solid var(--wm-border-soft);
}

.rounds-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--wm-text);
}

.section-desc {
  font-size: 11px;
  color: var(--wm-text-muted);
  line-height: 1.5;
}

.desc-highlight {
  font-family: var(--wm-mono);
  font-weight: 600;
  color: var(--wm-text);
  background: var(--wm-surface-2);
  padding: 1px 6px;
  border-radius: var(--wm-radius-sm);
  margin: 0 2px;
}

/* Switch Control */
.switch-control {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px 4px 4px;
  border-radius: var(--wm-radius-pill);
  transition: background 0.2s;
}

.switch-control:hover {
  background: var(--wm-surface-2);
}

.switch-control input {
  display: none;
}

.switch-track {
  width: 34px;
  height: 18px;
  background: var(--wm-surface-3);
  border-radius: var(--wm-radius-pill);
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
  flex-shrink: 0;
}

/* 전역 임베드 시트가 트랙/노브 배경을 !important 로 고정하므로 상태 구분은 여기서 되찾는다 */
.switch-track::after {
  content: '';
  position: absolute;
  left: 2px;
  top: 2px;
  width: 14px;
  height: 14px;
  background: var(--wm-text) !important;
  border-radius: 50%;
  box-shadow: var(--wm-shadow-1);
  transition: transform 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
}

.switch-control input:checked + .switch-track {
  background: var(--wm-accent) !important;
}

.switch-control input:checked + .switch-track::after {
  transform: translateX(16px);
  background: var(--wm-on-accent) !important;
}

.switch-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--wm-text-muted);
}

.switch-control input:checked ~ .switch-label {
  color: var(--wm-accent-text);
}

/* Slider Content */
.rounds-content {
  animation: fadeIn 0.3s ease;
}

.slider-display {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.slider-main-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.val-num {
  font-family: var(--wm-mono);
  font-size: 22px;
  font-weight: 700;
  color: var(--wm-text);
}

.val-unit {
  font-size: 11px;
  color: var(--wm-text-muted);
  font-weight: 500;
}

.slider-meta-info {
  font-family: var(--wm-mono);
  font-size: 10.5px;
  color: var(--wm-text-muted);
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border);
  padding: 4px 8px;
  border-radius: var(--wm-radius-sm);
}

.range-wrapper {
  position: relative;
  padding: 0 2px;
}

.minimal-slider {
  -webkit-appearance: none;
  width: 100%;
  height: 4px;
  background: var(--wm-surface-3);
  border-radius: 2px;
  outline: none;
  /* 채움(진행) 표시 — 전역 시트의 background 단축 지정이 이미지를 지우므로 !important */
  background-image: linear-gradient(var(--wm-accent), var(--wm-accent)) !important;
  background-size: var(--percent, 0%) 100% !important;
  background-repeat: no-repeat !important;
  cursor: pointer;
}

.minimal-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 15px;
  height: 15px;
  border-radius: 50%;
  background: var(--wm-surface);
  border: 2px solid var(--wm-accent);
  cursor: pointer;
  box-shadow: var(--wm-shadow-1);
  transition: transform 0.1s;
  margin-top: -6px; /* Center thumb */
}

.minimal-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.minimal-slider::-webkit-slider-runnable-track {
  height: 4px;
  border-radius: 2px;
}

.range-marks {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-family: var(--wm-mono);
  font-size: 9.5px;
  color: var(--wm-text-dim);
  position: relative;
}

.mark-recommend {
  cursor: pointer;
  transition: color 0.2s;
  position: relative;
}

.mark-recommend:hover {
  color: var(--wm-text);
}

.mark-recommend.active {
  color: var(--wm-accent-text);
  font-weight: 700;
}

.mark-recommend::after {
  content: '';
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  width: 1px;
  height: 4px;
  background: var(--wm-border-strong);
}

/* Auto Info */
.auto-info-card {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  background: var(--wm-surface-2);
  border: 1px solid var(--wm-border-soft);
  padding: 14px 16px;
  border-radius: var(--wm-radius-sm);
}

.auto-value {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  gap: 4px;
  padding-right: 18px;
  border-right: 1px solid var(--wm-border);
}

.auto-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
}

.auto-meta-row {
  display: flex;
  align-items: center;
}

.duration-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-family: var(--wm-mono);
  font-size: 10.5px;
  font-weight: 500;
  color: var(--wm-text-muted);
  background: var(--wm-surface);
  border: 1px solid var(--wm-border);
  padding: 3px 8px;
  border-radius: var(--wm-radius-sm);
  box-shadow: var(--wm-shadow-1);
}

.auto-desc {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.auto-desc p {
  margin: 0;
  font-size: 12px;
  color: var(--wm-text-muted);
  line-height: 1.5;
}

.highlight-tip {
  margin-top: 4px !important;
  font-size: 11.5px !important;
  color: var(--wm-accent-text) !important;
  font-weight: 600;
  cursor: pointer;
}

.highlight-tip:hover {
  text-decoration: underline;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Modal Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .profile-modal {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-leave-active .profile-modal {
  transition: all 0.3s ease-in;
}

.modal-enter-from .profile-modal,
.modal-leave-to .profile-modal {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
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
