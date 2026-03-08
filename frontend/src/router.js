import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('./views/Dashboard.vue'),
    meta: { title: '仪表盘' }
  },
  {
    path: '/hotspots',
    name: 'Hotspots',
    component: () => import('./views/Hotspots.vue'),
    meta: { title: '热点列表' }
  },
  {
    path: '/keywords',
    name: 'Keywords',
    component: () => import('./views/Keywords.vue'),
    meta: { title: '关键词管理' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('./views/Settings.vue'),
    meta: { title: '系统设置' }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 更新页面标题
router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'Home'} - Hot Monitor`
  next()
})

export default router
