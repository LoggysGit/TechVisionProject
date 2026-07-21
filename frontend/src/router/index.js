import { createRouter, createWebHistory } from 'vue-router'

// = Views = //
import HomeView from '@/views/HomeView.vue'
import WorkspaceView from '@/views/WorkspaceView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/workspace',
      name: 'workspace',
      component: WorkspaceView,
    }
  ],
})

export default router
