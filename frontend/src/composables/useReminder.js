// ===== 浏览器提醒服务 =====
// 使用浏览器 Notification API，在事件到期时弹窗提醒
// 不需要任何第三方服务，Chrome/Edge/Firefox 都支持
//
// 使用方式：
//   import { useReminder } from '../composables/useReminder'
//   const { start, stop } = useReminder(events, 60000) // 每分钟检查一次

import { ref } from 'vue'

export function useReminder(eventsRef, checkInterval = 30000) {
  let timer = null
  const permissionGranted = ref(false)
  const notifiedIds = ref(new Set()) // 已经提醒过的事件 ID，避免重复提醒

  /** 请求通知权限 */
  async function requestPermission() {
    if (!('Notification' in window)) {
      console.warn('浏览器不支持通知功能')
      return false
    }

    if (Notification.permission === 'granted') {
      permissionGranted.value = true
      return true
    }

    if (Notification.permission !== 'denied') {
      const result = await Notification.requestPermission()
      permissionGranted.value = result === 'granted'
      return permissionGranted.value
    }

    return false
  }

  /** 检查并发送提醒 */
  function checkAndNotify() {
    if (!permissionGranted.value) return
    if (!eventsRef.value || eventsRef.value.length === 0) return

    const now = new Date()

    for (const evt of eventsRef.value) {
      // 已完成的不提醒
      if (evt.completed) continue

      const eventTime = new Date(evt.event_time)

      // 事件已过期的不提醒
      if (eventTime < now) continue

      // 距离事件还有多少毫秒
      const diff = eventTime - now

      // 在事件开始前 5 分钟内提醒，且还没提醒过
      if (diff <= 5 * 60 * 1000 && !notifiedIds.value.has(evt.id)) {
        // 标记为已提醒
        notifiedIds.value.add(evt.id)

        // 发送浏览器通知
        const notification = new Notification('🔔 日程提醒', {
          body: `📌 ${evt.title}\n🕐 ${formatRemindTime(eventTime)}\n📂 ${evt.event_type}`,
          icon: '/favicon.svg',
          tag: `event-${evt.id}`, // 相同 tag 的通知会合并
          requireInteraction: true, // 不自动消失，需要用户点掉
        })

        // 点击通知跳到日历页
        notification.onclick = () => {
          window.focus()
          window.location.hash = '#/calendar'
          notification.close()
        }
      }
    }

    // 清理旧事件（已过期超过 1 小时的事件）
    for (const id of notifiedIds.value) {
      const evt = eventsRef.value.find((e) => e.id === id)
      if (!evt || new Date(evt.event_time) < new Date(now - 3600000)) {
        notifiedIds.value.delete(id)
      }
    }
  }

  /** 启动提醒服务 */
  async function start() {
    const ok = await requestPermission()
    if (!ok) {
      console.warn('通知权限未获得，提醒功能不可用')
      return false
    }
    // 立即检查一次
    checkAndNotify()
    // 定时检查
    timer = setInterval(checkAndNotify, checkInterval)
    console.log(`提醒服务已启动，每 ${checkInterval / 1000} 秒检查一次`)
    return true
  }

  /** 停止提醒服务 */
  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  return { start, stop, permissionGranted, requestPermission }
}

/** 格式化提醒时间 */
function formatRemindTime(date) {
  const M = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const m = String(date.getMinutes()).padStart(2, '0')
  return `${M}月${d}日 ${h}:${m}`
}
