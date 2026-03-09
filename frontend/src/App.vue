<script setup>
import { RouterView, RouterLink, useRoute } from 'vue-router'
import { ref, computed, onMounted } from 'vue'
import { useHotspotsStore, useDashboardStore } from './stores'

const route = useRoute()
const hotspotsStore = useHotspotsStore()
const dashboardStore = useDashboardStore()

const sidebarCollapsed = ref(false)

const navItems = [
  { path: '/', name: 'Dashboard', icon: 'dashboard', label: '仪表盘' },
  { path: '/hotspots', name: 'Hotspots', icon: 'fire', label: '热点列表' },
  { path: '/keywords', name: 'Keywords', icon: 'tag', label: '关键词' },
  { path: '/settings', name: 'Settings', icon: 'settings', label: '设置' },
]

const currentTime = ref(new Date())

onMounted(() => {
  setInterval(() => {
    currentTime.value = new Date()
  }, 1000)
  
  dashboardStore.fetchStats()
})

const formattedTime = computed(() => {
  return currentTime.value.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
})

const formattedDate = computed(() => {
  return currentTime.value.toLocaleDateString('zh-CN', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
})
</script>

<template>
  <div class="min-h-screen bg-cyber-dark text-gray-100 flex">
    <!-- 侧边栏 -->
    <aside 
      :class="[
        'fixed left-0 top-0 h-full bg-cyber-darker border-r border-cyber-border z-50',
        'transition-all duration-300 flex flex-col',
        sidebarCollapsed ? 'w-16' : 'w-64'
      ]"
    >
      <!-- Logo -->
      <div class="p-4 border-b border-cyber-border">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-cyber-primary to-cyber-secondary flex items-center justify-center">
            <svg class="w-6 h-6 text-cyber-dark" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span v-if="!sidebarCollapsed" class="font-orbitron text-lg font-bold cyber-gradient-text">
            HOT MONITOR
          </span>
        </div>
      </div>
      
      <!-- 导航 -->
      <nav class="flex-1 p-3 space-y-2">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
            route.path === item.path 
              ? 'bg-cyber-primary/10 text-cyber-primary border border-cyber-primary/30' 
              : 'text-gray-400 hover:bg-cyber-card hover:text-gray-200'
          ]"
        >
          <!-- 图标 -->
          <svg class="w-5 h-5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <template v-if="item.icon === 'dashboard'">
              <rect x="3" y="3" width="7" height="7" rx="1"/>
              <rect x="14" y="3" width="7" height="7" rx="1"/>
              <rect x="3" y="14" width="7" height="7" rx="1"/>
              <rect x="14" y="14" width="7" height="7" rx="1"/>
            </template>
            <template v-else-if="item.icon === 'fire'">
              <path d="M12 2c.5 3-1 6-3 8s-4 3-4 6c0 4 4 6 7 6s7-2 7-6c0-2-1-4-2-5s-2-2-2-4c0-1.5.5-3 1-4-1.5 1-4 2-4-1z"/>
            </template>
            <template v-else-if="item.icon === 'tag'">
              <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/>
              <circle cx="7" cy="7" r="1"/>
            </template>
            <template v-else-if="item.icon === 'settings'">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
            </template>
          </svg>
          <span v-if="!sidebarCollapsed" class="font-medium">{{ item.label }}</span>
          
          <!-- 未读数量徽章 -->
          <span 
            v-if="item.icon === 'fire' && dashboardStore.stats.unread_hotspots > 0 && !sidebarCollapsed"
            class="ml-auto px-2 py-0.5 text-xs rounded-full bg-cyber-danger text-white"
          >
            {{ dashboardStore.stats.unread_hotspots > 99 ? '99+' : dashboardStore.stats.unread_hotspots }}
          </span>
        </RouterLink>
      </nav>
      
      <!-- 底部状态 -->
      <div class="p-4 border-t border-cyber-border">
        <div v-if="!sidebarCollapsed" class="text-xs text-gray-500 space-y-1">
          <div class="flex justify-between">
            <span>{{ formattedDate }}</span>
            <span class="text-cyber-primary font-mono">{{ formattedTime }}</span>
          </div>
          <div class="flex items-center gap-1">
            <span class="w-2 h-2 rounded-full bg-cyber-success animate-pulse"></span>
            <span>系统运行中</span>
          </div>
        </div>
        <button 
          @click="sidebarCollapsed = !sidebarCollapsed"
          class="w-full mt-2 p-2 rounded hover:bg-cyber-card transition-colors"
        >
          <svg 
            :class="['w-5 h-5 mx-auto transition-transform', sidebarCollapsed ? 'rotate-180' : '']" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            stroke-width="2"
          >
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
      </div>
    </aside>
    
    <!-- 主内容区 -->
    <main 
      :class="[
        'flex-1 min-h-screen transition-all duration-300',
        sidebarCollapsed ? 'ml-16' : 'ml-64'
      ]"
    >
      <div class="p-6">
        <RouterView v-slot="{ Component, route }">
          <transition name="fade" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </RouterView>
      </div>
    </main>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
