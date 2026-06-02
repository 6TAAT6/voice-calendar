<!--
  App.vue — 根组件（整个 App 的"外壳"）
  所有页面都在这层壳里面渲染：

  顶部导航栏（固定不变）
  ┌──────────────────┐
  │ 🎙️语音日历  📅日程 ⚙️设置 │  ← nav
  ├──────────────────┤
  │                  │
  │  <router-view>   │  ← 当前页面内容在这里渲染
  │                  │
  └──────────────────┘
-->
<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <nav class="navbar">
      <router-link to="/" class="logo">🎙️ 语音日历</router-link>
      <div class="nav-links">
        <router-link to="/calendar">📅 日程</router-link>
        <router-link to="/settings">⚙️ 设置</router-link>
      </div>
    </nav>

    <!-- 页面内容区域：router-view 是个"占位符" -->
    <!-- 它会根据当前 URL 自动替换成对应的页面组件 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App',
}
</script>

<style>
/* 全局样式（没有 scoped，会影响所有页面） */

/* 重置默认边距 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    'Helvetica Neue', Arial, sans-serif;
  background: #f5f6f8;
  color: #333;
}

/* 导航栏样式 */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  font-size: 18px;
  font-weight: bold;
  text-decoration: none;
  color: #333;
}

.nav-links {
  display: flex;
  gap: 20px;
}

.nav-links a {
  text-decoration: none;
  color: #666;
  font-size: 15px;
  padding: 6px 12px;
  border-radius: 6px;
  transition: background 0.2s;
}

.nav-links a:hover {
  background: #f0f0f0;
}

/* 当前激活的导航链接高亮 */
.nav-links a.router-link-active {
  color: #4a90d9;
  font-weight: 600;
}

/* main-content 里放 router-view 渲染的页面 */
.main-content {
  min-height: calc(100vh - 60px);
}
</style>
