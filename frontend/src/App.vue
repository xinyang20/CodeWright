<template>
  <div id="app">
    <template v-if="showWorkspaceShell">
      <div class="app-shell">
        <header class="app-topbar">
          <div class="app-topbar-inner">
            <router-link to="/dashboard" class="brand">
              <span class="brand-mark">C</span>
              <span>CodeWright</span>
            </router-link>

            <nav class="app-nav" aria-label="主导航">
              <router-link to="/dashboard">控制台</router-link>
              <router-link to="/projects">项目</router-link>
              <router-link v-if="authStore.isAdmin" to="/admin">管理</router-link>
            </nav>

            <div class="app-user">
              <span>{{ authStore.user?.username || '未登录' }}</span>
              <button class="btn" type="button" @click="handleLogout">退出</button>
            </div>
          </div>
        </header>

        <main class="app-main">
          <router-view />
        </main>
      </div>
    </template>

    <router-view v-else />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const publicRouteNames = ['home', 'login', 'register', 'not-found']
const showWorkspaceShell = computed(() => !publicRouteNames.includes(String(route.name)))

const handleLogout = () => {
  authStore.logout()
  router.push('/')
}
</script>
