<template>
  <div class="dashboard">
    <h1>控制台</h1>
    <p>欢迎使用 CodeWright，{{ authStore.user?.username }}！</p>
    
    <!-- TODO: 实现控制台功能 -->
    <el-row :gutter="24">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>我的项目</span>
          </template>
          <p>项目管理功能开发中...</p>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>最近活动</span>
          </template>
          <p>活动记录功能开发中...</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<style scoped>
.dashboard {
  padding: 24px;
}
</style>
