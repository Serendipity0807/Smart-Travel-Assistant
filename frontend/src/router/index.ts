// 路由: / 首页(规划表单), /plan 行程结果页
import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    {
      path: '/plan',
      name: 'plan',
      component: () => import('@/views/PlanView.vue'), // 懒加载: 进结果页才下载
    },
  ],
})

export default router
