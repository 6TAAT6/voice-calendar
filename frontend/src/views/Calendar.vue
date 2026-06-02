<!--
  Calendar.vue — 月视图日历 + 日程管理
  功能: 日历网格展示 / 月导航 / 事件卡片 / 详情弹窗 / 完成标记 / 删除
-->
<template>
  <div class="calendar-page">
    <!-- ═══ 页面标题 ═══ -->
    <div class="page-header">
      <h1>📅 我的日程</h1>
      <div class="header-actions">
        <button class="btn-sm" :class="{ active: remindEnabled }" @click="toggleRemind">
          🔔 {{ remindEnabled ? '提醒已开启' : '开启提醒' }}
        </button>
        <router-link to="/" class="btn-sm btn-primary">➕ 添加</router-link>
      </div>
    </div>

    <!-- ═══ 月份导航 ═══ -->
    <div class="month-nav">
      <button @click="prevMonth">◀</button>
      <span class="month-label">{{ monthLabel }}</span>
      <button @click="nextMonth">▶</button>
      <button class="today-btn" @click="goToday">今天</button>
    </div>

    <!-- ═══ 星期头 ═══ -->
    <div class="weekdays">
      <span v-for="d in weekDays" :key="d" class="weekday">{{ d }}</span>
    </div>

    <!-- ═══ 日历网格 ═══ -->
    <div class="calendar-grid">
      <div
        v-for="(day, idx) in calendarDays"
        :key="idx"
        class="day-cell"
        :class="{
          'other-month': !day.isCurrentMonth,
          today: day.isToday,
          'has-events': day.events.length > 0,
        }"
        @click="selectDay(day)"
      >
        <span class="day-num">{{ day.day }}</span>
        <div class="day-events">
          <div
            v-for="evt in day.events"
            :key="evt.id"
            class="day-event-dot"
            :class="{ completed: evt.completed }"
            :title="evt.title"
          >
            {{ evt.title }}
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 选中日事件列表 ═══ -->
    <div v-if="selectedDay" class="selected-day-panel">
      <div class="panel-header">
        <h2>{{ selectedDayLabel }}</h2>
        <button class="btn-sm" @click="selectedDay = null">✕</button>
      </div>

      <div v-if="selectedDayEvents.length === 0" class="empty-day">
        📭 当天暂无日程
      </div>

      <div v-else class="event-list">
        <div
          v-for="evt in selectedDayEvents"
          :key="evt.id"
          class="event-card"
          :class="{ completed: evt.completed }"
        >
          <div class="event-header">
            <span class="event-type">{{ evt.event_type }}</span>
            <div class="event-card-actions">
              <button
                v-if="!evt.completed"
                class="action-btn done"
                title="标记完成"
                @click="handleComplete(evt)"
              >
                ✅
              </button>
              <button class="action-btn del" title="删除" @click="handleDelete(evt.id)">
                🗑️
              </button>
            </div>
          </div>
          <div class="event-title">{{ evt.title }}</div>
          <div class="event-time">🕐 {{ formatTime(evt.event_time) }}</div>
          <div class="event-desc" v-if="evt.description">{{ evt.description }}</div>
          <div class="event-meta">
            <span v-if="evt.remind">🔔 已提醒</span>
            <span v-if="evt.completed" class="done-tag">✅ 已完成</span>
            <span v-else class="upcoming-tag">
              {{ getRelativeTime(evt.event_time) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 加载 / 错误 ═══ -->
    <div v-if="loading" class="center-msg">⏳ 加载中...</div>
    <div v-if="error" class="error-toast">
      ⚠️ {{ error }}
      <button @click="error = ''" class="close-btn">×</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { listEvents, deleteEvent } from '../api/index'
import { useReminder } from '../composables/useReminder'

export default {
  name: 'Calendar',
  setup() {
    // ---- 状态 ----
    const events = ref([])
    const loading = ref(true)
    const error = ref('')
    const currentDate = ref(new Date()) // 当前显示的月份
    const selectedDay = ref(null)       // 选中的天
    const remindEnabled = ref(false)

    // ---- 提醒服务 ----
    const reminder = useReminder(events, 30000)

    // ---- 星期头 ----
    const weekDays = ['日', '一', '二', '三', '四', '五', '六']

    // ---- 月份标签 ----
    const monthLabel = computed(() => {
      const y = currentDate.value.getFullYear()
      const m = currentDate.value.getMonth() + 1
      return `${y}年 ${m}月`
    })

    // ---- 选中天的标签 ----
    const selectedDayLabel = computed(() => {
      if (!selectedDay.value) return ''
      const { year, month, day } = selectedDay.value
      const week = weekDays[new Date(year, month, day).getDay()]
      return `${year}年${month + 1}月${day}日 周${week}`
    })

    // ---- 选中天的事件列表 ----
    const selectedDayEvents = computed(() => {
      if (!selectedDay.value) return []
      return selectedDay.value.events
    })

    // ========================================
    // 日历网格生成（核心算法）
    // ========================================
    const calendarDays = computed(() => {
      const year = currentDate.value.getFullYear()
      const month = currentDate.value.getMonth() // 0-11
      const today = new Date()
      const todayY = today.getFullYear()
      const todayM = today.getMonth()
      const todayD = today.getDate()

      // 本月第一天是周几（0=周日）
      const firstDayOfWeek = new Date(year, month, 1).getDay()
      // 本月有多少天
      const daysInMonth = new Date(year, month + 1, 0).getDate()
      // 上月有多少天（用于填充前面的格子）
      const daysInPrevMonth = new Date(year, month, 0).getDate()

      const days = []

      // 填充上月的尾巴（前面空白的格子）
      for (let i = firstDayOfWeek - 1; i >= 0; i--) {
        const day = daysInPrevMonth - i
        const date = new Date(year, month - 1, day)
        days.push({
          day,
          date,
          isCurrentMonth: false,
          isToday: false,
          events: eventsOnDate(date),
        })
      }

      // 本月所有天
      for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day)
        days.push({
          day,
          date,
          isCurrentMonth: true,
          isToday: year === todayY && month === todayM && day === todayD,
          events: eventsOnDate(date),
        })
      }

      // 填充下月的头（尾巴空白的格子，凑满 6 行）
      const remaining = 42 - days.length // 6行 × 7列 = 42
      for (let day = 1; day <= remaining; day++) {
        const date = new Date(year, month + 1, day)
        days.push({
          day,
          date,
          isCurrentMonth: false,
          isToday: false,
          events: eventsOnDate(date),
        })
      }

      return days
    })

    /** 查找某个日期上有哪些事件 */
    function eventsOnDate(date) {
      if (!events.value) return []
      return events.value.filter((evt) => {
        const evtDate = new Date(evt.event_time)
        return (
          evtDate.getFullYear() === date.getFullYear() &&
          evtDate.getMonth() === date.getMonth() &&
          evtDate.getDate() === date.getDate()
        )
      })
    }

    // ---- 月份导航 ----
    function prevMonth() {
      const d = new Date(currentDate.value)
      d.setMonth(d.getMonth() - 1)
      currentDate.value = d
      selectedDay.value = null
    }
    function nextMonth() {
      const d = new Date(currentDate.value)
      d.setMonth(d.getMonth() + 1)
      currentDate.value = d
      selectedDay.value = null
    }
    function goToday() {
      currentDate.value = new Date()
      const today = new Date()
      selectDay({
        day: today.getDate(),
        date: today,
        isCurrentMonth: true,
        isToday: true,
        events: eventsOnDate(today),
      })
    }

    // ---- 选择某天 ----
    function selectDay(day) {
      selectedDay.value = day
    }

    // ---- 加载事件 ----
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

    // ---- 删除事件 ----
    async function handleDelete(id) {
      if (!confirm('确定删除这个日程吗？')) return
      try {
        await deleteEvent(id)
        events.value = events.value.filter((e) => e.id !== id)
        // 刷新选中天的事件
        if (selectedDay.value) {
          selectedDay.value.events = eventsOnDate(selectedDay.value.date)
        }
      } catch (e) {
        error.value = e.message || '删除失败'
      }
    }

    // ---- 标记完成 ----
    async function handleComplete(evt) {
      try {
        const resp = await fetch(`http://localhost:8000/events/${evt.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ completed: true }),
        })
        if (!resp.ok) throw new Error('更新失败')
        evt.completed = true
      } catch (e) {
        error.value = e.message || '操作失败'
      }
    }

    // ---- 切换提醒 ----
    async function toggleRemind() {
      if (remindEnabled.value) {
        reminder.stop()
        remindEnabled.value = false
      } else {
        const ok = await reminder.start()
        remindEnabled.value = ok
        if (!ok) {
          alert('需要浏览器通知权限才能开启提醒\n请在浏览器设置中允许本站发送通知')
        }
      }
    }

    // ---- 格式化 ----
    function formatTime(isoStr) {
      if (!isoStr) return ''
      const d = new Date(isoStr)
      const M = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const h = String(d.getHours()).padStart(2, '0')
      const m = String(d.getMinutes()).padStart(2, '0')
      return `${M}月${day}日 ${h}:${m}`
    }

    /** 相对时间：多久后 */
    function getRelativeTime(isoStr) {
      const diff = new Date(isoStr) - new Date()
      if (diff < 0) return '已过期'
      const mins = Math.floor(diff / 60000)
      if (mins < 60) return `${mins}分钟后`
      const hours = Math.floor(mins / 60)
      if (hours < 24) return `${hours}小时后`
      const days = Math.floor(hours / 24)
      return `${days}天后`
    }

    // ---- 生命周期 ----
    onMounted(loadEvents)

    onUnmounted(() => {
      reminder.stop()
    })

    return {
      events,
      loading,
      error,
      currentDate,
      selectedDay,
      remindEnabled,
      weekDays,
      monthLabel,
      selectedDayLabel,
      selectedDayEvents,
      calendarDays,
      prevMonth,
      nextMonth,
      goToday,
      selectDay,
      handleDelete,
      handleComplete,
      toggleRemind,
      formatTime,
      getRelativeTime,
    }
  },
}
</script>

<style scoped>
/* ===== 布局 ===== */
.calendar-page {
  max-width: 700px;
  margin: 0 auto;
  padding: 20px;
}

/* ===== 页面头 ===== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h1 { font-size: 22px; color: #333; margin: 0; }
.header-actions { display: flex; gap: 8px; }

.btn-sm {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  border: 1px solid #ddd;
  background: white;
  color: #666;
  text-decoration: none;
  transition: all 0.2s;
}
.btn-sm:hover { border-color: #4a90d9; color: #4a90d9; }
.btn-sm.active { background: #4a90d9; color: white; border-color: #4a90d9; }
.btn-primary { background: #4a90d9; color: white; border-color: #4a90d9; }
.btn-primary:hover { opacity: 0.9; }

/* ===== 月份导航 ===== */
.month-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 16px;
}
.month-nav button {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 15px;
  color: #666;
}
.month-nav button:hover { background: #f0f0f0; }
.month-label { font-size: 18px; font-weight: 600; min-width: 120px; text-align: center; }
.today-btn { font-size: 13px !important; }

/* ===== 星期头 ===== */
.weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  margin-bottom: 4px;
}
.weekday {
  text-align: center;
  font-size: 12px;
  color: #999;
  font-weight: 600;
  padding: 6px 0;
}

/* ===== 日历网格 ===== */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}
.day-cell {
  aspect-ratio: 1;
  border-radius: 8px;
  padding: 4px;
  cursor: pointer;
  background: #fafafa;
  border: 1px solid transparent;
  transition: all 0.15s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.day-cell:hover {
  border-color: #4a90d9;
  box-shadow: 0 0 0 1px #4a90d9;
}
.day-cell.other-month { opacity: 0.35; }
.day-cell.today {
  background: #e8f0fe;
  border-color: #4a90d9;
}
.day-cell.has-events { background: #f0f9ff; }

.day-num {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  margin-bottom: 2px;
}
.day-cell.today .day-num {
  background: #4a90d9;
  color: white;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

/* 日历格子里的事件点 */
.day-events {
  display: flex;
  flex-direction: column;
  gap: 1px;
  flex: 1;
  overflow: hidden;
}
.day-event-dot {
  font-size: 10px;
  padding: 2px 4px;
  border-radius: 3px;
  background: #4a90d9;
  color: white;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}
.day-event-dot.completed {
  background: #aaa;
  text-decoration: line-through;
}

/* ===== 选中天的面板 ===== */
.selected-day-panel {
  margin-top: 20px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}
.panel-header h2 { font-size: 16px; color: #333; margin: 0; }
.empty-day { text-align: center; padding: 32px; color: #999; font-size: 15px; }

/* ===== 事件卡片列表 ===== */
.event-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.event-card {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 14px;
  text-align: left;
}
.event-card.completed { opacity: 0.55; }

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.event-type {
  font-size: 11px;
  background: #e8f0fe;
  color: #4a90d9;
  padding: 2px 8px;
  border-radius: 4px;
}
.event-card-actions { display: flex; gap: 4px; }
.action-btn {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  padding: 2px;
  opacity: 0.6;
}
.action-btn:hover { opacity: 1; }

.event-title { font-size: 16px; font-weight: 600; color: #333; margin-bottom: 4px; }
.event-time { color: #666; font-size: 13px; margin-bottom: 2px; }
.event-desc { color: #888; font-size: 12px; margin-bottom: 4px; }
.event-meta { font-size: 11px; color: #999; margin-top: 6px; display: flex; gap: 10px; }
.done-tag { color: #16a34a; font-weight: 600; }
.upcoming-tag { color: #f59e0b; }

/* ===== 公共 ===== */
.center-msg { text-align: center; padding: 40px; color: #999; }
.error-toast {
  margin-top: 12px;
  padding: 10px 14px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 13px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.close-btn { background: none; border: none; font-size: 18px; cursor: pointer; color: #dc2626; }
</style>
