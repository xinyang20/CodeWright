<template>
  <div class="not-found">
    <section class="not-found-card">
      <span class="status-code">404</span>
      <h1>页面不存在</h1>
      <p>该地址没有对应的工作区页面，请返回首页或控制台继续操作。</p>
      <div class="actions">
        <button class="btn" type="button" @click="$router.push('/')">返回首页</button>
        <button class="btn btn-primary" type="button" @click="$router.push('/dashboard')">进入控制台</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.not-found {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: var(--cw-bg);
}

.not-found-card {
  width: min(100%, 520px);
  padding: 38px;
  border: 1px solid var(--cw-border);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: var(--cw-shadow-md);
  text-align: center;
}

.status-code {
  display: inline-flex;
  margin-bottom: 12px;
  padding: 6px 12px;
  border-radius: 999px;
  background: var(--cw-blue-50);
  color: var(--cw-blue-700);
  font-weight: 800;
}

h1 {
  margin: 0 0 8px;
  color: var(--cw-text);
  letter-spacing: -0.05em;
}

p {
  margin: 0 0 24px;
  color: var(--cw-text-muted);
}

.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
}
</style>
