<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>CodeWright</h1>
        <p>登录到代码版权工匠</p>
      </div>

      <form class="login-form" @submit.prevent="handleSubmit">
        <div class="form-item">
          <input
            v-model="form.username"
            type="text"
            placeholder="请输入用户名"
            class="form-input"
            required
          />
        </div>

        <div class="form-item">
          <input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            class="form-input"
            required
          />
        </div>

        <div class="form-item">
          <button
            type="submit"
            class="btn btn-primary btn-large login-button"
            :disabled="authStore.loading"
          >
            {{ authStore.loading ? '登录中...' : '登录' }}
          </button>
        </div>
      </form>

      <div class="login-footer">
        <p>
          还没有账号？
          <router-link to="/register" class="link">立即注册</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { LoginRequest } from '@/types'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = reactive<LoginRequest>({
  username: '',
  password: ''
})

const getLoginErrorMessage = (error: unknown): string => {
  if (typeof error === 'string') {
    return error
  }

  if (typeof error === 'object' && error !== null) {
    const apiError = error as {
      code?: unknown
      detail?: unknown
      message?: unknown
    }

    if (apiError.message === 'Network Error' || apiError.code === 'ERR_NETWORK') {
      return '无法连接后端服务，请确认后端已启动在 127.0.0.1:8001'
    }

    if (typeof apiError.message === 'string' && apiError.message.trim()) {
      return apiError.message
    }

    if (typeof apiError.detail === 'string' && apiError.detail.trim()) {
      return apiError.detail
    }
  }

  return '登录失败，请检查用户名和密码'
}

const handleSubmit = async () => {
  if (authStore.loading) {
    return
  }

  if (!form.username || !form.password) {
    alert('请填写用户名和密码')
    return
  }

  if (form.username.length < 3 || form.username.length > 50) {
    alert('用户名长度在 3 到 50 个字符')
    return
  }

  if (form.password.length < 6) {
    alert('密码长度不能少于 6 个字符')
    return
  }

  try {
    await authStore.login(form)

    // 登录成功后重定向
    const redirect = route.query.redirect as string || '/dashboard'
    router.push(redirect)
  } catch (error) {
    console.error('登录失败:', error)
    alert(getLoginErrorMessage(error))
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--cw-bg);
}

.login-container {
  width: min(100%, 420px);
  padding: 34px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid var(--cw-border);
  border-radius: 22px;
  box-shadow: var(--cw-shadow-md);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  color: var(--cw-text);
  font-size: 30px;
  letter-spacing: -0.05em;
  margin-bottom: 8px;
}

.login-header p {
  color: var(--cw-text-muted);
  font-size: 15px;
}

.login-form {
  margin-bottom: 24px;
}

.form-item {
  margin-bottom: 20px;
}

.form-input {
  width: 100%;
  min-height: 44px;
  font-size: 15px;
}

.login-button {
  width: 100%;
}

.login-footer {
  text-align: center;
}

.link {
  color: var(--cw-blue-600);
  text-decoration: none;
  font-weight: 650;
}

.link:hover {
  text-decoration: underline;
}
</style>
