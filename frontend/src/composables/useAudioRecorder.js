// ===== 音频录制模块 =====
// 封装浏览器的 MediaRecorder API
// 使用方式（在 .vue 文件里）：
//   import { useAudioRecorder } from '../composables/useAudioRecorder'
//   const { startRecording, stopRecording, isRecording, audioBlob } = useAudioRecorder()

import { ref } from 'vue'

export function useAudioRecorder() {
  // ---- 状态变量 ----
  const isRecording = ref(false)      // 是否正在录音
  const audioBlob = ref(null)         // 录音结果的音频数据
  const audioUrl = ref('')            // 录音结果的可播放链接（用于试听）
  const error = ref('')               // 错误信息
  const duration = ref(0)             // 录音时长（秒）
  const isProcessing = ref(false)     // 是否正在识别中

  // ---- 内部变量 ----
  let mediaRecorder = null            // MediaRecorder 实例
  let audioChunks = []                // 录音片段缓存
  let startTime = null                // 开始录音的时间
  let durationTimer = null            // 计时器

  /**
   * 开始录音
   * 1. 请求麦克风权限
   * 2. 创建 MediaRecorder 实例
   * 3. 开始录制
   */
  async function startRecording() {
    try {
      // 重置状态
      audioChunks = []
      audioBlob.value = null
      audioUrl.value = ''
      error.value = ''
      duration.value = 0

      // 请求麦克风：浏览器会弹出"是否允许使用麦克风"
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,        // 单声道（讯飞推荐）
          sampleRate: 16000,      // 16kHz 采样率（讯飞推荐）
          echoCancellation: true, // 回声消除
          noiseSuppression: true, // 降噪
        },
      })

      // 创建录音器
      // 优先用 audio/webm 格式（Chrome/Edge 原生支持）
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'

      mediaRecorder = new MediaRecorder(stream, { mimeType })

      // 每当积累一段音频数据，推入缓存
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }

      // 录音停止时的回调
      mediaRecorder.onstop = () => {
        // 生成 Blob 和可播放 URL
        audioBlob.value = new Blob(audioChunks, { type: mimeType })
        audioUrl.value = URL.createObjectURL(audioBlob.value)

        // 计算时长
        if (startTime) {
          duration.value = Math.round((Date.now() - startTime) / 1000)
        }

        // 释放麦克风
        stream.getTracks().forEach((track) => track.stop())
      }

      // 开始录制
      mediaRecorder.start()
      isRecording.value = true
      startTime = Date.now()

      // 启动计时器
      durationTimer = setInterval(() => {
        if (startTime) {
          duration.value = Math.round((Date.now() - startTime) / 1000)
        }
      }, 1000)
    } catch (err) {
      // 用户拒绝麦克风权限 或 设备不支持
      if (err.name === 'NotAllowedError') {
        error.value = '麦克风权限被拒绝，请在浏览器设置中允许访问麦克风'
      } else if (err.name === 'NotFoundError') {
        error.value = '未检测到麦克风设备'
      } else {
        error.value = `录音启动失败: ${err.message}`
      }
      console.error('录音错误:', err)
    }
  }

  /**
   * 停止录音
   * 返回音频 Blob（可以直接传给后端）
   */
  function stopRecording() {
    // 清除计时器
    if (durationTimer) {
      clearInterval(durationTimer)
      durationTimer = null
    }

    if (mediaRecorder && mediaRecorder.state === 'recording') {
      // onstop 回调里会生成 audioBlob
      mediaRecorder.stop()
    }

    isRecording.value = false
  }

  /**
   * 取消录音（不保留音频数据）
   */
  function cancelRecording() {
    stopRecording()
    audioBlob.value = null
    audioUrl.value = ''
    duration.value = 0
  }

  return {
    // 状态
    isRecording,
    audioBlob,
    audioUrl,
    error,
    duration,
    isProcessing,
    // 方法
    startRecording,
    stopRecording,
    cancelRecording,
  }
}
