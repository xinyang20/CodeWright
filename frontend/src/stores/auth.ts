import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest, RegisterRequest, LoginResponse } from '@/types'
import { authApi } from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const loading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // 动作
  const login = async (credentials: LoginRequest): Promise<void> => {
    loading.value = true
    try {
      const response = await authApi.login(credentials)
      if (response.code === 0) {
        const data = response.data as LoginResponse
        token.value = data.access_token
        user.value = data.user
        localStorage.setItem('token', data.access_token)
        console.log('登录成功')
      } else {
        throw new Error(response.message)
      }
    } catch (error: any) {
      console.error(error.message || '登录失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const register = async (userData: RegisterRequest): Promise<void> => {
    loading.value = true
    try {
      const response = await authApi.register(userData)
      if (response.code === 0) {
        console.log('注册成功，请登录')
      } else {
        throw new Error(response.message)
      }
    } catch (error: any) {
      console.error(error.message || '注册失败')
      throw error
    } finally {
      loading.value = false
    }
  }

  const logout = (): void => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    console.log('已退出登录')
  }

  const getCurrentUser = async (): Promise<void> => {
    if (!token.value) return
    
    try {
      const response = await authApi.getCurrentUser()
      if (response.code === 0) {
        user.value = response.data
      } else {
        // Token可能已过期，清除本地存储
        logout()
      }
    } catch (error) {
      logout()
    }
  }

  // 初始化时获取用户信息
  if (token.value) {
    getCurrentUser()
  }

  return {
    user: readonly(user),
    token: readonly(token),
    loading: readonly(loading),
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    getCurrentUser
  }
})
