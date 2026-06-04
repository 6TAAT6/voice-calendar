// ===== 程序入口 =====
// 就像 C++ 的 main() 函数，整个前端 App 从这里启动
// 做的事情：创建 Vue 应用 → 装上路由器 → 挂载到页面 #app 节点

import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 导入路由配置

const app = createApp(App) // 创建 Vue 应用实例
app.use(router) // 装上路由器（让页面之间可以跳转）
app.mount('#app') // 挂载到 index.html 里的 <div id="app">
