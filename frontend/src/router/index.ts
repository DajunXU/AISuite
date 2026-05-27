import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { usePermissionStore } from '@/stores/permission'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/knowledge/manager',
      name: 'KnowledgeBaseManager',
      component: () => import('@/views/KnowledgeBase.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/knowledge/authority',
      name: 'KnowledgeBaseAuthority',
      component: () => import('@/views/KnowledgeBaseAuthority.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/knowledge',
      name: 'KnowledgeBase',
      redirect: '/knowledge/manager'
    },
    {
      path: '/knowledge/:id',
      name: 'KnowledgeBaseDetail',
      component: () => import('@/views/KnowledgeBaseDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('@/views/Chat.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/dialog/:code',
      name: 'PublicDialog',
      component: () => import('@/views/PublicDialog.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/public-dialog',
      name: 'PublicDialogManagement',
      component: () => import('@/views/PublicDialogManagement.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      name: 'Admin',
      component: () => import('@/views/Admin/Admin.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/llm',
      name: 'LLMManagement',
      component: () => import('@/views/LLMManagement.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/embedding',
      name: 'EmbeddingModelManagement',
      component: () => import('@/views/EmbeddingModelManagement.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/admin/permission',
      name: 'PermissionManagement',
      component: () => import('@/views/Admin/PermissionManagement.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/audit',
      name: 'Audit',
      component: () => import('@/views/Audit.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('@/views/Profile.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ]
})

let permissionLoaded = false

export const resetPermissionLoaded = () => {
  permissionLoaded = false
}

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  
  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresAuth && userStore.isAuthenticated && !permissionLoaded) {
    const permissionStore = usePermissionStore()
    await permissionStore.loadUserPermissions()
    permissionLoaded = true
    
    if (to.meta.requiresAdmin && userStore.user?.role !== 'admin') {
      next('/')
    } else {
      next()
    }
  } else if (to.meta.requiresAdmin && userStore.user?.role !== 'admin') {
    next('/')
  } else {
    next()
  }
})

export default router
