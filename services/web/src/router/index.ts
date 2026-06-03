import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '../composables/useAuth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      name: 'workbench',
      component: () => import('../views/WorkbenchView.vue'),
    },
  ],
})

router.beforeEach((to) => {
  if (to.meta.public) {
    if (to.name === 'login' && isAuthenticated()) {
      return { name: 'workbench' }
    }
    return true
  }
  if (!isAuthenticated()) {
    return { name: 'login' }
  }
  return true
})

export default router
