// ===== 音频录制模块 =====
// 双轨录制：MediaRecorder（试听）+ AudioContext ScriptProcessor（PCM 采集）
// 使用方式（在 .vue 文件里）：
//   import { useAudioRecorder } from '../composables/useAudioRecorder'
//   const { startRecording, stopRecording, isRecording, pcmData, audioBlob } = useAudioRecorder()

import { ref } from 'vue'

export function useAudioRecorder() {
  // ---- 状态变量 ----
  const isRecording = ref(false)      // 是否正在录音
  const audioBlob = ref(null)         // WebM 数据（用于试听回放）
  const audioUrl = ref('')            // 试听链接
  const pcmData = ref(null)           // PCM ArrayBuffer（发给后端）
  const error = ref('')               // 错误信息
  const duration = ref(0)             // 录音时长（秒）
  const isProcessing = ref(false)     // 是否正在识别中

  // ---- 内部变量 ----
  let mediaRecorder = null            // MediaRecorder 实例（生成试听文件）
  let audioChunks = []                // WebM 片段缓存
  let audioCtx = null                 // AudioContext（PCM 采集）
  let pcmChunks = []                  // Int16Array 片段缓存
  let startTime = null                // 开始录音的时间
  let durationTimer = null            // 计时器

  /**
   * 开始录音
   *
   * 双轨并行：
   *   track1: MediaRecorder → WebM → 试听回放
   *   track2: AudioContext ScriptProcessor → 实时 PCM → 发给讯飞
   */
  async function startRecording() {
    try {
      // 重置状态
      audioChunks = []
      pcmChunks = []
      audioBlob.value = null
      audioUrl.value = ''
      pcmData.value = null
      error.value = ''
      duration.value = 0

      // 请求麦克风
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })

      // ==== Track 1: MediaRecorder（生成 WebM 试听文件）====
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'

      mediaRecorder = new MediaRecorder(stream, { mimeType })

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        // 生成试听 URL
        audioBlob.value = new Blob(audioChunks, { type: mimeType })
        audioUrl.value = URL.createObjectURL(audioBlob.value)

        // 计算时长
        if (startTime) {
          duration.value = Math.round((Date.now() - startTime) / 1000)
        }

        // 释放麦克风
        stream.getTracks().forEach((track) => track.stop())
      }

      // ==== Track 2: AudioContext ScriptProcessor（实时采集 PCM）====
      audioCtx = new AudioContext({ sampleRate: 16000 })
      const source = audioCtx.createMediaStreamSource(stream)

      // ScriptProcessorNode: bufferSize=4096, 1 输入声道, 1 输出声道
      // 虽然官方标记为 deprecated，但所有现代浏览器仍支持，AudioWorklet 更复杂不必要
      const processor = audioCtx.createScriptProcessor(4096, 1, 1)

      processor.onaudioprocess = (event) => {
        if (!isRecording.value) return
        // inputBuffer.getChannelData(0) → Float32Array, 范围 -1.0 ~ 1.0
        const floatData = event.inputBuffer.getChannelData(0)
        const int16 = new Int16Array(floatData.length)
        for (let i = 0; i < floatData.length; i++) {
          const s = Math.max(-1, Math.min(1, floatData[i]))
          int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
        }
        pcmChunks.push(int16)
      }

      // 连接节点链：source → processor → destination
      // destination 是必须的，虽然不播放声音
      source.connect(processor)
      processor.connect(audioCtx.destination)

      // ==== 开始录制 ====
      mediaRecorder.start()
      isRecording.value = true
      startTime = Date.now()

      // 计时器
      durationTimer = setInterval(() => {
        if (startTime) {
          duration.value = Math.round((Date.now() - startTime) / 1000)
        }
      }, 1000)
    } catch (err) {
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
   *
   * 停止后 PCM 数据立即可用（实时采集，无需转换）
   */
  function stopRecording() {
    // 先标记停止（让 ScriptProcessor 停止采集）
    isRecording.value = false

    // 清除计时器
    if (durationTimer) {
      clearInterval(durationTimer)
      durationTimer = null
    }

    // 停止 MediaRecorder（onstop 回调生成试听 URL）
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop()
    }

    // 关闭 AudioContext
    if (audioCtx) {
      audioCtx.close().catch(() => {})
      audioCtx = null
    }

    // 合并所有 PCM 片段为一个 ArrayBuffer
    if (pcmChunks.length > 0) {
      // 计算总长度
      let totalLen = 0
      for (const chunk of pcmChunks) {
        totalLen += chunk.length
      }

      // 合并为一个 Int16Array
      const merged = new Int16Array(totalLen)
      let offset = 0
      for (const chunk of pcmChunks) {
        merged.set(chunk, offset)
        offset += chunk.length
      }

      pcmData.value = merged.buffer
    } else {
      pcmData.value = null
    }

    pcmChunks = []
  }

  /**
   * 取消录音（不保留任何数据）
   */
  function cancelRecording() {
    stopRecording()
    audioBlob.value = null
    audioUrl.value = ''
    pcmData.value = null
    duration.value = 0
  }

  return {
    // 状态
    isRecording,
    audioBlob,
    audioUrl,
    pcmData,
    error,
    duration,
    isProcessing,
    // 方法
    startRecording,
    stopRecording,
    cancelRecording,
  }
}
