import { ref } from 'vue'

export const useAuth = () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const setUser = (newUser: any) => {
    user.value = newUser
    localStorage.setItem('user', JSON.stringify(newUser))
  }

  const clearAuth = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  const isAuthenticated = () => {
    return !!token.value
  }

  const isAdmin = () => {
    return user.value?.role === 'admin'
  }

  return {
    token,
    user,
    setToken,
    setUser,
    clearAuth,
    isAuthenticated,
    isAdmin
  }
}