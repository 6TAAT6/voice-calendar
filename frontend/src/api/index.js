// ===== API 客户端 =====
// 封装所有向后端发请求的函数
const BASE_URL = 'http://localhost:8000'

/**
 * 发送 PCM 音频到后端进行语音识别
 */
export async function recognizeSpeech(pcmData) {
  const response = await fetch(`${BASE_URL}/speech/recognize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/octet-stream' },
    body: pcmData,
  })
  if (!response.ok) {
    const err = await response.json()
    throw new Error(err.error || err.detail || '语音识别失败')
  }
  return response.json()
}

/**
 * 将自然语言文字解析为结构化日程
 */
export async function parseText(text) {
  const response = await fetch(`${BASE_URL}/nlp/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!response.ok) {
    const err = await response.json()
    throw new Error(err.error || err.detail || '语义解析失败')
  }
  return response.json()
}

/**
 * AI 对话修正：用户说"不对，改成xxx"
 *
 * @param {string} originalText - 第一次识别/解析的文字
 * @param {string} correctionText - 用户说的修正指令
 */
export async function correctSchedule(originalText, correctionText) {
  const response = await fetch(`${BASE_URL}/nlp/correct`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      original_text: originalText,
      correction_text: correctionText,
    }),
  })
  if (!response.ok) {
    const err = await response.json()
    throw new Error(err.error || err.detail || 'AI 修正失败')
  }
  return response.json()
}

/**
 * 文字转语音 → 返回音频 Blob
 *
 * @param {string} text - 要合成的文字
 * @returns {Promise<Blob>} MP3 音频 Blob
 */
export async function synthesizeSpeech(text) {
  const response = await fetch(`${BASE_URL}/speech/synthesize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!response.ok) {
    const err = await response.json()
    throw new Error(err.error || err.detail || '语音合成失败')
  }
  return response.blob()
}

/**
 * 创建事件（支持冲突检测）
 *
 * 如果后端检测到冲突，会返回 { success: false, should_confirm: true, warnings: [...] }
 * 前端展示警告，用户确认后用 force_create=true 重新调用
 */
export async function createEvent(eventData, forceCreate = false) {
  const response = await fetch(`${BASE_URL}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...eventData, force_create: forceCreate }),
  })
  if (!response.ok) {
    const err = await response.json()
    throw new Error(err.error || err.detail || '创建事件失败')
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
    throw new Error(err.error || err.detail || '获取事件失败')
  }
  return response.json()
}

/**
 * 更新事件
 */
export async function updateEvent(eventId, data) {
  const response = await fetch(`${BASE_URL}/events/${eventId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const err = await response.json()
    throw new Error(err.error || err.detail || '更新事件失败')
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
    throw new Error(err.error || err.detail || '删除事件失败')
  }
  return true
}
