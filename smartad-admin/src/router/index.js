import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    redirect: '/strategy',
    children: [
      {
        path: 'strategy',
        name: 'Strategy',
        component: () => import('@/views/strategy/StrategyList.vue'),
        meta: { title: '策略管理', icon: 'DataLine' },
      },
      {
        path: 'report',
        name: 'Report',
        component: () => import('@/views/report/ReportList.vue'),
        meta: { title: '投放报表', icon: 'TrendCharts' },
      },
      {
        path: 'alert',
        name: 'Alert',
        component: () => import('@/views/alert/AlertList.vue'),
        meta: { title: '告警管理', icon: 'Bell' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth !== false && !token) {
    return '/login'
  }
  if (to.path === '/login' && token) {
    return '/'
  }
})

export default router
