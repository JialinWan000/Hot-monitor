<script setup>
import { onMounted, ref, computed, watch } from 'vue'
import { useHotspotsStore } from '../stores'

const hotspotsStore = useHotspotsStore()

const selectedSource = ref('')
const searchQuery = ref('')
const onlyUnread = ref(false)
const refreshing = ref(false)
const searchDomain = ref('')
const showSearchModal = ref(false)
const searching = ref(false)

onMounted(() => {
  hotspotsStore.fetchHotspots()
  hotspotsStore.fetchSources()
})

const filteredHotspots = computed(() => {
  let result = hotspotsStore.hotspots
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(h => 
      h.title.toLowerCase().includes(query) ||
      h.summary?.toLowerCase().includes(query)
    )
  }
  
  return result
})

function loadMore() {
  hotspotsStore.page++
  hotspotsStore.fetchHotspots({
    source: selectedSource.value || undefined,
    unread_only: onlyUnread.value || undefined,
  })
}

async function handleRefresh() {
  refreshing.value = true
  try {
    await hotspotsStore.refresh()
    hotspotsStore.page = 1
    await hotspotsStore.fetchHotspots()
  } finally {
    refreshing.value = false
  }
}

async function handleSearch() {
  if (!searchDomain.value.trim()) return
  
  searching.value = true
  try {
    await hotspotsStore.searchDomain(searchDomain.value)
    showSearchModal.value = false
    searchDomain.value = ''
    // 等待一会儿再刷新
    setTimeout(() => {
      hotspotsStore.fetchHotspots()
    }, 2000)
  } finally {
    searching.value = false
  }
}

watch([selectedSource, onlyUnread], () => {
  hotspotsStore.page = 1
  hotspotsStore.fetchHotspots({
    source: selectedSource.value || undefined,
    unread_only: onlyUnread.value || undefined,
  })
})

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
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold font-orbitron cyber-gradient-text">HOTSPOTS</h1>
        <p class="text-gray-500 text-sm mt-1">发现最新热点资讯</p>
      </div>
      <div class="flex gap-3">
        <button 
          @click="showSearchModal = true"
          class="cyber-btn flex items-center gap-2"
        >
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <span>搜索领域</span>
        </button>
        <button 
          @click="handleRefresh"
          :disabled="refreshing"
          class="cyber-btn-primary flex items-center gap-2"
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
          <span>{{ refreshing ? '抓取中...' : '抓取热点' }}</span>
        </button>
      </div>
    </div>
    
    <!-- 筛选栏 -->
    <div class="cyber-card">
      <div class="flex flex-wrap items-center gap-4">
        <!-- 搜索框 -->
        <div class="flex-1 min-w-[200px]">
          <input 
            v-model="searchQuery"
            type="text"
            placeholder="搜索热点标题..."
            class="cyber-input"
          />
        </div>
        
        <!-- 来源筛选 -->
        <select v-model="selectedSource" class="cyber-input w-auto">
          <option value="">全部来源</option>
          <option v-for="source in hotspotsStore.sources" :key="source" :value="source">
            {{ source.toUpperCase() }}
          </option>
        </select>
        
        <!-- 未读筛选 -->
        <label class="flex items-center gap-2 cursor-pointer">
          <input 
            v-model="onlyUnread" 
            type="checkbox" 
            class="w-4 h-4 rounded border-cyber-border bg-cyber-darker text-cyber-primary focus:ring-cyber-primary/30"
          />
          <span class="text-sm">仅未读</span>
        </label>
        
        <!-- 全部已读 -->
        <button 
          @click="hotspotsStore.markAllAsRead()"
          class="text-sm text-gray-400 hover:text-cyber-primary transition-colors"
        >
          全部标记已读
        </button>
      </div>
    </div>
    
    <!-- 热点列表 -->
    <div v-if="hotspotsStore.loading && hotspotsStore.page === 1" class="space-y-4">
      <div v-for="i in 5" :key="i" class="cyber-card animate-pulse">
        <div class="flex gap-4">
          <div class="w-12 h-12 bg-cyber-border rounded"></div>
          <div class="flex-1">
            <div class="h-5 bg-cyber-border rounded w-3/4 mb-2"></div>
            <div class="h-4 bg-cyber-border rounded w-1/2"></div>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else-if="filteredHotspots.length === 0" class="cyber-card text-center py-16">
      <svg class="w-20 h-20 mx-auto mb-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 6v6l4 2"/>
      </svg>
      <p class="text-gray-400 text-lg">暂无热点数据</p>
      <p class="text-gray-500 text-sm mt-2">点击"抓取热点"按钮获取最新内容</p>
    </div>
    
    <div v-else class="space-y-4">
      <a
        v-for="hotspot in filteredHotspots"
        :key="hotspot.id"
        :href="hotspot.url"
        target="_blank"
        @click="hotspotsStore.markAsRead(hotspot.id)"
        :class="[
          'cyber-card block transition-all duration-200 hover:scale-[1.01]',
          !hotspot.read && 'border-l-2 border-l-cyber-primary'
        ]"
      >
        <div class="flex gap-4">
          <div class="flex-shrink-0 w-12 h-12 rounded-lg bg-cyber-darker flex items-center justify-center text-2xl">
            {{ getSourceIcon(hotspot.source) }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-4">
              <h3 :class="[
                'font-medium line-clamp-2',
                hotspot.read ? 'text-gray-400' : 'text-gray-100'
              ]">
                {{ hotspot.title }}
              </h3>
              <span v-if="hotspot.ai_score" class="flex-shrink-0 cyber-badge">
                AI {{ hotspot.ai_score }}/10
              </span>
            </div>
            
            <p v-if="hotspot.summary" class="text-sm text-gray-500 mt-2 line-clamp-2">
              {{ hotspot.summary }}
            </p>
            
            <div class="flex items-center gap-4 mt-3 text-xs text-gray-500">
              <span class="uppercase font-medium text-cyber-primary/80">
                {{ hotspot.source }}
              </span>
              <span>{{ formatTime(hotspot.discovered_at) }}</span>
              <span v-if="hotspot.matched_keywords?.length" class="flex items-center gap-1">
                <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/>
                </svg>
                {{ hotspot.matched_keywords.join(', ') }}
              </span>
              <a 
                :href="hotspot.url" 
                target="_blank"
                class="ml-auto text-cyber-primary hover:text-cyber-secondary"
                @click.stop
              >
                访问原文 →
              </a>
            </div>
          </div>
        </div>
      </a>
      
      <!-- 加载更多 -->
      <div class="text-center py-4">
        <button 
          v-if="hotspotsStore.hotspots.length < hotspotsStore.total"
          @click="loadMore"
          :disabled="hotspotsStore.loading"
          class="cyber-btn"
        >
          {{ hotspotsStore.loading ? '加载中...' : '加载更多' }}
        </button>
        <p v-else class="text-gray-500 text-sm">
          已加载全部 {{ hotspotsStore.total }} 条热点
        </p>
      </div>
    </div>
    
    <!-- 搜索弹窗 -->
    <Teleport to="body">
      <div 
        v-if="showSearchModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showSearchModal = false"></div>
        <div class="relative bg-cyber-darker border border-cyber-border rounded-xl p-6 w-full max-w-md animate-slide-up">
          <h3 class="text-lg font-semibold mb-4">搜索特定领域</h3>
          <p class="text-sm text-gray-400 mb-4">
            输入您感兴趣的领域（如"AI大模型"、"前端开发"），系统将从各数据源搜索相关热点。
          </p>
          <input 
            v-model="searchDomain"
            type="text"
            placeholder="输入领域关键词..."
            class="cyber-input mb-4"
            @keyup.enter="handleSearch"
          />
          <div class="flex justify-end gap-3">
            <button @click="showSearchModal = false" class="cyber-btn">
              取消
            </button>
            <button 
              @click="handleSearch"
              :disabled="searching || !searchDomain.trim()"
              class="cyber-btn-primary"
            >
              {{ searching ? '搜索中...' : '开始搜索' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
