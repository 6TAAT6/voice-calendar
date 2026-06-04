<!--
  Home.vue — 语音日历主页面
  完整流程：录音 → 语音识别 → NLP解析 → TTS语音反馈 → 创建日程
  PR8 新增：AI 对话修正 + 冲突检测 + 语音播报
-->
<template>
  <div class="home">
    <h1>🎙️ 语音日历</h1>
    <p class="subtitle">说一句话，轻松管理你的日程</p>

    <!-- ═══ 语音输入区域 ═══ -->
    <div class="voice-area">
      <!-- 阶段1: 录音 -->
      <div v-if="phase === 'idle' || phase === 'recording'" class="recorder-box">
        <button class="mic-btn" :class="{ recording: isRecording }" @click="handleMicClick">
          <span class="mic-icon">{{ isRecording ? '⏹️' : '🎤' }}</span>
          <span class="mic-label">{{ isRecording ? '点击停止' : '点击录音' }}</span>
        </button>

        <p v-if="isRecording" class="timer">{{ durationText }}</p>
        <p v-else class="hint">说出你的日程，例如："明天下午三点开产品评审会"</p>
      </div>

      <!-- 阶段2: 识别中 -->
      <div v-else-if="phase === 'recognizing'" class="loading-box">
        <div class="spinner"></div>
        <p class="processing-text">正在识别语音...</p>
      </div>

      <!-- 阶段3: 识别完成，显示文字 + 修正入口 -->
      <div v-else-if="phase === 'recognized' || phase === 'correcting'" class="result-box">
        <div class="result-label">识别结果：</div>
        <div class="result-text">{{ recognizedText }}</div>

        <!-- AI 对话修正：说"不对，改成xxx" -->
        <div v-if="phase === 'correcting'" class="correct-box">
          <p class="correct-hint">🔧 请说出修正指令，例如："改成后天上午十点"</p>
          <div class="correct-actions">
            <button
              class="btn btn-sm"
              :class="{ recording: isRecording }"
              @click="handleCorrectMic"
            >
              {{ isRecording ? '⏹️ 停止修正' : '🎤 说出修正' }}
            </button>
            <button class="btn btn-sm btn-outline" @click="phase = 'recognized'">取消修正</button>
          </div>
          <p v-if="phase === 'recognizing'" class="processing-text">AI 正在理解修正...</p>
        </div>

        <div v-else class="result-actions">
          <button class="btn btn-primary" @click="handleParse">🤖 智能解析</button>
          <button class="btn btn-outline" @click="startCorrection">✏️ 语音修正</button>
          <button class="btn btn-outline" @click="retry">🔄 重新录音</button>
        </div>
      </div>

      <!-- 阶段4: 解析中 -->
      <div v-else-if="phase === 'parsing'" class="loading-box">
        <div class="spinner"></div>
        <p class="processing-text">🤖 DeepSeek 正在理解你的日程...</p>
      </div>

      <!-- 阶段5: 解析完成，确认创建 -->
      <div v-else-if="phase === 'confirm'" class="result-box">
        <div class="result-label">日程确认：</div>
        <div class="parsed-detail">
          <div class="field"><span class="key">📌 标题</span>{{ parsedEvent.title }}</div>
          <div class="field">
            <span class="key">🕐 时间</span>{{ formatTime(parsedEvent.event_time) }}
          </div>
          <div class="field"><span class="key">📂 类型</span>{{ parsedEvent.event_type }}</div>
          <div v-if="parsedEvent.description" class="field">
            <span class="key">📝 备注</span>{{ parsedEvent.description }}
          </div>
        </div>

        <!-- 冲突警告 -->
        <div v-if="conflictWarnings.length > 0" class="conflict-warning">
          <div v-for="(w, i) in conflictWarnings" :key="i" class="warning-item">
            {{ w.message }}
          </div>
          <div class="conflict-actions">
            <button class="btn btn-primary" @click="handleCreate(true)">仍要创建</button>
            <button class="btn btn-outline" @click="retry">取消</button>
          </div>
        </div>

        <div v-else class="result-actions">
          <button class="btn btn-primary" :disabled="creating" @click="handleCreate(false)">
            {{ creating ? '创建中...' : '✅ 确认创建' }}
          </button>
          <button class="btn btn-outline" @click="retry">🔄 重新录音</button>
        </div>
      </div>

      <!-- 阶段6: 创建成功 + 语音反馈 -->
      <div v-else-if="phase === 'done'" class="done-box">
        <div class="done-icon">🎉</div>
        <p class="done-text">日程已创建！</p>
        <p v-if="ttsPlaying" class="tts-status">🔊 正在语音播报...</p>
        <div class="result-actions">
          <router-link to="/calendar" class="btn btn-primary">📅 查看日程</router-link>
          <button class="btn btn-outline" @click="retry">➕ 继续添加</button>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="error-toast">
        ⚠️ {{ error }}
        <button class="close-btn" @click="error = ''">×</button>
      </div>
    </div>

    <!-- ═══ 快捷入口 ═══ -->
    <div class="quick-links">
      <router-link to="/calendar" class="card">📅 查看日程</router-link>
      <router-link to="/settings" class="card">⚙️ 设置</router-link>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useAudioRecorder } from '../composables/useAudioRecorder'
import {
  recognizeSpeech,
  parseText,
  correctSchedule,
  synthesizeSpeech,
  createEvent,
} from '../api/index'

export default {
  name: 'Home',
  setup() {
    // ---- 录音模块 ----
    const {
      isRecording,
      pcmData,
      error: recorderError,
      duration,
      startRecording,
      stopRecording,
      cancelRecording,
    } = useAudioRecorder()

    // ---- 状态管理 ----
    const phase = ref('idle')
    const recognizedText = ref('')
    const parsedEvent = ref({})
    const conflictWarnings = ref([])
    const error = ref('')
    const creating = ref(false)
    const ttsPlaying = ref(false)

    // ---- 计时器格式化 ----
    const durationText = computed(() => {
      const s = duration.value
      return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
    })

    // ---- 格式化时间显示 ----
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

    // ---- 错误翻译 ----
    function translateError(err) {
      const msg = err.message || String(err)
      if (msg.includes('timeout')) return '网络超时，请确认后端已启动后重试'
      if (msg.includes('illegal access') || msg.includes('Unauthorized') || msg.includes('401'))
        return '讯飞授权失败，请检查密钥配置'
      if (msg.includes('Websocket closed')) return '语音服务器连接中断，请重试'
      if (msg.includes('Failed to fetch') || msg.includes('NetworkError'))
        return '无法连接服务器，请确认后端已启动'
      if (msg.includes('DeepSeek')) return 'AI 解析失败，请再说一遍或换个说法'
      if (msg.includes('讯飞')) return msg
      return msg || '操作失败，请重试'
    }

    /**
     * 播放语音反馈
     */
    async function playVoiceFeedback(text) {
      try {
        ttsPlaying.value = true
        const audioBlob = await synthesizeSpeech(text)
        const audioUrl = URL.createObjectURL(audioBlob)
        const audio = new Audio(audioUrl)
        audio.onended = () => {
          ttsPlaying.value = false
          URL.revokeObjectURL(audioUrl)
        }
        audio.onerror = () => {
          ttsPlaying.value = false
          URL.revokeObjectURL(audioUrl)
        }
        await audio.play()
      } catch (e) {
        ttsPlaying.value = false
        console.warn('语音播报失败（不影响功能）:', e.message)
      }
    }

    // ---- 步骤1: 录音 → 识别 ----
    async function handleMicClick() {
      if (isRecording.value) {
        stopRecording()
        phase.value = 'recognizing'

        if (!pcmData.value) {
          error.value = recorderError.value || '录音数据为空，请重新录制'
          phase.value = 'idle'
          return
        }

        try {
          const result = await recognizeSpeech(pcmData.value)
          recognizedText.value = result.text
          phase.value = 'recognized'
        } catch (e) {
          error.value = translateError(e)
          phase.value = 'idle'
        }
      } else {
        await startRecording()
        if (!isRecording.value) {
          error.value = recorderError.value || '无法启动录音'
          phase.value = 'idle'
        } else {
          phase.value = 'recording'
        }
      }
    }

    // ---- AI 对话修正 ----
    function startCorrection() {
      phase.value = 'correcting'
    }

    async function handleCorrectMic() {
      if (isRecording.value) {
        stopRecording()
        const prev = phase.value
        phase.value = 'recognizing'

        if (!pcmData.value) {
          error.value = recorderError.value || '修正录音为空，请重试'
          phase.value = prev
          return
        }

        try {
          const result = await recognizeSpeech(pcmData.value)
          const correction = result.text
          if (!correction) {
            error.value = '未识别到修正内容，请重说'
            phase.value = prev
            return
          }
          // 调用 AI 修正
          const corrected = await correctSchedule(recognizedText.value, correction)
          parsedEvent.value = corrected
          recognizedText.value = correction
          phase.value = 'confirm'
        } catch (e) {
          error.value = translateError(e)
          phase.value = 'correcting'
        }
      } else {
        await startRecording()
        if (!isRecording.value) {
          error.value = recorderError.value || '无法启动录音'
          phase.value = 'correcting'
        }
      }
    }

    // ---- 步骤2: NLP 解析 ----
    async function handleParse() {
      phase.value = 'parsing'
      try {
        const result = await parseText(recognizedText.value)
        parsedEvent.value = result
        phase.value = 'confirm'
      } catch (e) {
        error.value = translateError(e)
        phase.value = 'recognized'
      }
    }

    // ---- 步骤3: 创建事件 ----
    async function handleCreate(forceCreate) {
      creating.value = true
      try {
        const result = await createEvent(
          {
            title: parsedEvent.value.title,
            event_time: parsedEvent.value.event_time,
            event_type: parsedEvent.value.event_type || '其他',
            description: parsedEvent.value.description || '',
            remind: parsedEvent.value.remind !== false,
          },
          forceCreate,
        )

        // 检查冲突
        if (!result.success && result.should_confirm) {
          conflictWarnings.value = result.warnings || []
          creating.value = false
          return
        }

        conflictWarnings.value = []
        phase.value = 'done'

        // 语音反馈：播报创建结果
        const dt = new Date(parsedEvent.value.event_time)
        const timeStr = `${dt.getMonth() + 1}月${dt.getDate()}日 ${String(dt.getHours()).padStart(2, '0')}点${String(dt.getMinutes()).padStart(2, '0')}分`
        const feedback = `已为您创建${timeStr}的${parsedEvent.value.title}`
        playVoiceFeedback(feedback)
      } catch (e) {
        error.value = translateError(e)
      } finally {
        creating.value = false
      }
    }

    // ---- 重新录音 ----
    function retry() {
      phase.value = 'idle'
      recognizedText.value = ''
      parsedEvent.value = {}
      conflictWarnings.value = []
      cancelRecording()
    }

    return {
      isRecording,
      duration,
      phase,
      recognizedText,
      parsedEvent,
      conflictWarnings,
      error,
      creating,
      ttsPlaying,
      durationText,
      formatTime,
      handleMicClick,
      handleParse,
      handleCreate,
      handleCorrectMic,
      startCorrection,
      retry,
    }
  },
}
</script>

<style scoped>
/* ===== 布局 ===== */
.home {
  max-width: 600px;
  margin: 0 auto;
  padding: 40px 20px;
  text-align: center;
}
h1 {
  font-size: 28px;
  color: #333;
}
.subtitle {
  color: #666;
  margin-bottom: 30px;
}

/* ===== 录音区域 ===== */
.voice-area {
  margin: 10px 0;
}
.recorder-box {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* ===== 录音按钮 ===== */
.mic-btn {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  border: 4px solid #4a90d9;
  background: #e8f0fe;
  cursor: pointer;
  color: #4a90d9;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s;
  user-select: none;
}
.mic-btn:hover {
  background: #4a90d9;
  color: white;
}
.mic-btn.recording {
  border-color: #e74c3c;
  background: #ffe8e6;
  color: #e74c3c;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.4);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 15px rgba(231, 76, 60, 0);
  }
}
.mic-icon {
  font-size: 36px;
}
.mic-label {
  font-size: 14px;
}

/* 计时器 */
.timer {
  margin-top: 16px;
  font-size: 28px;
  font-weight: bold;
  color: #e74c3c;
  font-family: 'Courier New', monospace;
}
.hint {
  color: #999;
  margin-top: 16px;
  font-size: 14px;
}

/* 加载动画 */
.loading-box {
  padding: 40px;
}
.spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 16px;
  border: 4px solid #e0e0e0;
  border-top-color: #4a90d9;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.processing-text {
  color: #4a90d9;
  font-size: 16px;
}

/* 识别结果 / 确认 */
.result-box {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 12px;
  padding: 24px;
}
.result-label {
  font-size: 13px;
  color: #888;
  margin-bottom: 8px;
  text-align: left;
}
.result-text {
  font-size: 20px;
  color: #333;
  padding: 16px;
  background: white;
  border-radius: 8px;
  margin-bottom: 20px;
}

/* AI 修正区域 */
.correct-box {
  margin-bottom: 16px;
  padding: 12px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
}
.correct-hint {
  color: #92400e;
  font-size: 14px;
  margin-bottom: 10px;
}
.correct-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* 解析详情 */
.parsed-detail {
  text-align: left;
  background: white;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}
.field {
  padding: 6px 0;
  font-size: 15px;
  color: #333;
  border-bottom: 1px solid #f0f0f0;
}
.field:last-child {
  border-bottom: none;
}
.key {
  display: inline-block;
  width: 70px;
  color: #888;
  font-size: 14px;
}

/* 冲突警告 */
.conflict-warning {
  margin-bottom: 16px;
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}
.warning-item {
  color: #dc2626;
  font-size: 14px;
  padding: 4px 0;
}
.conflict-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 10px;
}

/* 按钮 */
.result-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}
.btn {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  border: none;
  transition: opacity 0.2s;
  text-decoration: none;
  display: inline-block;
}
.btn:hover {
  opacity: 0.85;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-sm {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  background: #f0f0f0;
  border: 1px solid #ccc;
  color: #333;
}
.btn-sm.recording {
  background: #ffe8e6;
  border-color: #e74c3c;
  color: #e74c3c;
}
.btn-primary {
  background: #4a90d9;
  color: white;
}
.btn-outline {
  background: white;
  color: #4a90d9;
  border: 1px solid #4a90d9;
}

/* 创建成功 */
.done-box {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  padding: 32px;
}
.done-icon {
  font-size: 48px;
}
.done-text {
  font-size: 18px;
  color: #16a34a;
  margin: 12px 0 20px;
}
.tts-status {
  color: #4a90d9;
  font-size: 14px;
}

/* 错误 */
.error-toast {
  margin-top: 16px;
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #dc2626;
}

/* 快捷入口 */
.quick-links {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 40px;
}
.card {
  padding: 20px 30px;
  background: #f8f9fa;
  border-radius: 12px;
  text-decoration: none;
  color: #333;
  font-size: 16px;
  border: 1px solid #e0e0e0;
  transition: transform 0.2s;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>
