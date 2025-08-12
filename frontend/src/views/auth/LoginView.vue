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
            @keyup.enter="handleSubmit"
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

const handleSubmit = async () => {
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
    alert('登录失败，请检查用户名和密码')
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-container {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  color: #2f54eb;
  font-size: 28px;
  margin-bottom: 8px;
}

.login-header p {
  color: #666;
  font-size: 16px;
}

.login-form {
  margin-bottom: 24px;
}

.form-item {
  margin-bottom: 20px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 16px;
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #2f54eb;
}

.btn {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  background: #fff;
  color: #333;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn:hover {
  border-color: #2f54eb;
  color: #2f54eb;
}

.btn-primary {
  background: #2f54eb;
  color: #fff;
  border-color: #2f54eb;
}

.btn-primary:hover {
  background: #1d39c4;
  border-color: #1d39c4;
}

.btn-large {
  padding: 12px 24px;
  font-size: 16px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-button {
  width: 100%;
}

.login-footer {
  text-align: center;
}

.link {
  color: #2f54eb;
  text-decoration: none;
}

.link:hover {
  text-decoration: underline;
}
</style>
