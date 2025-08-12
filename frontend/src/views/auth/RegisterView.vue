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
            @keyup.enter="handleSubmit"
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

    // 注册成功后跳转到登录页
    alert('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    console.error('注册失败:', error)
    alert('注册失败，请重试')
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-container {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 32px;
}

.register-header h1 {
  color: #2f54eb;
  font-size: 28px;
  margin-bottom: 8px;
}

.register-header p {
  color: #666;
  font-size: 16px;
}

.register-form {
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

.register-button {
  width: 100%;
}

.register-footer {
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
