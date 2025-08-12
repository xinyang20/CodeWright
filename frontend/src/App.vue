<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// 应用根组件
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background-color: #fafafa;
  color: #111;
  line-height: 1.6;
}

#app {
  min-height: 100vh;
}

/* Element Plus 自定义样式 */
.el-button {
  border-radius: 6px;
}

.el-card {
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.el-input {
  border-radius: 6px;
}

/* 工具类 */
.text-center {
  text-align: center;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}

.p-4 {
  padding: 16px;
}
</style>
