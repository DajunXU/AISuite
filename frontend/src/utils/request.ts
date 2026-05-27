import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import router from '@/router'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 60000
})

request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      // 统一处理认证失败
      const isAuthError = status === 401 || 
        data?.detail === '无法验证凭据' || 
        (typeof data?.detail === 'string' && data.detail.includes('无法验证凭据'))
      
      if (isAuthError) {
        ElMessage.error('认证失败，请重新登录')
        const userStore = useUserStore()
        userStore.logout()
        router.push('/login')
        return Promise.reject(error)
      }
      
      switch (status) {
        case 403:
          ElMessage.error('没有权限访问')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        default:
          ElMessage.error(data.detail || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

// 权限管理 API
export const getRoles = () => {
  return request.get('/permission/roles')
}

export const createRole = (data: any) => {
  return request.post('/permission/roles', data)
}

export const updateRole = (id: number, data: any) => {
  return request.put(`/permission/roles/${id}`, data)
}

export const deleteRole = (id: number) => {
  return request.delete(`/permission/roles/${id}`)
}

export const getMenus = () => {
  return request.get('/permission/menus')
}

export const getUserMenus = () => {
  return request.get('/permission/user-menus')
}

export const createMenu = (data: any) => {
  return request.post('/permission/menus', data)
}

export const updateMenu = (id: number, data: any) => {
  return request.put(`/permission/menus/${id}`, data)
}

export const deleteMenu = (id: number) => {
  return request.delete(`/permission/menus/${id}`)
}

export const getPermissions = () => {
  return request.get('/permission/permissions')
}

export const createPermission = (data: any) => {
  return request.post('/permission/permissions', data)
}

export const updatePermission = (id: number, data: any) => {
  return request.put(`/permission/permissions/${id}`, data)
}

export const deletePermission = (id: number) => {
  return request.delete(`/permission/permissions/${id}`)
}

export const assignRolePermissions = (roleId: number, data: any) => {
  return request.post(`/permission/roles/${roleId}/permissions`, data)
}

export const getUserRoles = (userId: number) => {
  return request.get(`/permission/users/${userId}/roles`)
}

export const assignUserRoles = (userId: number, data: any) => {
  return request.post(`/permission/users/${userId}/roles`, data)
}

export default request
