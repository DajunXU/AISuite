import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request, { getUserMenus } from '@/utils/request'

export const usePermissionStore = defineStore('permission', () => {
  const userPermissions = ref<string[]>([])
  const userRoles = ref<any[]>([])
  const menus = ref<any[]>([])
  const loading = ref(false)

  const hasPermission = (permission: string) => {
    return userPermissions.value.includes(permission)
  }

  const hasRole = (roleName: string) => {
    return userRoles.value.some(role => role.name === roleName)
  }

  const canAccessMenu = (menuPath: string) => {
    const menu = menus.value.find(m => m.path === menuPath)
    if (!menu) return false
    return true
  }

  const getAccessibleMenus = () => {
    return menus.value
  }

  const loadUserPermissions = async () => {
    loading.value = true
    try {
      const rolesResponse = await request.get('/permission/user/roles')
      userRoles.value = rolesResponse.roles || []

      const permissions = new Set<string>()
      for (const role of userRoles.value) {
        if (role.permissions) {
          role.permissions.forEach((p: any) => {
            permissions.add(p.code)
          })
        }
      }
      userPermissions.value = Array.from(permissions)

      const menusResponse = await request.get('/permission/user-menus')
      menus.value = menusResponse.menus || []
    } catch (error) {
      console.error('加载用户权限失败:', error)
    } finally {
      loading.value = false
    }
  }

  const clearPermissions = () => {
    userPermissions.value = []
    userRoles.value = []
    menus.value = []
  }

  return {
    userPermissions,
    userRoles,
    menus,
    loading,
    hasPermission,
    hasRole,
    canAccessMenu,
    getAccessibleMenus,
    loadUserPermissions,
    clearPermissions
  }
})
