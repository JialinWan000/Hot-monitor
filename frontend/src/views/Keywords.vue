<script setup>
import { onMounted, ref, computed } from 'vue'
import { useKeywordsStore } from '../stores'

const keywordsStore = useKeywordsStore()

const showModal = ref(false)
const editingKeyword = ref(null)
const form = ref({
  keyword: '',
  description: '',
  priority: 'normal',
})

const priorities = [
  { value: 'low', label: '低', color: 'gray' },
  { value: 'normal', label: '普通', color: 'primary' },
  { value: 'high', label: '高', color: 'warning' },
  { value: 'critical', label: '紧急', color: 'danger' },
]

onMounted(() => {
  keywordsStore.fetchKeywords()
})

const sortedKeywords = computed(() => {
  const priorityOrder = { critical: 0, high: 1, normal: 2, low: 3 }
  return [...keywordsStore.keywords].sort((a, b) => {
    // 活跃的排前面
    if (a.is_active !== b.is_active) return b.is_active - a.is_active
    // 按优先级排序
    return priorityOrder[a.priority] - priorityOrder[b.priority]
  })
})

function openAddModal() {
  editingKeyword.value = null
  form.value = { keyword: '', description: '', priority: 'normal' }
  showModal.value = true
}

function openEditModal(keyword) {
  editingKeyword.value = keyword
  form.value = {
    keyword: keyword.keyword,
    description: keyword.description || '',
    priority: keyword.priority || 'normal',
  }
  showModal.value = true
}

async function handleSubmit() {
  if (!form.value.keyword.trim()) return
  
  try {
    if (editingKeyword.value) {
      await keywordsStore.updateKeyword(editingKeyword.value.id, form.value)
    } else {
      await keywordsStore.addKeyword(form.value)
    }
    showModal.value = false
  } catch (error) {
    console.error('保存失败:', error)
  }
}

async function handleDelete(id) {
  if (confirm('确定要删除这个关键词吗？')) {
    await keywordsStore.deleteKeyword(id)
  }
}

function getPriorityClass(priority) {
  const classes = {
    low: 'border-gray-500/30 bg-gray-500/10 text-gray-400',
    normal: 'border-cyber-primary/30 bg-cyber-primary/10 text-cyber-primary',
    high: 'border-cyber-warning/30 bg-cyber-warning/10 text-cyber-warning',
    critical: 'border-cyber-danger/30 bg-cyber-danger/10 text-cyber-danger',
  }
  return classes[priority] || classes.normal
}

function getPriorityLabel(priority) {
  return priorities.find(p => p.value === priority)?.label || '普通'
}
</script>

<template>
  <div class="space-y-6 animate-fade-in">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold font-orbitron cyber-gradient-text">KEYWORDS</h1>
        <p class="text-gray-500 text-sm mt-1">管理监控关键词，及时发现相关热点</p>
      </div>
      <button @click="openAddModal" class="cyber-btn-primary flex items-center gap-2">
        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        <span>添加关键词</span>
      </button>
    </div>
    
    <!-- 统计信息 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="stat-card text-center">
        <p class="text-2xl font-bold text-cyber-primary font-mono">{{ keywordsStore.keywords.length }}</p>
        <p class="text-sm text-gray-500">总关键词</p>
      </div>
      <div class="stat-card text-center">
        <p class="text-2xl font-bold text-cyber-success font-mono">{{ keywordsStore.activeKeywords.length }}</p>
        <p class="text-sm text-gray-500">活跃监控</p>
      </div>
      <div class="stat-card text-center">
        <p class="text-2xl font-bold text-cyber-warning font-mono">
          {{ keywordsStore.keywords.filter(k => k.priority === 'high' || k.priority === 'critical').length }}
        </p>
        <p class="text-sm text-gray-500">高优先级</p>
      </div>
      <div class="stat-card text-center">
        <p class="text-2xl font-bold text-cyber-secondary font-mono">
          {{ keywordsStore.keywords.reduce((sum, k) => sum + (k.match_count || 0), 0) }}
        </p>
        <p class="text-sm text-gray-500">总匹配数</p>
      </div>
    </div>
    
    <!-- 关键词列表 -->
    <div v-if="keywordsStore.loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="cyber-card animate-pulse">
        <div class="h-6 bg-cyber-border rounded w-1/2 mb-3"></div>
        <div class="h-4 bg-cyber-border rounded w-3/4"></div>
      </div>
    </div>
    
    <div v-else-if="keywordsStore.keywords.length === 0" class="cyber-card text-center py-16">
      <svg class="w-20 h-20 mx-auto mb-4 text-gray-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
        <path d="M20.59 13.41l-7.17 7.17a2 2 0 01-2.83 0L2 12V2h10l8.59 8.59a2 2 0 010 2.82z"/>
        <circle cx="7" cy="7" r="1"/>
      </svg>
      <p class="text-gray-400 text-lg">暂无关键词</p>
      <p class="text-gray-500 text-sm mt-2">添加关键词以监控相关热点</p>
      <button @click="openAddModal" class="cyber-btn-primary mt-4">
        添加第一个关键词
      </button>
    </div>
    
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="keyword in sortedKeywords"
        :key="keyword.id"
        :class="[
          'keyword-card group transition-all duration-300',
          !keyword.is_active && 'opacity-60'
        ]"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-2 flex-1 min-w-0">
            <span 
              :class="[
                'px-2 py-0.5 text-xs rounded border',
                getPriorityClass(keyword.priority)
              ]"
            >
              {{ getPriorityLabel(keyword.priority) }}
            </span>
            <h3 class="font-medium truncate">{{ keyword.keyword }}</h3>
          </div>
          
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button 
              @click="openEditModal(keyword)"
              class="p-1 hover:text-cyber-primary transition-colors"
              title="编辑"
            >
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
            </button>
            <button 
              @click="handleDelete(keyword.id)"
              class="p-1 hover:text-cyber-danger transition-colors"
              title="删除"
            >
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
              </svg>
            </button>
          </div>
        </div>
        
        <p v-if="keyword.description" class="text-sm text-gray-500 mb-3 line-clamp-2">
          {{ keyword.description }}
        </p>
        
        <div class="flex items-center justify-between pt-3 border-t border-cyber-border">
          <div class="flex items-center gap-4 text-xs text-gray-500">
            <span class="flex items-center gap-1">
              <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2c.5 3-1 6-3 8s-4 3-4 6c0 4 4 6 7 6s7-2 7-6c0-2-1-4-2-5s-2-2-2-4c0-1.5.5-3 1-4-1.5 1-4 2-4-1z"/>
              </svg>
              {{ keyword.match_count || 0 }} 匹配
            </span>
          </div>
          
          <button
            @click="keywordsStore.toggleKeyword(keyword.id)"
            :class="[
              'relative w-12 h-6 rounded-full transition-colors',
              keyword.is_active ? 'bg-cyber-primary' : 'bg-cyber-border'
            ]"
          >
            <span
              :class="[
                'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
                keyword.is_active ? 'left-7' : 'left-1'
              ]"
            ></span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 添加/编辑弹窗 -->
    <Teleport to="body">
      <div 
        v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
      >
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showModal = false"></div>
        <div class="relative bg-cyber-darker border border-cyber-border rounded-xl p-6 w-full max-w-md animate-slide-up">
          <h3 class="text-lg font-semibold mb-4">
            {{ editingKeyword ? '编辑关键词' : '添加关键词' }}
          </h3>
          
          <form @submit.prevent="handleSubmit" class="space-y-4">
            <div>
              <label class="block text-sm text-gray-400 mb-1">关键词 *</label>
              <input 
                v-model="form.keyword"
                type="text"
                required
                placeholder="例如：GPT-5、Claude、AI模型"
                class="cyber-input"
              />
            </div>
            
            <div>
              <label class="block text-sm text-gray-400 mb-1">描述</label>
              <textarea 
                v-model="form.description"
                rows="2"
                placeholder="关键词的描述信息（可选）"
                class="cyber-input resize-none"
              ></textarea>
            </div>
            
            <div>
              <label class="block text-sm text-gray-400 mb-2">优先级</label>
              <div class="grid grid-cols-4 gap-2">
                <button
                  v-for="p in priorities"
                  :key="p.value"
                  type="button"
                  @click="form.priority = p.value"
                  :class="[
                    'py-2 rounded border text-sm transition-all',
                    form.priority === p.value 
                      ? getPriorityClass(p.value) 
                      : 'border-cyber-border text-gray-500 hover:border-cyber-primary/30'
                  ]"
                >
                  {{ p.label }}
                </button>
              </div>
            </div>
            
            <div class="flex justify-end gap-3 pt-4">
              <button type="button" @click="showModal = false" class="cyber-btn">
                取消
              </button>
              <button type="submit" class="cyber-btn-primary">
                {{ editingKeyword ? '保存' : '添加' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>
  </div>
</template>
