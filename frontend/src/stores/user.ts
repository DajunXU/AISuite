import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'
import { usePermissionStore } from './permission'
import { resetPermissionLoaded } from '@/router'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const isAuthenticated = ref(!!token.value)

  const login = async (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await request.post('/auth/login', formData)
    
    if (response.access_token) {
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)
      isAuthenticated.value = true
      
      // 获取用户信息
      await getUserInfo()
    }
    
    return response
  }

  const register = async (userData: {
    username: string
    email: string
    password: string
    full_name?: string
  }) => {
    const response = await request.post('/auth/register', userData)
    return response
  }

  const getUserInfo = async () => {
    try {
      const response = await request.get('/auth/me')
      user.value = response
      localStorage.setItem('user', JSON.stringify(response))
      
      const permissionStore = usePermissionStore()
      await permissionStore.loadUserPermissions()
      
      return response
    } catch (error) {
      logout()
      throw error
    }
  }

  const logout = async () => {
    try {
      await request.post('/auth/logout')
    } catch (error) {
      console.error('登出请求失败:', error)
    }
    
    token.value = ''
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    
    const permissionStore = usePermissionStore()
    permissionStore.clearPermissions()
    resetPermissionLoaded()
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    getUserInfo,
    logout
  }
})