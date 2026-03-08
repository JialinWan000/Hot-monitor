import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { keywordsApi, hotspotsApi, systemApi, notificationsApi } from '../api'

// 关键词 Store
export const useKeywordsStore = defineStore('keywords', () => {
  const keywords = ref([])
  const loading = ref(false)
  
  const activeKeywords = computed(() => 
    keywords.value.filter(k => k.is_active)
  )
  
  async function fetchKeywords() {
    loading.value = true
    try {
      keywords.value = await keywordsApi.getAll()
    } finally {
      loading.value = false
    }
  }
  
  async function addKeyword(data) {
    const newKeyword = await keywordsApi.create(data)
    keywords.value.unshift(newKeyword)
    return newKeyword
  }
  
  async function updateKeyword(id, data) {
    const updated = await keywordsApi.update(id, data)
    const index = keywords.value.findIndex(k => k.id === id)
    if (index !== -1) {
      keywords.value[index] = updated
    }
    return updated
  }
  
  async function deleteKeyword(id) {
    await keywordsApi.delete(id)
    keywords.value = keywords.value.filter(k => k.id !== id)
  }
  
  async function toggleKeyword(id) {
    const updated = await keywordsApi.toggle(id)
    const index = keywords.value.findIndex(k => k.id === id)
    if (index !== -1) {
      keywords.value[index] = updated
    }
    return updated
  }
  
  return {
    keywords,
    loading,
    activeKeywords,
    fetchKeywords,
    addKeyword,
    updateKeyword,
    deleteKeyword,
    toggleKeyword,
  }
})

// 热点 Store
export const useHotspotsStore = defineStore('hotspots', () => {
  const hotspots = ref([])
  const sources = ref([])
  const loading = ref(false)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  
  const unreadCount = computed(() =>
    hotspots.value.filter(h => !h.read).length
  )
  
  async function fetchHotspots(params = {}) {
    loading.value = true
    try {
      const result = await hotspotsApi.getAll({
        page: page.value,
        page_size: pageSize.value,
        ...params,
      })
      hotspots.value = result.items
      total.value = result.total
    } finally {
      loading.value = false
    }
  }
  
  async function fetchSources() {
    const result = await hotspotsApi.getSources()
    sources.value = result.sources
  }
  
  async function markAsRead(id) {
    await hotspotsApi.markAsRead(id)
    const hotspot = hotspots.value.find(h => h.id === id)
    if (hotspot) {
      hotspot.read = true
    }
  }
  
  async function markAllAsRead() {
    await hotspotsApi.markAllAsRead()
    hotspots.value.forEach(h => h.read = true)
  }
  
  async function refresh() {
    await hotspotsApi.refresh()
  }
  
  async function searchDomain(domain, sources = null) {
    await hotspotsApi.search({ domain, sources })
  }
  
  return {
    hotspots,
    sources,
    loading,
    total,
    page,
    pageSize,
    unreadCount,
    fetchHotspots,
    fetchSources,
    markAsRead,
    markAllAsRead,
    refresh,
    searchDomain,
  }
})

// 仪表盘 Store
export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref({
    total_keywords: 0,
    active_keywords: 0,
    total_hotspots: 0,
    unread_hotspots: 0,
    today_hotspots: 0,
    notifications_sent: 0,
  })
  const loading = ref(false)
  
  async function fetchStats() {
    loading.value = true
    try {
      stats.value = await systemApi.getDashboard()
    } finally {
      loading.value = false
    }
  }
  
  return {
    stats,
    loading,
    fetchStats,
  }
})

// 设置 Store
export const useSettingsStore = defineStore('settings', () => {
  const systemSettings = ref({})
  const notificationSettings = ref({})
  const loading = ref(false)
  
  async function fetchSettings() {
    loading.value = true
    try {
      const [sys, notify] = await Promise.all([
        systemApi.getSettings(),
        notificationsApi.getSettings(),
      ])
      systemSettings.value = sys
      notificationSettings.value = notify
    } finally {
      loading.value = false
    }
  }
  
  async function updateSystemSetting(key, value) {
    await systemApi.updateSetting({ key, value: String(value) })
    systemSettings.value[key] = value
  }
  
  async function updateNotificationSettings(data) {
    await notificationsApi.updateSettings(data)
    Object.assign(notificationSettings.value, data)
  }
  
  return {
    systemSettings,
    notificationSettings,
    loading,
    fetchSettings,
    updateSystemSetting,
    updateNotificationSettings,
  }
})
