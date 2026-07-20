import { createRouter, createWebHistory } from 'vue-router'

// = Views = //
import HomeView from '@/views/HomeView.vue'
import LoginView from '@/views/LoginView.vue'
import ProfileView from '@/views/ProfileView.vue'
import WorkspaceView from '@/views/WorkspaceView.vue'
import ReportView from '@/views/ReportView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
    },
    {
      path: '/workspace',
      name: 'workspace',
      component: WorkspaceView,
    }
  ],
})

export default router
