<template>
  <div class="home">
    <div class="container">
      <!-- 头部 -->
      <header class="header">
        <div class="header-content">
          <div class="logo">
            <h1>CodeWright</h1>
            <span class="subtitle">代码版权工匠</span>
          </div>
          <div class="nav-buttons">
            <button v-if="!isAuthenticated" @click="$router.push('/login')" class="btn">
              登录
            </button>
            <button v-if="!isAuthenticated" @click="$router.push('/register')" class="btn btn-primary">
              注册
            </button>
            <button v-if="isAuthenticated" @click="$router.push('/dashboard')" class="btn">
              控制台
            </button>
            <button v-if="isAuthenticated" @click="handleLogout" class="btn">
              退出
            </button>
          </div>
        </div>
      </header>

      <!-- 主要内容 -->
      <main class="main">
        <div class="hero">
          <h2>软件著作权申请材料准备平台</h2>
          <p class="hero-description">
            通过自动排版、语法高亮、模板化文档与 PDF 导出等能力，
            显著降低材料准备门槛并提升专业度
          </p>
          <div class="hero-buttons">
            <button
              v-if="!isAuthenticated"
              class="btn btn-primary btn-large"
              @click="$router.push('/register')"
            >
              立即开始
            </button>
            <button
              v-if="isAuthenticated"
              class="btn btn-primary btn-large"
              @click="$router.push('/projects')"
            >
              我的项目
            </button>
          </div>
        </div>

        <!-- 功能特性 -->
        <div class="features">
          <h3>核心功能</h3>
          <div class="feature-grid">
            <div class="feature-card">
              <div class="feature-header">
                <span class="feature-icon">📄</span>
                <span>代码文件构建</span>
              </div>
              <p>支持多种编程语言的语法高亮，自动排版，生成规范的代码文档</p>
            </div>
            <div class="feature-card">
              <div class="feature-header">
                <span class="feature-icon">🖼️</span>
                <span>操作文档构建</span>
              </div>
              <p>图文并茂的操作手册生成，支持模板化文档，提升材料专业度</p>
            </div>
            <div class="feature-card">
              <div class="feature-header">
                <span class="feature-icon">⬇️</span>
                <span>PDF 导出</span>
              </div>
              <p>一键导出高质量PDF文档，符合软著申请要求，支持中文字体</p>
            </div>
          </div>
        </div>
      </main>

      <!-- 页脚 -->
      <footer class="footer">
        <p>&copy; 2024 CodeWright. All rights reserved.</p>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const isAuthenticated = computed(() => authStore.isAuthenticated)

const handleLogout = () => {
  authStore.logout()
  router.push('/')
}
</script>

<style scoped>
.home {
  min-height: 100vh;
}

.container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 16px 0;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
}

.logo h1 {
  margin: 0;
  color: #2f54eb;
  font-size: 24px;
}

.subtitle {
  color: #666;
  font-size: 14px;
  margin-left: 8px;
}

.nav-buttons {
  display: flex;
  gap: 12px;
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

.main {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 60px 24px;
  width: 100%;
}

.hero {
  text-align: center;
  margin-bottom: 80px;
}

.hero h2 {
  font-size: 36px;
  color: #111;
  margin-bottom: 16px;
}

.hero-description {
  font-size: 18px;
  color: #666;
  margin-bottom: 32px;
  line-height: 1.6;
}

.hero-buttons {
  margin-top: 32px;
}

.features {
  margin-top: 60px;
}

.features h3 {
  text-align: center;
  font-size: 28px;
  margin-bottom: 40px;
  color: #111;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.feature-card {
  text-align: center;
  padding: 32px 24px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.feature-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.feature-icon {
  font-size: 32px;
}

.feature-header span:last-child {
  font-size: 18px;
  font-weight: 600;
  color: #111;
}

.feature-card p {
  color: #666;
  line-height: 1.6;
  margin: 0;
}

.footer {
  background: #f5f5f5;
  text-align: center;
  color: #666;
  border-top: 1px solid #e4e7ed;
  padding: 24px 0;
}
</style>
