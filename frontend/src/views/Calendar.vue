<!--
  Calendar.vue — 日程列表页面
  从后端加载所有事件并展示
-->
<template>
  <div class="calendar-page">
    <h1>📅 我的日程</h1>

    <!-- 错误提示 -->
    <div v-if="error" class="error-banner">⚠️ {{ error }}</div>

    <!-- 加载中 -->
    <div v-if="loading" class="empty-state">
      <p class="icon">⏳</p>
      <p>加载中...</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="events.length === 0" class="empty-state">
      <p class="icon">📭</p>
      <p>暂无日程安排</p>
      <router-link to="/" class="back-link">← 返回首页添加日程</router-link>
    </div>

    <!-- 事件列表 -->
    <div v-else class="event-list">
      <div v-for="evt in events" :key="evt.id" class="event-card" :class="{ completed: evt.completed }">
        <div class="event-header">
          <span class="event-type">{{ evt.event_type }}</span>
          <button class="del-btn" @click="handleDelete(evt.id)" title="删除">×</button>
        </div>
        <div class="event-title">{{ evt.title }}</div>
        <div class="event-time">🕐 {{ formatTime(evt.event_time) }}</div>
        <div class="event-desc" v-if="evt.description">{{ evt.description }}</div>
        <div class="event-meta">
          <span v-if="evt.remind">🔔 已提醒</span>
          <span v-if="evt.completed" class="done-tag">✅ 已完成</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { listEvents, deleteEvent } from '../api/index'

export default {
  name: 'Calendar',
  setup() {
    const events = ref([])
    const loading = ref(true)
    const error = ref('')

    async function loadEvents() {
      loading.value = true
      try {
        events.value = await listEvents()
      } catch (e) {
        error.value = e.message || '加载日程失败'
      } finally {
        loading.value = false
      }
    }

    async function handleDelete(id) {
      if (!confirm('确定删除这个日程吗？')) return
      try {
        await deleteEvent(id)
        events.value = events.value.filter((e) => e.id !== id)
      } catch (e) {
        error.value = e.message || '删除失败'
      }
    }

    function formatTime(isoStr) {
      if (!isoStr) return ''
      const d = new Date(isoStr)
      const y = d.getFullYear()
      const M = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const h = String(d.getHours()).padStart(2, '0')
      const m = String(d.getMinutes()).padStart(2, '0')
      const week = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()]
      return `${y}年${M}月${day}日 周${week} ${h}:${m}`
    }

    onMounted(loadEvents)

    return { events, loading, error, handleDelete, formatTime }
  },
}
</script>

<style scoped>
.calendar-page { max-width: 600px; margin: 0 auto; padding: 40px 20px; }
h1 { font-size: 24px; color: #333; margin-bottom: 24px; }

.empty-state { text-align: center; padding: 60px 20px; color: #999; }
.icon { font-size: 48px; margin-bottom: 12px; }
.back-link { display: inline-block; margin-top: 16px; color: #4a90d9; text-decoration: none; }
.back-link:hover { text-decoration: underline; }

.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

/* 事件卡片 */
.event-list { display: flex; flex-direction: column; gap: 12px; }
.event-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 16px;
  text-align: left;
  transition: box-shadow 0.2s;
}
.event-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.event-card.completed { opacity: 0.6; }

.event-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.event-type {
  font-size: 12px;
  background: #e8f0fe;
  color: #4a90d9;
  padding: 2px 8px;
  border-radius: 4px;
}
.del-btn {
  background: none;
  border: none;
  font-size: 20px;
  color: #ccc;
  cursor: pointer;
  line-height: 1;
}
.del-btn:hover { color: #e74c3c; }

.event-title { font-size: 18px; font-weight: 600; color: #333; margin-bottom: 6px; }
.event-time { color: #666; font-size: 14px; margin-bottom: 4px; }
.event-desc { color: #888; font-size: 13px; margin-bottom: 4px; }
.event-meta { font-size: 12px; color: #999; margin-top: 6px; display: flex; gap: 12px; }
.done-tag { color: #16a34a; }
</style>
