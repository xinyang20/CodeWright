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
                <span class="feature-icon">Code</span>
                <span>代码文件构建</span>
              </div>
              <p>支持多种编程语言的语法高亮，自动排版，生成规范的代码文档</p>
            </div>
            <div class="feature-card">
              <div class="feature-header">
                <span class="feature-icon">Doc</span>
                <span>操作文档构建</span>
              </div>
              <p>图文并茂的操作手册生成，支持模板化文档，提升材料专业度</p>
            </div>
            <div class="feature-card">
              <div class="feature-header">
                <span class="feature-icon">PDF</span>
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
import { computed } from 'vue'
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
  background: var(--cw-bg);
}

.container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: rgba(255, 255, 255, 0.86);
  border-bottom: 1px solid var(--cw-border);
  padding: 14px 0;
  backdrop-filter: blur(18px);
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
  color: var(--cw-text);
  font-size: 24px;
  letter-spacing: -0.04em;
}

.subtitle {
  color: var(--cw-text-muted);
  font-size: 14px;
  margin-left: 8px;
}

.nav-buttons {
  display: flex;
  gap: 12px;
}

.main {
  flex: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 72px 24px 48px;
  width: 100%;
}

.hero {
  text-align: center;
  margin-bottom: 80px;
}

.hero h2 {
  max-width: 780px;
  margin: 0 auto 18px;
  font-size: clamp(36px, 7vw, 68px);
  line-height: 1.02;
  color: var(--cw-text);
  letter-spacing: -0.06em;
  font-weight: 820;
}

.hero h2::after {
  content: "";
  display: block;
  width: 86px;
  height: 4px;
  margin: 24px auto 0;
  border-radius: 999px;
  background: var(--cw-blue-400);
}

.hero-description {
  max-width: 680px;
  margin: 0 auto 32px;
  font-size: 18px;
  color: var(--cw-text-muted);
  line-height: 1.75;
}

.hero-buttons {
  margin-top: 32px;
}

.features {
  margin-top: 72px;
}

.features h3 {
  text-align: center;
  font-size: 28px;
  margin-bottom: 28px;
  color: var(--cw-text);
  letter-spacing: -0.04em;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}

.feature-card {
  padding: 26px;
  border: 1px solid var(--cw-border);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: var(--cw-shadow-sm);
}

.feature-card:hover {
  border-color: var(--cw-blue-200);
  box-shadow: var(--cw-shadow-md);
}

.feature-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.feature-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--cw-blue-50);
  color: var(--cw-blue-700);
  font-size: 12px;
  font-weight: 800;
}

.feature-header span:last-child {
  font-size: 17px;
  font-weight: 720;
  color: var(--cw-text);
}

.feature-card p {
  color: var(--cw-text-muted);
  line-height: 1.75;
  margin: 0;
}

.footer {
  background: transparent;
  text-align: center;
  color: var(--cw-text-subtle);
  border-top: 1px solid var(--cw-border);
  padding: 24px 0;
}

@media (max-width: 720px) {
  .header-content,
  .nav-buttons {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-content {
    gap: 16px;
  }

  .nav-buttons {
    width: 100%;
  }

  .nav-buttons .btn {
    width: 100%;
  }
}
</style>
