<script setup>
import { onMounted, computed, ref } from 'vue'
import { useDashboardStore, useHotspotsStore, useKeywordsStore } from '../stores'

const dashboardStore = useDashboardStore()
const hotspotsStore = useHotspotsStore()
const keywordsStore = useKeywordsStore()

const refreshing = ref(false)

onMounted(() => {
  dashboardStore.fetchStats()
  hotspotsStore.fetchHotspots({ page_size: 5 })
  keywordsStore.fetchKeywords()
})

const statCards = computed(() => [
  {
    label: '活跃关键词',
    value: dashboardStore.stats.active_keywords,
    total: dashboardStore.stats.total_keywords,
    icon: 'tag',
    color: 'primary',
  },
  {
    label: '今日热点',
    value: dashboardStore.stats.today_hotspots,
    total: dashboardStore.stats.total_hotspots,
    icon: 'fire',
    color: 'secondary',
  },
  {
    label: '未读热点',
    value: dashboardStore.stats.unread_hotspots,
    icon: 'bell',
    color: 'warning',
  },
  {
    label: '已发送通知',
    value: dashboardStore.stats.notifications_sent,
    icon: 'send',
    color: 'success',
  },
])

async function handleRefresh() {
  refreshing.value = true
  try {
    await hotspotsStore.refresh()
    await dashboardStore.fetchStats()
    await hotspotsStore.fetchHotspots({ page_size: 5 })
  } finally {
    refreshing.value = false
  }
}

function getSourceIcon(source) {
  const icons = {
    hackernews: '🔶',
    github: '🐙',
    twitter: '🐦',
    reddit: '🤖',
    zhihu: '知',
    bing: '🔍',
    google: '🔎',
    duckduckgo: '🦆',
  }
  return icons[source] || '📰'
}

function formatTime(dateStr) {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold font-orbitron cyber-gradient-text">DASHBOARD</h1>
        <p class="text-gray-500 text-sm mt-1">实时监控热点动态</p>
      </div>
      <button 
        @click="handleRefresh"
        :disabled="refreshing"
        class="cyber-btn flex items-center gap-2"
      >
        <svg 
          :class="['w-4 h-4', refreshing && 'animate-spin']" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          stroke-width="2"
        >
          <path d="M23 4v6h-6M1 20v-6h6"/>
          <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
        </svg>
        <span>{{ refreshing ? '刷新中...' : '立即刷新' }}</span>
      </button>
    </div>
    
    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div 
        v-for="(stat, index) in statCards" 
        :key="stat.label"
        class="stat-card group"
        :style="{ animationDelay: `${index * 100}ms` }"
      >
        <div class="flex items-start justify-between">
          <div>
            <p class="text-gray-400 text-sm">{{ stat.label }}</p>
            <p class="text-3xl font-bold mt-2 font-mono" :class="`text-cyber-${stat.color}`">
              {{ stat.value }}
            </p>
            <p v-if="stat.total" class="text-xs text-gray-500 mt-1">
              共 {{ stat.total }} 个
            </p>
          </div>
          <div 
            :class="[
              'w-12 h-12 rounded-lg flex items-center justify-center',
              `bg-cyber-${stat.color}/10 text-cyber-${stat.color}`
            ]"
          >
            <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <template v-if="stat.icon === 'tag'">
                <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/>
                <circle cx="7" cy="7" r="1"/>
              </template>
              <template v-else-if="stat.icon === 'fire'">
                <path d="M12 2c.5 3-1 6-3 8s-4 3-4 6c0 4 4 6 7 6s7-2 7-6c0-2-1-4-2-5s-2-2-2-4c0-1.5.5-3 1-4-1.5 1-4 2-4-1z"/>
              </template>
              <template v-else-if="stat.icon === 'bell'">
                <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 01-3.46 0"/>
              </template>
              <template v-else-if="stat.icon === 'send'">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </template>
            </svg>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 主内容区 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 最新热点 -->
      <div class="lg:col-span-2 cyber-card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-cyber-primary animate-pulse"></span>
            最新热点
          </h2>
          <RouterLink to="/hotspots" class="text-sm text-cyber-primary hover:text-cyber-secondary transition-colors">
            查看全部 →
          </RouterLink>
        </div>
        
        <div v-if="hotspotsStore.loading" class="space-y-4">
          <div v-for="i in 3" :key="i" class="animate-pulse">
            <div class="h-4 bg-cyber-border rounded w-3/4 mb-2"></div>
            <div class="h-3 bg-cyber-border rounded w-1/2"></div>
          </div>
        </div>
        
        <div v-else-if="hotspotsStore.hotspots.length === 0" class="text-center py-12 text-gray-500">
          <svg class="w-16 h-16 mx-auto mb-4 opacity-50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 6v6l4 2"/>
          </svg>
          <p>暂无热点数据</p>
          <p class="text-sm mt-1">点击刷新按钮获取最新热点</p>
        </div>
        
        <div v-else class="space-y-3">
          <a
            v-for="hotspot in hotspotsStore.hotspots"
            :key="hotspot.id"
            :href="hotspot.source_url"
            target="_blank"
            :class="[
              'block p-3 rounded-lg border transition-all duration-300 group hotspot-card-mini',
              'hover:border-cyber-primary/50 hover:bg-cyber-primary/5 hover:shadow-lg hover:shadow-cyber-primary/10',
              hotspot.read 
                ? 'border-cyber-border/50 opacity-70' 
                : 'border-cyber-border bg-cyber-card'
            ]"
          >
            <div class="flex items-start gap-3">
              <span class="text-xl flex-shrink-0 group-hover:scale-110 transition-transform">{{ getSourceIcon(hotspot.source) }}</span>
              <div class="flex-1 min-w-0">
                <h3 class="font-medium text-gray-200 truncate group-hover:text-cyber-primary transition-colors">
                  {{ hotspot.title }}
                </h3>
                <!-- AI 摘要 -->
                <p v-if="hotspot.summary || hotspot.ai_analysis || hotspot.content" class="text-sm text-gray-400 mt-1 line-clamp-2">
                  <span class="text-cyber-primary/80 text-xs">摘要:</span>
                  {{ hotspot.summary || hotspot.ai_analysis || (hotspot.content ? hotspot.content.substring(0, 80) + '...' : '') }}
                </p>
                <div class="flex items-center gap-3 mt-2 text-xs text-gray-500">
                  <span class="uppercase text-cyber-secondary/80">{{ hotspot.source }}</span>
                  <span>•</span>
                  <span>{{ formatTime(hotspot.discovered_at) }}</span>
                  <span v-if="hotspot.score" class="ml-auto ai-score-mini">
                    AI {{ Math.round(hotspot.score) }}分
                  </span>
                </div>
              </div>
            </div>
          </a>
        </div>
      </div>
      
      <!-- 活跃关键词 -->
      <div class="cyber-card">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-cyber-secondary animate-pulse"></span>
            监控关键词
          </h2>
          <RouterLink to="/keywords" class="text-sm text-cyber-primary hover:text-cyber-secondary transition-colors">
            管理 →
          </RouterLink>
        </div>
        
        <div v-if="keywordsStore.loading" class="space-y-2">
          <div v-for="i in 5" :key="i" class="animate-pulse">
            <div class="h-8 bg-cyber-border rounded"></div>
          </div>
        </div>
        
        <div v-else-if="keywordsStore.activeKeywords.length === 0" class="text-center py-8 text-gray-500">
          <svg class="w-12 h-12 mx-auto mb-3 opacity-50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
            <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/>
            <circle cx="7" cy="7" r="1"/>
          </svg>
          <p>暂无活跃关键词</p>
          <RouterLink to="/keywords" class="text-sm text-cyber-primary hover:underline mt-2 inline-block">
            添加关键词
          </RouterLink>
        </div>
        
        <div v-else class="space-y-2">
          <div
            v-for="keyword in keywordsStore.activeKeywords.slice(0, 10)"
            :key="keyword.id"
            class="flex items-center justify-between p-2 rounded border border-cyber-border hover:border-cyber-primary/30 transition-colors"
          >
            <span class="text-sm font-medium truncate">{{ keyword.keyword }}</span>
            <span class="cyber-badge">
              {{ keyword.match_count || 0 }}
            </span>
          </div>
          
          <p v-if="keywordsStore.activeKeywords.length > 10" class="text-xs text-gray-500 text-center pt-2">
            还有 {{ keywordsStore.activeKeywords.length - 10 }} 个关键词
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
