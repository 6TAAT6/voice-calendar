// ===== 路由配置 =====
// 作用：URL 地址 ↔ 页面 的映射表
// 例如：用户访问 /calendar → 显示日历页面
//       用户访问 /settings → 显示设置页面

import { createRouter, createWebHistory } from 'vue-router'

// 导入各个页面组件（就像 C++ 的 #include）
import Home from '../views/Home.vue'
import Calendar from '../views/Calendar.vue'
import Settings from '../views/Settings.vue'

// 路由规则表：每个对象定义一条路径
const routes = [
  {
    path: '/',           // 浏览器地址栏：http://xxx.com/
    name: 'home',        // 路由名称（代码里跳转用）
    component: Home,     // 显示哪个页面组件
  },
  {
    path: '/calendar',   // 浏览器地址栏：http://xxx.com/calendar
    name: 'calendar',
    component: Calendar,
  },
  {
    path: '/settings',   // 浏览器地址栏：http://xxx.com/settings
    name: 'settings',
    component: Settings,
  },
]

// 创建路由器实例
const router = createRouter({
  history: createWebHistory(),  // 使用 HTML5 历史模式（URL 看起来像正常路径）
  routes,                        // 传入路由规则表
})

export default router
