<!--
  Calendar.vue — 月视图日历 + 日程管理
  重设计：大卡片 + 类型颜色 + 简约现代风格
-->
<template>
  <div class="calendar-page">
    <!-- ═══ 顶部栏 ═══ -->
    <header class="cal-header">
      <router-link to="/" class="logo-link">🎙️ 语音日历</router-link>
      <nav class="cal-nav">
        <button class="nav-btn" :class="{ active: remindEnabled }" @click="toggleRemind">
          🔔 {{ remindEnabled ? '提醒中' : '提醒' }}
        </button>
        <router-link to="/" class="nav-btn primary">+ 添加日程</router-link>
      </nav>
    </header>

    <!-- ═══ 月份导航 ═══ -->
    <div class="month-nav">
      <button class="arrow-btn" @click="prevMonth">‹</button>
      <h2 class="month-title">{{ monthLabel }}</h2>
      <button class="arrow-btn" @click="nextMonth">›</button>
      <button class="today-link" @click="goToday">今天</button>
    </div>

    <!-- ═══ 星期头 ═══ -->
    <div class="weekdays">
      <div v-for="d in weekDays" :key="d" class="weekday">
        <span class="weekday-text">{{ d }}</span>
      </div>
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
          'is-selected': selectedDay && selectedDay.date.getTime() === day.date.getTime(),
        }"
        @click="selectDay(day)"
      >
        <span class="day-num">{{ day.day }}</span>
        <div class="day-events">
          <div
            v-for="evt in day.events.slice(0, 2)"
            :key="evt.id"
            class="day-chip"
            :class="[eventColorClass(evt.event_type), { completed: evt.completed }]"
            :title="evt.title"
          >
            {{ evt.title.slice(0, 5) }}{{ evt.title.length > 5 ? '…' : '' }}
          </div>
          <div v-if="day.events.length > 2" class="more-tag">+{{ day.events.length - 2 }}</div>
        </div>
      </div>
    </div>

    <!-- ═══ 今日日程列表 ═══ -->
    <div v-if="selectedDay" class="day-detail">
      <div class="day-detail-header">
        <h3>{{ selectedDayLabel }}</h3>
        <button class="close-detail" @click="selectedDay = null">✕</button>
      </div>

      <div v-if="selectedDayEvents.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <p>当天暂无日程</p>
        <router-link to="/" class="empty-action">+ 添加日程</router-link>
      </div>

      <div v-else class="event-cards">
        <div
          v-for="evt in selectedDayEvents"
          :key="evt.id"
          class="event-card"
          :class="{ completed: evt.completed }"
        >
          <div class="event-left-bar" :class="eventColorClass(evt.event_type)"></div>
          <div class="event-body">
            <div class="event-row1">
              <span class="evt-title">{{ evt.title }}</span>
              <span class="evt-type" :class="eventColorClass(evt.event_type)">{{ typeLabel(evt.event_type) }}</span>
            </div>
            <div class="event-row2">
              <span class="evt-time">🕐 {{ formatTime(evt.event_time) }}</span>
              <span class="evt-relative">{{ getRelativeTime(evt.event_time) }}</span>
            </div>
            <div v-if="evt.description" class="event-row3">{{ evt.description }}</div>
          </div>
          <div class="event-actions">
            <button
              v-if="!evt.completed"
              class="eact-btn check"
              title="标记完成"
              @click.stop="handleComplete(evt)"
            >
              ○
            </button>
            <span v-else class="done-badge">✓</span>
            <button class="eact-btn del" title="删除" @click.stop="handleDelete(evt.id)">✕</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 没有选中天时，显示即将到来的事件 -->
    <div v-else class="upcoming-section">
      <h3 class="section-title">📋 近期日程</h3>
      <div v-if="upcomingEvents.length === 0" class="empty-state small">
        <p>暂无日程，去<a href="/">首页</a>添加吧</p>
      </div>
      <div v-else class="upcoming-list">
        <div
          v-for="evt in upcomingEvents.slice(0, 5)"
          :key="evt.id"
          class="upcoming-item"
          :class="{ completed: evt.completed }"
          @click="jumpToEvent(evt)"
        >
          <div class="up-color" :class="eventColorClass(evt.event_type)"></div>
          <div class="up-body">
            <span class="up-title">{{ evt.title }}</span>
            <span class="up-time">{{ formatTime(evt.event_time) }}</span>
          </div>
          <span class="up-relative">{{ getRelativeTime(evt.event_time) }}</span>
        </div>
      </div>
    </div>

    <!-- ═══ 加载 / 错误 ═══ -->
    <div v-if="loading" class="center-msg">⏳ 加载中...</div>
    <div v-if="error" class="error-toast">
      {{ error }}
      <button @click="error = ''" class="close-btn">×</button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { listEvents, deleteEvent } from '../api/index'
import { useReminder } from '../composables/useReminder'

// 事件类型 → 颜色映射
const TYPE_COLORS = {
  会议:     'type-meeting',
  运动:     'type-sport',
  生日:     'type-birthday',
  约会:     'type-date',
  提醒:     'type-reminder',
  购物:     'type-shop',
  就医:     'type-medical',
  旅行:     'type-travel',
  学习:     'type-study',
  其他:     'type-other',
}
const TYPE_NAMES = {
  会议: '会议', 运动: '运动', 生日: '生日', 约会: '约会',
  提醒: '提醒', 购物: '购物', 就医: '就医', 旅行: '旅行',
  学习: '学习', 其他: '其他',
}

export default {
  name: 'Calendar',
  setup() {
    const events = ref([])
    const loading = ref(true)
    const error = ref('')
    const currentDate = ref(new Date())
    const selectedDay = ref(null)
    const remindEnabled = ref(false)

    const reminder = useReminder(events, 30000)
    const weekDays = ['日', '一', '二', '三', '四', '五', '六']

    const monthLabel = computed(() => {
      const y = currentDate.value.getFullYear()
      const m = currentDate.value.getMonth() + 1
      return `${y}年 ${m}月`
    })

    // 修复：正确从 date 对象提取年月日
    const selectedDayLabel = computed(() => {
      if (!selectedDay.value) return ''
      const d = selectedDay.value.date
      return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 周${weekDays[d.getDay()]}`
    })

    const selectedDayEvents = computed(() => {
      if (!selectedDay.value) return []
      return selectedDay.value.events
    })

    // 近期未过期事件
    const upcomingEvents = computed(() => {
      const now = new Date()
      return [...events.value]
        .filter(e => new Date(e.event_time) >= now)
        .sort((a, b) => new Date(a.event_time) - new Date(b.event_time))
    })

    // ==== 日历网格 ====
    const calendarDays = computed(() => {
      const year = currentDate.value.getFullYear()
      const month = currentDate.value.getMonth()
      const today = new Date()
      const todayY = today.getFullYear()
      const todayM = today.getMonth()
      const todayD = today.getDate()

      const firstDayOfWeek = new Date(year, month, 1).getDay()
      const daysInMonth = new Date(year, month + 1, 0).getDate()
      const daysInPrevMonth = new Date(year, month, 0).getDate()

      const days = []

      // 上月填充
      for (let i = firstDayOfWeek - 1; i >= 0; i--) {
        const day = daysInPrevMonth - i
        const date = new Date(year, month - 1, day)
        days.push({ day, date, isCurrentMonth: false, isToday: false, events: eventsOnDate(date) })
      }

      // 本月
      for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day)
        days.push({
          day, date,
          isCurrentMonth: true,
          isToday: year === todayY && month === todayM && day === todayD,
          events: eventsOnDate(date),
        })
      }

      // 下月填充（最少5行）
      const remaining = days.length <= 35 ? 35 - days.length : 42 - days.length
      for (let day = 1; day <= remaining; day++) {
        const date = new Date(year, month + 1, day)
        days.push({ day, date, isCurrentMonth: false, isToday: false, events: eventsOnDate(date) })
      }

      return days
    })

    function eventsOnDate(date) {
      if (!events.value) return []
      return events.value.filter(evt => {
        const ed = new Date(evt.event_time)
        return ed.getFullYear() === date.getFullYear() &&
               ed.getMonth() === date.getMonth() &&
               ed.getDate() === date.getDate()
      })
    }

    function eventColorClass(type) {
      return TYPE_COLORS[type] || TYPE_COLORS['其他']
    }
    function typeLabel(type) {
      return TYPE_NAMES[type] || type || '其他'
    }

    // ==== 导航 ====
    function prevMonth() {
      const d = new Date(currentDate.value); d.setMonth(d.getMonth() - 1)
      currentDate.value = d; selectedDay.value = null
    }
    function nextMonth() {
      const d = new Date(currentDate.value); d.setMonth(d.getMonth() + 1)
      currentDate.value = d; selectedDay.value = null
    }
    function goToday() {
      currentDate.value = new Date()
      const today = new Date()
      selectDay({ day: today.getDate(), date: today, isCurrentMonth: true, isToday: true, events: eventsOnDate(today) })
    }
    function selectDay(day) {
      selectedDay.value = day
    }
    function jumpToEvent(evt) {
      const d = new Date(evt.event_time)
      currentDate.value = d
      selectDay({ day: d.getDate(), date: d, isCurrentMonth: true, isToday: false, events: eventsOnDate(d) })
    }

    // ==== CRUD ====
    async function loadEvents() {
      loading.value = true
      try { events.value = await listEvents() }
      catch (e) { error.value = e.message || '加载失败' }
      finally { loading.value = false }
    }

    async function handleDelete(id) {
      if (!confirm('确定删除？')) return
      try {
        await deleteEvent(id)
        events.value = events.value.filter(e => e.id !== id)
        if (selectedDay.value) selectedDay.value.events = eventsOnDate(selectedDay.value.date)
      } catch (e) { error.value = e.message || '删除失败' }
    }

    async function handleComplete(evt) {
      try {
        const resp = await fetch(`http://localhost:8000/events/${evt.id}`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ completed: true }),
        })
        if (!resp.ok) throw new Error('更新失败')
        evt.completed = true
      } catch (e) { error.value = e.message || '操作失败' }
    }

    async function toggleRemind() {
      if (remindEnabled.value) { reminder.stop(); remindEnabled.value = false }
      else {
        const ok = await reminder.start()
        remindEnabled.value = ok
        if (!ok) alert('需要浏览器通知权限才能开启提醒，请在浏览器设置中允许本站发送通知')
      }
    }

    function formatTime(isoStr) {
      if (!isoStr) return ''
      const d = new Date(isoStr)
      return `${d.getMonth() + 1}月${d.getDate()}日 ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    }

    function getRelativeTime(isoStr) {
      if (!isoStr) return ''
      const diff = new Date(isoStr) - new Date()
      if (diff < 0) return '已过期'
      const mins = Math.floor(diff / 60000)
      if (mins < 60) return `${mins}分钟后`
      const hours = Math.floor(mins / 60)
      if (hours < 24) return `${hours}小时后`
      const days = Math.floor(hours / 24)
      return `${days}天后`
    }

    onMounted(loadEvents)
    onUnmounted(() => reminder.stop())

    return {
      events, loading, error, currentDate, selectedDay, remindEnabled,
      weekDays, monthLabel, selectedDayLabel, selectedDayEvents, upcomingEvents,
      calendarDays,
      prevMonth, nextMonth, goToday, selectDay, jumpToEvent,
      handleDelete, handleComplete, toggleRemind,
      formatTime, getRelativeTime, eventColorClass, typeLabel,
    }
  },
}
</script>

<style scoped>
/* ===== 布局 ===== */
.calendar-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ===== 顶部栏 ===== */
.cal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}
.logo-link {
  font-size: 22px; font-weight: 700; color: #1a1a2e;
  text-decoration: none; letter-spacing: -0.3px;
}
.cal-nav { display: flex; gap: 10px; }
.nav-btn {
  padding: 8px 18px; border-radius: 8px; font-size: 14px;
  cursor: pointer; border: 1px solid #e2e8f0; background: white;
  color: #475569; text-decoration: none; font-weight: 500;
  transition: all 0.15s;
}
.nav-btn:hover { border-color: #3b82f6; color: #3b82f6; }
.nav-btn.active { background: #3b82f6; color: white; border-color: #3b82f6; }
.nav-btn.primary { background: #3b82f6; color: white; border-color: #3b82f6; }
.nav-btn.primary:hover { background: #2563eb; }

/* ===== 月份导航 ===== */
.month-nav {
  display: flex; align-items: center; justify-content: center;
  gap: 12px; margin-bottom: 20px;
}
.arrow-btn {
  width: 40px; height: 40px; border-radius: 10px;
  border: 1px solid #e2e8f0; background: white;
  font-size: 22px; color: #475569; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.arrow-btn:hover { background: #f1f5f9; border-color: #cbd5e1; }
.month-title {
  font-size: 20px; font-weight: 700; color: #1e293b;
  min-width: 140px; text-align: center; margin: 0;
}
.today-link {
  margin-left: 8px; padding: 8px 16px; border-radius: 8px;
  border: 1px solid #3b82f6; background: white; color: #3b82f6;
  font-size: 13px; font-weight: 600; cursor: pointer;
}
.today-link:hover { background: #eff6ff; }

/* ===== 星期头 ===== */
.weekdays {
  display: grid; grid-template-columns: repeat(7, 1fr);
  gap: 4px; margin-bottom: 6px;
}
.weekday { text-align: center; padding: 8px 0; }
.weekday-text {
  font-size: 12px; color: #94a3b8; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.5px;
}

/* ===== 日历网格 ===== */
.calendar-grid {
  display: grid; grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}
.day-cell {
  min-height: 72px;
  border-radius: 10px; padding: 6px 7px;
  cursor: pointer;
  background: white;
  border: 1px solid #f1f5f9;
  transition: all 0.12s;
  display: flex; flex-direction: column;
}
.day-cell:hover { border-color: #93c5fd; box-shadow: 0 2px 8px rgba(59,130,246,0.08); }
.day-cell.other-month { opacity: 0.25; background: #fafbfc; }
.day-cell.today {
  background: #eff6ff; border-color: #bfdbfe;
}
.day-cell.is-selected {
  border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.25);
}

.day-num {
  font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 3px;
}
.day-cell.today .day-num {
  background: #3b82f6; color: white;
  width: 25px; height: 25px; display: flex; align-items: center; justify-content: center;
  border-radius: 50%;
}

.day-events { display: flex; flex-direction: column; gap: 2px; flex: 1; overflow: hidden; }

/* 事件类型颜色条 */
.day-chip {
  font-size: 11px; padding: 2px 6px; border-radius: 4px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  font-weight: 500; line-height: 1.4;
}
.day-chip.completed { opacity: 0.5; text-decoration: line-through; }
.more-tag { font-size: 10px; color: #94a3b8; padding-left: 4px; }

/* ===== 类型颜色 ===== */
.type-meeting  { background: #dbeafe; color: #1e40af; }
.type-sport    { background: #dcfce7; color: #166534; }
.type-birthday { background: #fce7f3; color: #9d174d; }
.type-date     { background: #fef3c7; color: #92400e; }
.type-reminder { background: #e0e7ff; color: #3730a3; }
.type-shop     { background: #ffe4e6; color: #9f1239; }
.type-medical  { background: #ccfbf1; color: #134e4a; }
.type-travel   { background: #f3e8ff; color: #6b21a8; }
.type-study    { background: #fff7ed; color: #9a3412; }
.type-other    { background: #f1f5f9; color: #475569; }

/* ===== 天详情面板 ===== */
.day-detail {
  margin-top: 24px;
  background: white; border: 1px solid #e2e8f0; border-radius: 14px;
  overflow: hidden;
}
.day-detail-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; background: #f8fafc; border-bottom: 1px solid #e2e8f0;
}
.day-detail-header h3 { font-size: 17px; color: #1e293b; margin: 0; font-weight: 700; }
.close-detail {
  width: 32px; height: 32px; border-radius: 8px; border: none;
  background: #f1f5f9; color: #64748b; font-size: 16px; cursor: pointer;
}
.close-detail:hover { background: #e2e8f0; }

.empty-state { text-align: center; padding: 40px 20px; }
.empty-state.small { padding: 24px; }
.empty-icon { font-size: 36px; margin-bottom: 8px; }
.empty-state p { color: #94a3b8; font-size: 15px; margin: 0 0 12px; }
.empty-action {
  display: inline-block; padding: 8px 20px; border-radius: 8px;
  background: #3b82f6; color: white; text-decoration: none; font-size: 14px; font-weight: 500;
}

/* ===== 事件卡片 ===== */
.event-cards { padding: 12px 16px; display: flex; flex-direction: column; gap: 10px; }
.event-card {
  display: flex; align-items: stretch;
  border-radius: 10px; overflow: hidden;
  border: 1px solid #e2e8f0;
  transition: box-shadow 0.15s;
}
.event-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
.event-card.completed { opacity: 0.5; }

.event-left-bar { width: 4px; flex-shrink: 0; }
.event-left-bar.type-meeting  { background: #3b82f6; }
.event-left-bar.type-sport    { background: #22c55e; }
.event-left-bar.type-birthday { background: #ec4899; }
.event-left-bar.type-date     { background: #f59e0b; }
.event-left-bar.type-reminder { background: #6366f1; }
.event-left-bar.type-shop     { background: #f43f5e; }
.event-left-bar.type-medical  { background: #14b8a6; }
.event-left-bar.type-travel   { background: #a855f7; }
.event-left-bar.type-study    { background: #f97316; }
.event-left-bar.type-other    { background: #94a3b8; }

.event-body { flex: 1; padding: 12px 14px; min-width: 0; }
.event-row1 { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.evt-title { font-size: 15px; font-weight: 600; color: #1e293b; }
.evt-type { font-size: 11px; padding: 3px 8px; border-radius: 5px; font-weight: 500; }
.event-row2 { display: flex; gap: 16px; font-size: 13px; color: #64748b; margin-bottom: 2px; }
.evt-relative { color: #94a3b8; }
.event-row3 { font-size: 13px; color: #94a3b8; margin-top: 4px; }

.event-actions {
  display: flex; flex-direction: column; justify-content: center;
  gap: 4px; padding: 8px;
}
.eact-btn {
  width: 30px; height: 30px; border-radius: 6px; border: none;
  font-size: 16px; cursor: pointer; color: #94a3b8; background: transparent;
  display: flex; align-items: center; justify-content: center;
}
.eact-btn:hover { background: #f1f5f9; color: #475569; }
.eact-btn.del:hover { background: #fef2f2; color: #ef4444; }
.eact-btn.check:hover { background: #f0fdf4; color: #22c55e; }
.done-badge { width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; color: #22c55e; font-size: 18px; font-weight: 700; }

/* ===== 近期日程 ===== */
.upcoming-section { margin-top: 24px; }
.section-title { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0 0 12px; }
.upcoming-list { display: flex; flex-direction: column; gap: 6px; }
.upcoming-item {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 16px; border-radius: 10px;
  border: 1px solid #f1f5f9; background: white;
  cursor: pointer; transition: all 0.12s;
}
.upcoming-item:hover { border-color: #e2e8f0; box-shadow: 0 1px 6px rgba(0,0,0,0.04); }
.upcoming-item.completed { opacity: 0.5; }
.up-color { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.up-color.type-meeting  { background: #3b82f6; }
.up-color.type-sport    { background: #22c55e; }
.up-color.type-birthday { background: #ec4899; }
.up-color.type-date     { background: #f59e0b; }
.up-color.type-reminder { background: #6366f1; }
.up-color.type-shop     { background: #f43f5e; }
.up-color.type-medical  { background: #14b8a6; }
.up-color.type-travel   { background: #a855f7; }
.up-color.type-study    { background: #f97316; }
.up-color.type-other    { background: #94a3b8; }
.up-body { flex: 1; display: flex; justify-content: space-between; }
.up-title { font-size: 14px; font-weight: 600; color: #334155; }
.up-time { font-size: 13px; color: #94a3b8; }
.up-relative { font-size: 12px; color: #94a3b8; flex-shrink: 0; }

/* ===== 公共 ===== */
.center-msg { text-align: center; padding: 40px; color: #94a3b8; }
.error-toast {
  margin-top: 12px; padding: 10px 14px;
  background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;
  color: #dc2626; font-size: 13px;
  display: flex; justify-content: space-between; align-items: center;
}
.close-btn { background: none; border: none; font-size: 18px; cursor: pointer; color: #dc2626; }
</style>
