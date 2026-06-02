<!--
  Calendar.vue — 日历/日程页面
  查看所有已创建的日程事件
-->
<template>
  <div class="calendar-page">
    <h1>📅 我的日程</h1>

    <!-- 占位内容，后续 PR 实现真实日历 -->
    <div class="empty-state">
      <p class="icon">📭</p>
      <p>暂无日程安排</p>
      <router-link to="/" class="back-link">← 返回首页添加日程</router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Calendar',
}
</script>

<style scoped>
.calendar-page {
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
