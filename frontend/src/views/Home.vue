<!--
  Home.vue — 首页
  每个 .vue 文件由三部分组成：
  <template>  → HTML 骨架（页面长什么样）
  <script>    → JS 逻辑（按钮点什么、数据怎么变）
  <style>     → CSS 样式（颜色、大小、间距）
-->
<template>
  <div class="home">
    <h1>🎙️ 语音日历</h1>
    <p class="subtitle">说一句话，轻松管理你的日程</p>

    <!-- 语音输入区域（功能后续 PR 实现） -->
    <div class="voice-area">
      <button class="mic-btn" disabled>
        🎤 点击录音（即将实现）
      </button>
      <p class="hint">例如说："明天下午三点开会"</p>
    </div>

    <!-- 快捷入口 -->
    <div class="quick-links">
      <router-link to="/calendar" class="card">
        📅 查看日程
      </router-link>
      <router-link to="/settings" class="card">
        ⚙️ 设置
      </router-link>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home',
}
</script>

<style scoped>
/* scoped 表示这些样式只对这个文件生效，不影响其他页面 */
.home {
  max-width: 600px;
  margin: 0 auto;
  padding: 40px 20px;
  text-align: center;
}

h1 {
  font-size: 28px;
  color: #333;
}

.subtitle {
  color: #666;
  margin-bottom: 40px;
}

.voice-area {
  margin: 40px 0;
}

.mic-btn {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  border: 4px solid #4a90d9;
  background: #e8f0fe;
  font-size: 18px;
  cursor: pointer;
  color: #4a90d9;
  transition: all 0.3s;
}

.mic-btn:hover {
  background: #4a90d9;
  color: white;
}

.mic-btn:disabled {
  border-color: #ccc;
  background: #f5f5f5;
  color: #999;
  cursor: not-allowed;
}

.hint {
  color: #999;
  margin-top: 12px;
  font-size: 14px;
}

.quick-links {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 40px;
}

.card {
  padding: 20px 30px;
  background: #f8f9fa;
  border-radius: 12px;
  text-decoration: none;
  color: #333;
  font-size: 16px;
  border: 1px solid #e0e0e0;
  transition: transform 0.2s;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>
