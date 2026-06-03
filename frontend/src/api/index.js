// ===== API 客户端 =====
// 封装所有向后端发请求的函数
const BASE_URL = 'http://localhost:8000'

/**
 * 发送 PCM 音频到后端进行语音识别
 *
 * @param {ArrayBuffer} pcmData - 前端已转换好的 PCM 数据（16kHz/16bit/单声道）
 * @returns {Promise<{text: string, success: boolean}>}
 */
export async function recognizeSpeech(pcmData) {
  const response = await fetch(`${BASE_URL}/speech/recognize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/octet-stream' },
    body: pcmData,
  })
  if (!response.ok) {
    const err = await response.json()
    throw new Error(err.detail || '语音识别失败')
  }
  return response.json()
}

/**
 * 将自然语言文字解析为结构化日程
 *
 * @param {string} text - 用户说的话（语音识别结果）
 * @returns {Promise<{title, event_time, event_type, description, remind}>}
 *
 * 例：parseText("明天下午三点开产品评审会")
 *   → { title: "产品评审会", event_time: "2026-06-04T15:00:00", ... }
 */
export async function parseText(text) {
  const response = await fetch(`${BASE_URL}/nlp/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!response.ok) {
    const err = await response.json()
    throw new Error(err.detail || '语义解析失败')
  }
  return response.json()
}

/**
 * 创建事件
 */
export async function createEvent(eventData) {
  const response = await fetch(`${BASE_URL}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(eventData),
  })
  if (!response.ok) {
    const err = await response.json()
    throw new Error(err.detail || '创建事件失败')
  }
  return response.json()
}

/**
 * 获取事件列表
 */
export async function listEvents(params = {}) {
  const query = new URLSearchParams(params).toString()
  const response = await fetch(`${BASE_URL}/events?${query}`)
  if (!response.ok) {
    const err = await response.json()
    throw new Error(err.detail || '获取事件失败')
  }
  return response.json()
}

/**
 * 删除事件
 */
export async function deleteEvent(eventId) {
  const response = await fetch(`${BASE_URL}/events/${eventId}`, {
    method: 'DELETE',
  })
  if (!response.ok && response.status !== 204) {
    const err = await response.json()
    throw new Error(err.detail || '删除事件失败')
  }
  return true
}
