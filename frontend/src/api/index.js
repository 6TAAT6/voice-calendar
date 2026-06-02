// ===== API 客户端 =====
// 封装所有向后端发请求的函数
// 后端地址：http://localhost:8000
// 前端地址：http://localhost:5173

const BASE_URL = 'http://localhost:8000'

/**
 * 发送音频到后端进行语音识别
 *
 * @param {Blob} audioBlob - 录音得到的音频数据
 * @returns {Promise<{text: string, success: boolean}>} 识别结果
 *
 * 使用方式：
 *   const result = await recognizeSpeech(audioBlob)
 *   console.log(result.text) // "明天下午三点开会"
 */
export async function recognizeSpeech(audioBlob) {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.wav')

  const response = await fetch(`${BASE_URL}/speech/recognize`, {
    method: 'POST',
    body: formData,
    // 不设置 Content-Type，浏览器会自动加上 multipart/form-data
  })

  if (!response.ok) {
    const err = await response.json()
    throw new Error(err.detail || '语音识别请求失败')
  }

  return response.json()
}

/**
 * 创建事件（后续 PR 对接）
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
