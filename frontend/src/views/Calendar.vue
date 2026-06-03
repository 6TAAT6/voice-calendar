<!-- Calendar.vue — 三视图日历 + 搜索 + 统计 + 导出 -->
<template>
  <div class="cal-app">
    <!-- ═══ 顶部栏 ═══ -->
    <header class="cal-topbar">
      <router-link to="/" class="cal-logo">🎙️ 语音日历</router-link>
      <div class="cal-top-actions">
        <button class="tb-btn" :class="{ on: remindEnabled }" @click="toggleRemind">
          🔔 {{ remindEnabled ? '提醒中' : '提醒' }}
        </button>
        <router-link to="/" class="tb-btn prim">+ 添加</router-link>
      </div>
    </header>

    <!-- ═══ 搜索栏 ═══ -->
    <div class="search-bar">
      <input v-model="searchQuery" placeholder="搜索日程..." class="search-input" @input="onSearchChange" />
      <select v-model="typeFilter" class="filter-select" @change="onSearchChange">
        <option value="">全部类型</option>
        <option v-for="t in allTypes" :key="t" :value="t">{{ t }}</option>
      </select>
      <button class="tb-btn sm" @click="exportICS">📥 导出日历</button>
    </div>

    <!-- ═══ 统计面板 ═══ -->
    <div class="stats-row" v-if="stats">
      <div class="stat-card">
        <div class="stat-num">{{ stats.this_month }}</div>
        <div class="stat-label">本月日程</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ stats.this_week }}</div>
        <div class="stat-label">本周</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ stats.upcoming_3days }}</div>
        <div class="stat-label">近3天</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ stats.completion_rate }}%</div>
        <div class="stat-label">完成率</div>
      </div>
    </div>

    <!-- ═══ 视图切换 + 月份导航 ═══ -->
    <div class="view-nav">
      <div class="view-tabs">
        <button :class="{ active: viewMode === 'month' }" @click="viewMode = 'month'">月</button>
        <button :class="{ active: viewMode === 'week' }" @click="viewMode = 'week'">周</button>
        <button :class="{ active: viewMode === 'day' }" @click="viewMode = 'day'">日</button>
      </div>
      <button class="arr-btn" @click="prev">‹</button>
      <h2 class="nav-title">{{ viewTitle }}</h2>
      <button class="arr-btn" @click="next">›</button>
      <button class="today-btn" @click="goToday">今天</button>
    </div>

    <!-- ═══ 月视图 ═══ -->
    <div v-if="viewMode === 'month'">
      <div class="weekdays">
        <span v-for="d in weekDays" :key="d" class="wd">{{ d }}</span>
      </div>
      <div class="month-grid">
        <div
          v-for="(d, i) in monthDays" :key="i"
          class="m-cell"
          :class="{ 'm-other': !d.inMonth, 'm-today': d.isToday, 'm-sel': selDay && selDay.d === d.d && selDay.m === d.m }"
          @click="selectMonthDay(d)"
        >
          <span class="m-num">{{ d.d }}</span>
          <div class="m-chips">
            <div
              v-for="ev in d.evs.slice(0, 2)" :key="ev.id"
              class="m-chip" :class="colorClass(ev.event_type)"
            >{{ ev.title.slice(0,4) }}{{ ev.title.length>4?'…':'' }}</div>
            <div v-if="d.evs.length>2" class="m-more">+{{ d.evs.length-2 }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 周视图 ═══ -->
    <div v-else-if="viewMode === 'week'" class="week-view">
      <template v-for="(d, di) in weekDaysFull" :key="di">
        <div class="w-col" :class="{ 'w-today': d.isToday }">
          <div class="w-head">{{ weekDays[di] }} {{ d.d }}/{{ d.m+1 }}</div>
          <div class="w-slots">
            <template v-for="h in 24" :key="h">
              <div class="w-slot" :class="{ 'w-has': d.evsByHour[h-1] }">
                <span class="w-hour">{{ h-1 }}:00</span>
                <div v-if="d.evsByHour[h-1]" class="w-ev" :class="colorClass(d.evsByHour[h-1][0].event_type)">
                  {{ d.evsByHour[h-1][0].title }}
                </div>
              </div>
            </template>
          </div>
        </div>
      </template>
    </div>

    <!-- ═══ 日视图 ═══ -->
    <div v-else-if="viewMode === 'day'" class="day-view">
      <h3 class="dv-date">{{ dayViewDate }}</h3>
      <div v-if="dayEvents.length === 0" class="empty-state">
        <p>当天暂无日程</p>
        <router-link to="/" class="empty-act">+ 添加日程</router-link>
      </div>
      <div v-else class="dv-timeline">
        <div v-for="ev in dayEvents" :key="ev.id" class="dv-row">
          <div class="dv-time">{{ timeOnly(ev.event_time) }}</div>
          <div class="dv-bar" :class="colorClass(ev.event_type)">
            <div class="dv-left" :class="colorClass(ev.event_type)"></div>
            <div class="dv-body">
              <div class="dv-title">{{ ev.title }}
                <span class="dv-type" :class="colorClass(ev.event_type)">{{ ev.event_type }}</span>
                <span v-if="ev.recurrence && ev.recurrence !== 'none'" class="dv-rec">🔄</span>
              </div>
              <div v-if="ev.description" class="dv-desc">{{ ev.description }}</div>
            </div>
            <div class="dv-act">
              <button v-if="!ev.completed" class="dv-btn" @click.stop="handleComplete(ev)" title="完成">○</button>
              <span v-else class="dv-done">✓</span>
              <button class="dv-btn dv-del" @click.stop="handleDelete(ev.id)">✕</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 点击月视图某天：下方展示事件 ═══ -->
    <div v-if="viewMode === 'month' && selDay" class="detail-panel">
      <div class="dp-head">
        <h3>{{ selDayLabel }}</h3>
        <button class="dp-close" @click="selDay = null">✕</button>
      </div>
      <div v-if="selEvents.length === 0" class="empty-state">
        <p>当天暂无日程</p>
        <router-link to="/" class="empty-act">+ 添加日程</router-link>
      </div>
      <div v-else class="event-cards">
        <div v-for="ev in selEvents" :key="ev.id" class="ev-card" :class="{ 'ev-done': ev.completed }">
          <div class="ev-bar" :class="colorClass(ev.event_type)"></div>
          <div class="ev-body">
            <div class="ev-r1">
              <span class="ev-title">{{ ev.title }}</span>
              <span v-if="ev.recurrence && ev.recurrence !== 'none'" class="dv-rec" :title="'重复:'+ev.recurrence">🔄</span>
              <span class="ev-type" :class="colorClass(ev.event_type)">{{ ev.event_type }}</span>
            </div>
            <div class="ev-r2">🕐 {{ formatTime(ev.event_time) }} · {{ relTime(ev.event_time) }}</div>
            <div v-if="ev.description" class="ev-r3">{{ ev.description }}</div>
          </div>
          <div class="ev-acts">
            <button v-if="!ev.completed" class="ea-btn ok" @click.stop="handleComplete(ev)">○</button>
            <span v-else class="ea-done">✓</span>
            <button class="ea-btn no" @click.stop="handleDelete(ev.id)">✕</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ 加载/错误 ═══ -->
    <div v-if="loading" class="msg">⏳ 加载中...</div>
    <div v-if="error" class="err">{{ error }}<button @click="error=''" class="err-x">×</button></div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listEvents, deleteEvent } from '../api/index'
import { useReminder } from '../composables/useReminder'

const TYPES = ['会议','运动','生日','约会','提醒','购物','就医','旅行','学习','其他']
const WEEK = ['日','一','二','三','四','五','六']
const CC = {
  '会议':'t1','运动':'t2','生日':'t3','约会':'t4','提醒':'t5',
  '购物':'t6','就医':'t7','旅行':'t8','学习':'t9','其他':'t0'
}

export default {
  name: 'Calendar',
  setup() {
    const events = ref([])
    const loading = ref(true)
    const error = ref('')
    const currentDate = ref(new Date())
    const selDay = ref(null)
    const remindEnabled = ref(false)
    const viewMode = ref('month')
    const searchQuery = ref('')
    const typeFilter = ref('')
    const stats = ref(null)

    const reminder = useReminder(events, 30000)
    const router = useRouter()

    const allTypes = TYPES
    const weekDays = WEEK

    // ==== 导航标题 ====
    const viewTitle = computed(() => {
      const d = currentDate.value
      const y = d.getFullYear()
      const m = d.getMonth() + 1
      if (viewMode.value === 'month') return `${y}年${m}月`
      if (viewMode.value === 'week') {
        const mon = new Date(y, m-1, 1)
        const firstDay = new Date(y, m-1, 1 - mon.getDay())
        const lastDay = new Date(firstDay); lastDay.setDate(firstDay.getDate() + 6)
        return `${firstDay.getMonth()+1}/${firstDay.getDate()} - ${lastDay.getMonth()+1}/${lastDay.getDate()}`
      }
      return `${y}年${m}月${d.getDate()}日`
    })

    const dayViewDate = computed(() => {
      const d = currentDate.value
      return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日 周${WEEK[d.getDay()]}`
    })

    const selDayLabel = computed(() => {
      if (!selDay.value) return ''
      const d = new Date(selDay.value.y, selDay.value.m, selDay.value.d)
      return `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日 周${WEEK[d.getDay()]}`
    })

    // ==== 事件工具 ====
    function evOnDate(date) {
      return events.value.filter(ev => {
        const ed = new Date(ev.event_time)
        return ed.getFullYear() === date.getFullYear() && ed.getMonth() === date.getMonth() && ed.getDate() === date.getDate()
      })
    }

    function colorClass(t) { return CC[t] || 't0' }
    function timeOnly(iso) {
      if (!iso) return ''
      const d = new Date(iso); return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
    }
    function formatTime(iso) {
      if (!iso) return ''
      const d = new Date(iso)
      return `${d.getMonth()+1}月${d.getDate()}日 ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
    }
    function relTime(iso) {
      if (!iso) return ''
      const diff = new Date(iso) - new Date()
      if (diff < 0) return '已过期'
      const m = Math.floor(diff/60000)
      if (m < 60) return `${m}分钟后`
      const h = Math.floor(m/60)
      if (h < 24) return `${h}小时后`
      return `${Math.floor(h/24)}天后`
    }

    // ==== 月视图数据 ====
    const monthDays = computed(() => {
      const y = currentDate.value.getFullYear()
      const m = currentDate.value.getMonth()
      const today = new Date()
      const tY = today.getFullYear(); const tM = today.getMonth(); const tD = today.getDate()

      const firstDOW = new Date(y, m, 1).getDay()
      const daysInM = new Date(y, m+1, 0).getDate()
      const daysInPrev = new Date(y, m, 0).getDate()

      const arr = []
      for (let i = firstDOW-1; i >= 0; i--) {
        const d = daysInPrev - i
        arr.push({ d, m: m-1, y: m===0?y-1:y, inMonth: false, isToday: false, evs: evOnDate(new Date(m===0?y-1:y, m-1, d)) })
      }
      for (let d = 1; d <= daysInM; d++) {
        arr.push({ d, m, y, inMonth: true, isToday: y===tY && m===tM && d===tD, evs: evOnDate(new Date(y, m, d)) })
      }
      const rem = arr.length <= 35 ? 35 - arr.length : 42 - arr.length
      for (let d = 1; d <= rem; d++) {
        arr.push({ d, m: m+1, y: m===11?y+1:y, inMonth: false, isToday: false, evs: evOnDate(new Date(m===11?y+1:y, m+1, d)) })
      }
      return arr
    })

    function selectMonthDay(d) {
      selDay.value = { d: d.d, m: d.m, y: d.y }
    }

    const selEvents = computed(() => {
      if (!selDay.value) return []
      const s = selDay.value
      return evOnDate(new Date(s.y, s.m, s.d))
    })

    // ==== 周视图 ====
    const weekDaysFull = computed(() => {
      const d = new Date(currentDate.value)
      const dow = d.getDay()
      const mon = new Date(d); mon.setDate(d.getDate() - dow)
      const arr = []
      for (let i = 0; i < 7; i++) {
        const day = new Date(mon); day.setDate(mon.getDate() + i)
        const now = new Date()
        const evs = evOnDate(day)
        const evsByHour = {}
        for (let h = 0; h < 24; h++) {
          const hevs = evs.filter(ev => new Date(ev.event_time).getHours() === h)
          if (hevs.length) evsByHour[h] = hevs
        }
        arr.push({
          d: day.getDate(), m: day.getMonth(), y: day.getFullYear(),
          isToday: day.toDateString() === now.toDateString(),
          evs, evsByHour
        })
      }
      return arr
    })

    // ==== 日视图 ====
    const dayEvents = computed(() => {
      const d = currentDate.value
      return evOnDate(new Date(d.getFullYear(), d.getMonth(), d.getDate()))
        .sort((a, b) => new Date(a.event_time) - new Date(b.event_time))
    })

    // ==== 导航 ====
    function prev() {
      const d = new Date(currentDate.value)
      if (viewMode.value === 'month') d.setMonth(d.getMonth()-1)
      else if (viewMode.value === 'week') d.setDate(d.getDate()-7)
      else d.setDate(d.getDate()-1)
      currentDate.value = d; selDay.value = null
    }
    function next() {
      const d = new Date(currentDate.value)
      if (viewMode.value === 'month') d.setMonth(d.getMonth()+1)
      else if (viewMode.value === 'week') d.setDate(d.getDate()+7)
      else d.setDate(d.getDate()+1)
      currentDate.value = d; selDay.value = null
    }
    function goToday() {
      currentDate.value = new Date(); selDay.value = null
    }

    // ==== 搜索/筛选 ====
    let searchTimer = null
    function onSearchChange() {
      clearTimeout(searchTimer)
      searchTimer = setTimeout(() => loadEvents(), 200)
    }

    // ==== 加载 ====
    async function loadEvents() {
      loading.value = true
      try {
        const params = {}
        if (searchQuery.value) params.search = searchQuery.value
        if (typeFilter.value) params.event_type = typeFilter.value
        events.value = await listEvents(params)
      } catch (e) { error.value = e.message || '加载失败' }
      finally { loading.value = false }
    }

    async function loadStats() {
      try { const r = await fetch('http://localhost:8000/stats'); stats.value = await r.json() }
      catch { /* stats not critical */ }
    }

    // ==== CRUD ====
    async function handleDelete(id) {
      if (!confirm('确定删除？')) return
      try {
        await deleteEvent(id)
        events.value = events.value.filter(e => e.id !== id)
        selDay.value = null
      } catch (e) { error.value = e.message }
    }
    async function handleComplete(ev) {
      try {
        const r = await fetch(`http://localhost:8000/events/${ev.id}`, {
          method: 'PUT', headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ completed: true })
        })
        if (!r.ok) throw new Error('更新失败')
        ev.completed = true
      } catch (e) { error.value = e.message }
    }

    // ==== 导出 ====
    function exportICS() {
      window.open('http://localhost:8000/events/export', '_blank')
    }

    // ==== 提醒 ====
    async function toggleRemind() {
      if (remindEnabled.value) { reminder.stop(); remindEnabled.value = false }
      else {
        const ok = await reminder.start()
        remindEnabled.value = ok
        if (!ok) alert('需要浏览器通知权限')
      }
    }

    onMounted(() => { loadEvents(); loadStats() })
    onUnmounted(() => reminder.stop())

    return {
      events, loading, error, stats, currentDate, selDay, remindEnabled,
      viewMode, searchQuery, typeFilter, allTypes, weekDays,
      viewTitle, dayViewDate, selDayLabel,
      monthDays, selEvents, weekDaysFull, dayEvents,
      prev, next, goToday, selectMonthDay,
      onSearchChange, loadEvents, loadStats,
      handleDelete, handleComplete, toggleRemind,
      formatTime, relTime, timeOnly, colorClass, exportICS
    }
  },
}
</script>

<style scoped>
.cal-app { max-width: 1040px; margin: 0 auto; padding: 20px 16px; font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }

/* ===== 顶部 ===== */
.cal-topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.cal-logo { font-size: 20px; font-weight: 700; color: #1a1a2e; text-decoration: none; }
.cal-top-actions { display: flex; gap: 8px; }
.tb-btn { padding: 7px 16px; border-radius: 8px; font-size: 13px; cursor: pointer; border: 1px solid #e2e8f0; background: white; color: #475569; text-decoration: none; font-weight: 500; transition: all 0.15s; }
.tb-btn:hover { border-color: #3b82f6; color: #3b82f6; }
.tb-btn.on { background: #3b82f6; color: white; border-color: #3b82f6; }
.tb-btn.prim { background: #3b82f6; color: white; border-color: #3b82f6; }
.tb-btn.prim:hover { background: #2563eb; }
.tb-btn.sm { font-size: 12px; padding: 6px 12px; }

/* ===== 搜索 ===== */
.search-bar { display: flex; gap: 8px; margin-bottom: 16px; align-items: center; }
.search-input {
  flex: 1; padding: 9px 14px; border-radius: 10px;
  border: 1px solid #e2e8f0; font-size: 14px; outline: none;
  transition: border-color 0.15s;
}
.search-input:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.1); }
.filter-select {
  padding: 9px 12px; border-radius: 10px;
  border: 1px solid #e2e8f0; font-size: 13px; background: white; cursor: pointer;
  outline: none; color: #475569;
}

/* ===== 统计 ===== */
.stats-row { display: flex; gap: 10px; margin-bottom: 18px; }
.stat-card {
  flex: 1; text-align: center; padding: 14px 8px;
  background: white; border: 1px solid #f1f5f9; border-radius: 12px;
}
.stat-num { font-size: 24px; font-weight: 700; color: #1e293b; }
.stat-label { font-size: 12px; color: #94a3b8; margin-top: 2px; }

/* ===== 视图切换 ===== */
.view-nav { display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 18px; }
.view-tabs { display: flex; gap: 2px; background: #f1f5f9; border-radius: 8px; padding: 3px; margin-right: 8px; }
.view-tabs button {
  padding: 6px 18px; border-radius: 6px; border: none; background: transparent;
  font-size: 13px; font-weight: 600; color: #64748b; cursor: pointer; transition: all 0.15s;
}
.view-tabs button.active { background: white; color: #1e293b; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.nav-title { font-size: 18px; font-weight: 700; color: #1e293b; min-width: 140px; text-align: center; margin: 0; }
.arr-btn {
  width: 36px; height: 36px; border-radius: 8px; border: 1px solid #e2e8f0;
  background: white; font-size: 20px; color: #64748b; cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.15s;
}
.arr-btn:hover { background: #f8fafc; border-color: #cbd5e1; }
.today-btn { padding: 7px 14px; border-radius: 8px; border: 1px solid #3b82f6; background: white; color: #3b82f6; font-size: 12px; font-weight: 600; cursor: pointer; }

/* ===== 月视图 ===== */
.weekdays { display: grid; grid-template-columns: repeat(7,1fr); gap: 3px; margin-bottom: 4px; }
.wd { text-align: center; font-size: 12px; color: #94a3b8; font-weight: 700; padding: 6px 0; }
.month-grid { display: grid; grid-template-columns: repeat(7,1fr); gap: 3px; }
.m-cell {
  min-height: 74px; border-radius: 10px; padding: 5px 6px; cursor: pointer;
  background: white; border: 1px solid #f1f5f9; transition: all 0.12s;
  display: flex; flex-direction: column;
}
.m-cell:hover { border-color: #93c5fd; }
.m-other { opacity: 0.3; }
.m-today { background: #eff6ff; border-color: #bfdbfe; }
.m-sel { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.2); }
.m-num { font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 2px; }
.m-today .m-num { background: #3b82f6; color: white; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 50%; }
.m-chips { display: flex; flex-direction: column; gap: 1px; }
.m-chip { font-size: 10px; padding: 2px 5px; border-radius: 4px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.m-more { font-size: 10px; color: #94a3b8; padding-left: 2px; }

/* Type colors */
.t1 { background: #dbeafe; color: #1e40af; }
.t2 { background: #dcfce7; color: #166534; }
.t3 { background: #fce7f3; color: #9d174d; }
.t4 { background: #fef3c7; color: #92400e; }
.t5 { background: #e0e7ff; color: #3730a3; }
.t6 { background: #ffe4e6; color: #9f1239; }
.t7 { background: #ccfbf1; color: #134e4a; }
.t8 { background: #f3e8ff; color: #6b21a8; }
.t9 { background: #fff7ed; color: #9a3412; }
.t0 { background: #f1f5f9; color: #475569; }

/* ===== 周视图 ===== */
.week-view { display: grid; grid-template-columns: repeat(7,1fr); gap: 3px; }
.w-col { border-radius: 10px; overflow: hidden; border: 1px solid #f1f5f9; }
.w-col.w-today { border-color: #bfdbfe; background: #fafcff; }
.w-head { text-align: center; font-size: 12px; font-weight: 600; color: #64748b; padding: 8px 2px; background: #f8fafc; }
.w-slots { }
.w-slot { padding: 2px 4px; font-size: 10px; color: #cbd5e1; min-height: 22px; border-top: 1px solid #f8fafc; }
.w-hour { margin-right: 2px; }
.w-ev { font-size: 10px; padding: 1px 4px; border-radius: 3px; margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.w-has { min-height: 28px; }

/* ===== 日视图 ===== */
.day-view { }
.dv-date { font-size: 17px; font-weight: 700; color: #1e293b; margin: 0 0 14px; }
.dv-timeline { display: flex; flex-direction: column; gap: 8px; }
.dv-row { display: flex; align-items: flex-start; gap: 10px; }
.dv-time { font-size: 13px; color: #94a3b8; min-width: 60px; padding-top: 10px; }
.dv-bar { flex: 1; display: flex; border-radius: 10px; border: 1px solid #e2e8f0; overflow: hidden; transition: box-shadow 0.15s; }
.dv-bar:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.dv-left { width: 4px; flex-shrink: 0; }
.dv-left.t1{background:#3b82f6}.dv-left.t2{background:#22c55e}.dv-left.t3{background:#ec4899}
.dv-left.t4{background:#f59e0b}.dv-left.t5{background:#6366f1}.dv-left.t6{background:#f43f5e}
.dv-left.t7{background:#14b8a6}.dv-left.t8{background:#a855f7}.dv-left.t9{background:#f97316}.dv-left.t0{background:#94a3b8}
.dv-body { flex: 1; padding: 10px 12px; }
.dv-title { font-size: 15px; font-weight: 600; color: #1e293b; }
.dv-type { font-size: 11px; padding: 2px 8px; border-radius: 5px; margin-left: 8px; }
.dv-rec { font-size: 13px; margin-left: 4px; cursor: help; }
.dv-desc { font-size: 12px; color: #94a3b8; margin-top: 3px; }
.dv-act { display: flex; flex-direction: column; justify-content: center; padding: 8px 6px; gap: 2px; }
.dv-btn { width: 28px; height: 28px; border-radius: 6px; border: none; background: transparent; font-size: 16px; cursor: pointer; color: #94a3b8; }
.dv-btn:hover { background: #f1f5f9; }
.dv-del:hover { background: #fef2f2; color: #ef4444; }
.dv-done { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; color: #22c55e; font-weight: 700; }

/* ===== 详情面板（月视图点天）===== */
.detail-panel { margin-top: 20px; border: 1px solid #e2e8f0; border-radius: 14px; overflow: hidden; background: white; }
.dp-head { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }
.dp-head h3 { font-size: 16px; color: #1e293b; margin: 0; }
.dp-close { width: 30px; height: 30px; border-radius: 8px; border: none; background: #f1f5f9; font-size: 15px; cursor: pointer; color: #64748b; }

/* ===== 事件卡片 ===== */
.event-cards { padding: 10px 14px; display: flex; flex-direction: column; gap: 8px; }
.ev-card { display: flex; border-radius: 10px; border: 1px solid #e2e8f0; overflow: hidden; }
.ev-card.ev-done { opacity: 0.5; }
.ev-bar { width: 4px; flex-shrink: 0; }
.ev-bar.t1{background:#3b82f6}.ev-bar.t2{background:#22c55e}.ev-bar.t3{background:#ec4899}
.ev-bar.t4{background:#f59e0b}.ev-bar.t5{background:#6366f1}.ev-bar.t6{background:#f43f5e}
.ev-bar.t7{background:#14b8a6}.ev-bar.t8{background:#a855f7}.ev-bar.t9{background:#f97316}.ev-bar.t0{background:#94a3b8}
.ev-body { flex: 1; padding: 12px 14px; min-width: 0; }
.ev-r1 { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.ev-title { font-size: 15px; font-weight: 600; color: #1e293b; }
.ev-type { font-size: 11px; padding: 2px 8px; border-radius: 5px; }
.ev-r2 { font-size: 13px; color: #64748b; }
.ev-r3 { font-size: 12px; color: #94a3b8; margin-top: 2px; }
.ev-acts { display: flex; flex-direction: column; justify-content: center; padding: 8px; gap: 2px; }
.ea-btn { width: 28px; height: 28px; border-radius: 6px; border: none; background: transparent; font-size: 16px; cursor: pointer; color: #94a3b8; }
.ea-btn:hover { background: #f1f5f9; }
.ea-btn.no:hover { background: #fef2f2; color: #ef4444; }
.ea-btn.ok:hover { background: #f0fdf4; color: #22c55e; }
.ea-done { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; color: #22c55e; font-weight: 700; }

/* ===== 公共 ===== */
.empty-state { text-align: center; padding: 32px 20px; color: #94a3b8; }
.empty-act { display: inline-block; margin-top: 8px; padding: 8px 18px; border-radius: 8px; background: #3b82f6; color: white; text-decoration: none; font-size: 14px; font-weight: 500; }
.msg { text-align: center; padding: 40px; color: #94a3b8; }
.err { margin-top: 12px; padding: 10px 14px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; color: #dc2626; font-size: 13px; display: flex; justify-content: space-between; align-items: center; }
.err-x { background: none; border: none; font-size: 18px; cursor: pointer; color: #dc2626; }
</style>
