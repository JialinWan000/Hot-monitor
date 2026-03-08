<script setup>
import { onMounted, ref, reactive, computed } from 'vue'
import { useSettingsStore } from '../stores'
import { notificationsApi, systemApi } from '../api'

const settingsStore = useSettingsStore()

const testingPush = ref(false)
const testingEmail = ref(false)
const saving = ref(false)
const vapidKey = ref('')
const pushSubscribed = ref(false)

const notifyForm = reactive({
  email_enabled: false,
  email_address: '',
  push_enabled: false,
  notify_on_match: true,
  notify_on_high_score: true,
  min_score_threshold: 7,
})

const crawlerForm = reactive({
  crawl_interval: 30,
  enabled_sources: [],
})

const allSources = [
  { id: 'hackernews', name: 'Hacker News', icon: '🔶' },
  { id: 'github', name: 'GitHub Trending', icon: '🐙' },
  { id: 'twitter', name: 'Twitter/X', icon: '🐦' },
  { id: 'reddit', name: 'Reddit', icon: '🤖' },
  { id: 'zhihu', name: '知乎热榜', icon: '知' },
  { id: 'bing', name: 'Bing News', icon: '🔍' },
  { id: 'google', name: 'Google News', icon: '🔎' },
  { id: 'duckduckgo', name: 'DuckDuckGo', icon: '🦆' },
]

onMounted(async () => {
  await settingsStore.fetchSettings()
  
  // 初始化表单
  Object.assign(notifyForm, settingsStore.notificationSettings)
  Object.assign(crawlerForm, {
    crawl_interval: settingsStore.systemSettings.crawl_interval || 30,
    enabled_sources: (settingsStore.systemSettings.enabled_sources || 'hackernews,github,reddit').split(','),
  })
  
  // 获取 VAPID key
  try {
    const result = await systemApi.getVapidKey()
    vapidKey.value = result.vapid_public_key
  } catch (e) {
    console.error('获取 VAPID key 失败')
  }
  
  // 检查推送订阅状态
  checkPushSubscription()
})

async function checkPushSubscription() {
  if ('serviceWorker' in navigator && 'PushManager' in window) {
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.getSubscription()
    pushSubscribed.value = !!subscription
  }
}

async function handleSaveNotifications() {
  saving.value = true
  try {
    await settingsStore.updateNotificationSettings(notifyForm)
    alert('通知设置已保存')
  } catch (error) {
    alert('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

async function handleSaveCrawler() {
  saving.value = true
  try {
    await settingsStore.updateSystemSetting('crawl_interval', crawlerForm.crawl_interval)
    await settingsStore.updateSystemSetting('enabled_sources', crawlerForm.enabled_sources.join(','))
    alert('爬虫设置已保存')
  } catch (error) {
    alert('保存失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

async function subscribePush() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    alert('您的浏览器不支持推送通知')
    return
  }
  
  try {
    const permission = await Notification.requestPermission()
    if (permission !== 'granted') {
      alert('需要通知权限才能接收推送')
      return
    }
    
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: vapidKey.value,
    })
    
    await notificationsApi.subscribe({
      endpoint: subscription.endpoint,
      keys: {
        p256dh: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('p256dh')))),
        auth: btoa(String.fromCharCode(...new Uint8Array(subscription.getKey('auth')))),
      }
    })
    
    pushSubscribed.value = true
    alert('推送订阅成功！')
  } catch (error) {
    console.error('订阅失败:', error)
    alert('订阅失败: ' + error.message)
  }
}

async function unsubscribePush() {
  try {
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.getSubscription()
    
    if (subscription) {
      await notificationsApi.unsubscribe(subscription.endpoint)
      await subscription.unsubscribe()
    }
    
    pushSubscribed.value = false
    alert('已取消推送订阅')
  } catch (error) {
    alert('取消订阅失败: ' + error.message)
  }
}

async function testPush() {
  testingPush.value = true
  try {
    await notificationsApi.test('push')
    alert('测试推送已发送，请检查浏览器通知')
  } catch (error) {
    alert('测试失败: ' + error.message)
  } finally {
    testingPush.value = false
  }
}

async function testEmail() {
  testingEmail.value = true
  try {
    await notificationsApi.test('email')
    alert('测试邮件已发送，请检查邮箱')
  } catch (error) {
    alert('测试失败: ' + error.message)
  } finally {
    testingEmail.value = false
  }
}

function toggleSource(sourceId) {
  const index = crawlerForm.enabled_sources.indexOf(sourceId)
  if (index === -1) {
    crawlerForm.enabled_sources.push(sourceId)
  } else {
    crawlerForm.enabled_sources.splice(index, 1)
  }
}
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- 页面标题 -->
    <div>
      <h1 class="text-2xl font-bold font-orbitron cyber-gradient-text">SETTINGS</h1>
      <p class="text-gray-500 text-sm mt-1">配置系统参数与通知选项</p>
    </div>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 通知设置 -->
      <div class="cyber-card">
        <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-cyber-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 01-3.46 0"/>
          </svg>
          通知设置
        </h2>
        
        <div class="space-y-4">
          <!-- 浏览器推送 -->
          <div class="p-4 rounded-lg border border-cyber-border">
            <div class="flex items-center justify-between mb-3">
              <div>
                <h3 class="font-medium">浏览器推送</h3>
                <p class="text-sm text-gray-500">接收实时浏览器推送通知</p>
              </div>
              <button
                @click="notifyForm.push_enabled = !notifyForm.push_enabled"
                :class="[
                  'relative w-12 h-6 rounded-full transition-colors',
                  notifyForm.push_enabled ? 'bg-cyber-primary' : 'bg-cyber-border'
                ]"
              >
                <span
                  :class="[
                    'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
                    notifyForm.push_enabled ? 'left-7' : 'left-1'
                  ]"
                ></span>
              </button>
            </div>
            
            <div v-if="notifyForm.push_enabled" class="flex gap-2">
              <button
                v-if="!pushSubscribed"
                @click="subscribePush"
                class="cyber-btn text-sm"
              >
                订阅推送
              </button>
              <template v-else>
                <button
                  @click="testPush"
                  :disabled="testingPush"
                  class="cyber-btn text-sm"
                >
                  {{ testingPush ? '发送中...' : '测试推送' }}
                </button>
                <button
                  @click="unsubscribePush"
                  class="cyber-btn-danger text-sm"
                >
                  取消订阅
                </button>
              </template>
            </div>
          </div>
          
          <!-- 邮件通知 -->
          <div class="p-4 rounded-lg border border-cyber-border">
            <div class="flex items-center justify-between mb-3">
              <div>
                <h3 class="font-medium">邮件通知</h3>
                <p class="text-sm text-gray-500">发送邮件到您的邮箱</p>
              </div>
              <button
                @click="notifyForm.email_enabled = !notifyForm.email_enabled"
                :class="[
                  'relative w-12 h-6 rounded-full transition-colors',
                  notifyForm.email_enabled ? 'bg-cyber-primary' : 'bg-cyber-border'
                ]"
              >
                <span
                  :class="[
                    'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
                    notifyForm.email_enabled ? 'left-7' : 'left-1'
                  ]"
                ></span>
              </button>
            </div>
            
            <div v-if="notifyForm.email_enabled" class="space-y-3">
              <input
                v-model="notifyForm.email_address"
                type="email"
                placeholder="your@email.com"
                class="cyber-input"
              />
              <button
                @click="testEmail"
                :disabled="testingEmail || !notifyForm.email_address"
                class="cyber-btn text-sm"
              >
                {{ testingEmail ? '发送中...' : '测试邮件' }}
              </button>
            </div>
          </div>
          
          <!-- 通知触发条件 -->
          <div class="space-y-3 pt-2">
            <label class="flex items-center gap-3 cursor-pointer">
              <input 
                v-model="notifyForm.notify_on_match" 
                type="checkbox" 
                class="w-4 h-4 rounded border-cyber-border bg-cyber-darker text-cyber-primary focus:ring-cyber-primary/30"
              />
              <span class="text-sm">关键词匹配时通知</span>
            </label>
            
            <label class="flex items-center gap-3 cursor-pointer">
              <input 
                v-model="notifyForm.notify_on_high_score" 
                type="checkbox" 
                class="w-4 h-4 rounded border-cyber-border bg-cyber-darker text-cyber-primary focus:ring-cyber-primary/30"
              />
              <span class="text-sm">高分热点通知（AI评分 ≥ {{ notifyForm.min_score_threshold }}）</span>
            </label>
            
            <div v-if="notifyForm.notify_on_high_score" class="flex items-center gap-3 ml-7">
              <input
                v-model.number="notifyForm.min_score_threshold"
                type="range"
                min="5"
                max="10"
                class="flex-1 accent-cyber-primary"
              />
              <span class="text-sm text-cyber-primary font-mono w-8">{{ notifyForm.min_score_threshold }}</span>
            </div>
          </div>
          
          <button 
            @click="handleSaveNotifications"
            :disabled="saving"
            class="cyber-btn-primary w-full mt-4"
          >
            {{ saving ? '保存中...' : '保存通知设置' }}
          </button>
        </div>
      </div>
      
      <!-- 爬虫设置 -->
      <div class="cyber-card">
        <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <svg class="w-5 h-5 text-cyber-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/>
          </svg>
          数据源设置
        </h2>
        
        <div class="space-y-4">
          <!-- 抓取间隔 -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">自动抓取间隔（分钟）</label>
            <div class="flex items-center gap-4">
              <input
                v-model.number="crawlerForm.crawl_interval"
                type="range"
                min="10"
                max="120"
                step="5"
                class="flex-1 accent-cyber-primary"
              />
              <span class="text-lg font-mono text-cyber-primary w-12 text-right">
                {{ crawlerForm.crawl_interval }}
              </span>
            </div>
            <p class="text-xs text-gray-500 mt-1">
              系统将每 {{ crawlerForm.crawl_interval }} 分钟自动抓取新热点
            </p>
          </div>
          
          <!-- 数据源选择 -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">启用的数据源</label>
            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="source in allSources"
                :key="source.id"
                @click="toggleSource(source.id)"
                :class="[
                  'p-3 rounded-lg border text-left transition-all flex items-center gap-2',
                  crawlerForm.enabled_sources.includes(source.id)
                    ? 'border-cyber-primary bg-cyber-primary/10'
                    : 'border-cyber-border hover:border-cyber-primary/30'
                ]"
              >
                <span class="text-xl">{{ source.icon }}</span>
                <span class="text-sm">{{ source.name }}</span>
              </button>
            </div>
          </div>
          
          <button 
            @click="handleSaveCrawler"
            :disabled="saving || crawlerForm.enabled_sources.length === 0"
            class="cyber-btn-primary w-full mt-4"
          >
            {{ saving ? '保存中...' : '保存数据源设置' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 系统信息 -->
    <div class="cyber-card">
      <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
        <svg class="w-5 h-5 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="16" x2="12" y2="12"/>
          <line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
        系统信息
      </h2>
      
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <span class="text-gray-500">版本</span>
          <p class="font-mono">v1.0.0</p>
        </div>
        <div>
          <span class="text-gray-500">后端状态</span>
          <p class="flex items-center gap-1">
            <span class="w-2 h-2 rounded-full bg-cyber-success"></span>
            运行中
          </p>
        </div>
        <div>
          <span class="text-gray-500">数据库</span>
          <p class="font-mono">SQLite</p>
        </div>
        <div>
          <span class="text-gray-500">AI服务</span>
          <p class="font-mono">OpenRouter</p>
        </div>
      </div>
    </div>
  </div>
</template>
