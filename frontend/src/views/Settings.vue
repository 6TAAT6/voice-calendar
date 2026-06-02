<!--
  Settings.vue — 设置页面
  后续用于配置语音、提醒等
-->
<template>
  <div class="settings-page">
    <h1>⚙️ 设置</h1>

    <div class="empty-state">
      <p class="icon">🔧</p>
      <p>语音和提醒设置即将上线</p>
      <router-link to="/" class="back-link">← 返回首页</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Settings',
}
</script>

<style scoped>
.settings-page {
  max-width: 600px;
  margin: 0 auto;
  padding: 40px 20px;
}

h1 {
  font-size: 24px;
  color: #333;
  margin-bottom: 30px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}

.icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.back-link {
  display: inline-block;
  margin-top: 16px;
  color: #4a90d9;
  text-decoration: none;
}

.back-link:hover {
  text-decoration: underline;
}
</style>
