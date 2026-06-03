<!--
  Home.vue — 语音日历主页面
  完整流程：录音 → 语音识别 → NLP解析 → 创建日程
-->
<template>
  <div class="home">
    <h1>🎙️ 语音日历</h1>
    <p class="subtitle">说一句话，轻松管理你的日程</p>

    <!-- ═══ 语音输入区域 ═══ -->
    <div class="voice-area">

      <!-- 阶段1: 录音 -->
      <div v-if="phase === 'idle' || phase === 'recording'" class="recorder-box">
        <button
          class="mic-btn"
          :class="{ recording: isRecording }"
          @click="handleMicClick"
        >
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

      <!-- 阶段3: 识别完成，显示文字 -->
      <div v-else-if="phase === 'recognized'" class="result-box">
        <div class="result-label">识别结果：</div>
        <div class="result-text">{{ recognizedText }}</div>
        <div class="result-actions">
          <button class="btn btn-primary" @click="handleParse">🤖 智能解析</button>
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
          <div class="field"><span class="key">🕐 时间</span>{{ formatTime(parsedEvent.event_time) }}</div>
          <div class="field"><span class="key">📂 类型</span>{{ parsedEvent.event_type }}</div>
          <div class="field" v-if="parsedEvent.description">
            <span class="key">📝 备注</span>{{ parsedEvent.description }}
          </div>
        </div>
        <div class="result-actions">
          <button class="btn btn-primary" @click="handleCreate" :disabled="creating">
            {{ creating ? '创建中...' : '✅ 确认创建' }}
          </button>
          <button class="btn btn-outline" @click="retry">🔄 重新录音</button>
        </div>
      </div>

      <!-- 阶段6: 创建成功 -->
      <div v-else-if="phase === 'done'" class="done-box">
        <div class="done-icon">🎉</div>
        <p class="done-text">日程已创建！</p>
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
import { recognizeSpeech, parseText, createEvent } from '../api/index'

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
    // idle → recording → recognizing → recognized → parsing → confirm → done
    const phase = ref('idle')
    const recognizedText = ref('')
    const parsedEvent = ref({})
    const error = ref('')
    const creating = ref(false)

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

    // ---- 步骤1: 点击录音按钮 ----
    async function handleMicClick() {
      if (isRecording.value) {
        // 停止录音 → PCM 数据立即可用（实时采集，无需转换等待）
        stopRecording()
        phase.value = 'recognizing'

        // stopRecording() 同步返回，pcmData 已填充
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
          error.value = e.message || '语音识别失败，请重试'
          phase.value = 'idle'
        }
      } else {
        // 开始录音
        await startRecording()
        if (!isRecording.value) {
          // 权限被拒
          error.value = recorderError.value || '无法启动录音'
          phase.value = 'idle'
        } else {
          phase.value = 'recording'
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
        error.value = e.message || '语义解析失败，请重试'
        phase.value = 'recognized'  // 回到文字确认页
      }
    }

    // ---- 步骤3: 创建事件 ----
    async function handleCreate() {
      creating.value = true
      try {
        await createEvent({
          title: parsedEvent.value.title,
          event_time: parsedEvent.value.event_time,
          event_type: parsedEvent.value.event_type || '其他',
          description: parsedEvent.value.description || '',
          remind: parsedEvent.value.remind !== false,
        })
        phase.value = 'done'
      } catch (e) {
        error.value = e.message || '创建事件失败'
      } finally {
        creating.value = false
      }
    }

    // ---- 重新录音 ----
    function retry() {
      phase.value = 'idle'
      recognizedText.value = ''
      parsedEvent.value = {}
      cancelRecording()
    }

    return {
      // 状态
      isRecording,
      duration,
      phase,
      recognizedText,
      parsedEvent,
      error,
      creating,
      // 格式化
      durationText,
      formatTime,
      // 方法
      handleMicClick,
      handleParse,
      handleCreate,
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
h1 { font-size: 28px; color: #333; }
.subtitle { color: #666; margin-bottom: 30px; }

/* ===== 录音区域 ===== */
.voice-area { margin: 10px 0; }
.recorder-box { display: flex; flex-direction: column; align-items: center; }

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
.mic-btn:hover { background: #4a90d9; color: white; }

.mic-btn.recording {
  border-color: #e74c3c;
  background: #ffe8e6;
  color: #e74c3c;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(231,76,60,0.4); }
  50%      { transform: scale(1.05); box-shadow: 0 0 0 15px rgba(231,76,60,0); }
}
.mic-icon { font-size: 36px; }
.mic-label { font-size: 14px; }

/* 计时器 */
.timer {
  margin-top: 16px;
  font-size: 28px;
  font-weight: bold;
  color: #e74c3c;
  font-family: 'Courier New', monospace;
}
.hint { color: #999; margin-top: 16px; font-size: 14px; }

/* 加载动画 */
.loading-box { padding: 40px; }
.spinner {
  width: 40px;
  height: 40px;
  margin: 0 auto 16px;
  border: 4px solid #e0e0e0;
  border-top-color: #4a90d9;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.processing-text { color: #4a90d9; font-size: 16px; }

/* 识别结果 / 确认 */
.result-box {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 12px;
  padding: 24px;
}
.result-label { font-size: 13px; color: #888; margin-bottom: 8px; text-align: left; }
.result-text {
  font-size: 20px;
  color: #333;
  padding: 16px;
  background: white;
  border-radius: 8px;
  margin-bottom: 20px;
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
.field:last-child { border-bottom: none; }
.key { display: inline-block; width: 70px; color: #888; font-size: 14px; }

/* 按钮 */
.result-actions { display: flex; gap: 12px; justify-content: center; }
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
.btn:hover { opacity: 0.85; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-primary { background: #4a90d9; color: white; }
.btn-outline { background: white; color: #4a90d9; border: 1px solid #4a90d9; }

/* 创建成功 */
.done-box {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 12px;
  padding: 32px;
}
.done-icon { font-size: 48px; }
.done-text { font-size: 18px; color: #16a34a; margin: 12px 0 20px; }

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
.close-btn { background: none; border: none; font-size: 20px; cursor: pointer; color: #dc2626; }

/* 快捷入口 */
.quick-links { display: flex; gap: 16px; justify-content: center; margin-top: 40px; }
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
.card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
</style>
