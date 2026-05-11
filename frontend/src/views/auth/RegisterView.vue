<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-header">
        <h1>CodeWright</h1>
        <p>注册代码版权工匠账号</p>
      </div>

      <form class="register-form" @submit.prevent="handleSubmit">
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
          <input
            v-model="form.confirmPassword"
            type="password"
            placeholder="请确认密码"
            class="form-input"
            required
          />
        </div>

        <div class="form-item">
          <button
            type="submit"
            class="btn btn-primary btn-large register-button"
            :disabled="authStore.loading"
          >
            {{ authStore.loading ? '注册中...' : '注册' }}
          </button>
        </div>
      </form>

      <div class="register-footer">
        <p>
          已有账号？
          <router-link to="/login" class="link">立即登录</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { RegisterRequest } from '@/types'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const handleSubmit = async () => {
  if (authStore.loading) {
    return
  }

  if (!form.username || !form.password || !form.confirmPassword) {
    alert('请填写所有字段')
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

  if (form.password !== form.confirmPassword) {
    alert('两次输入密码不一致')
    return
  }

  try {
    const registerData: RegisterRequest = {
      username: form.username,
      password: form.password
    }

    await authStore.register(registerData)
  } catch (error) {
    console.error('注册失败:', error)
    alert('注册失败，请重试')
    return
  }

  // 注册成功后跳转到登录页；跳转错误不应被当作注册失败处理
  alert('注册成功，请登录')
  router.push('/login')
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--cw-bg);
}

.register-container {
  width: min(100%, 420px);
  padding: 34px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid var(--cw-border);
  border-radius: 22px;
  box-shadow: var(--cw-shadow-md);
}

.register-header {
  text-align: center;
  margin-bottom: 32px;
}

.register-header h1 {
  color: var(--cw-text);
  font-size: 30px;
  letter-spacing: -0.05em;
  margin-bottom: 8px;
}

.register-header p {
  color: var(--cw-text-muted);
  font-size: 15px;
}

.register-form {
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

.register-button {
  width: 100%;
}

.register-footer {
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
