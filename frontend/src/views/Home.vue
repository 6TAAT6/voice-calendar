<!--
  Home.vue — 首页（语音录入核心页面）

  状态机：
  idle    → 初始状态，显示录音按钮
  recording → 正在录音，红色脉冲按钮 + 计时
  processing → 正在调用讯飞识别
  result  → 显示识别结果
  error   → 显示错误信息
-->
<template>
  <div class="home">
    <h1>🎙️ 语音日历</h1>
    <p class="subtitle">说一句话，轻松管理你的日程</p>

    <!-- ═══ 语音输入区域 ═══ -->
    <div class="voice-area">

      <!-- 状态1: 初始态 / 录音中 -->
      <div v-if="phase !== 'result'" class="recorder-box">
        <button
          class="mic-btn"
          :class="{ recording: isRecording }"
          :disabled="isProcessing"
          @click="handleMicClick"
        >
          <span class="mic-icon">{{ micIcon }}</span>
          <span class="mic-label">{{ micLabel }}</span>
        </button>

        <!-- 录音计时 -->
        <p v-if="isRecording" class="timer">{{ durationText }}</p>
        <p v-else-if="isProcessing" class="processing-text">正在识别中...</p>
        <p v-else class="hint">点击按钮开始录音，例如说："明天下午三点开会"</p>
      </div>

      <!-- 状态2: 识别完成 — 显示结果 -->
      <div v-else class="result-box">
        <div class="result-text">{{ recognizedText || '(未识别到内容)' }}</div>

        <div class="result-actions">
          <button class="btn btn-primary" @click="createEventFromText">
            ✅ 创建日程
          </button>
          <button class="btn btn-outline" @click="retry">
            🔄 重新录音
          </button>
        </div>
        <p class="hint">确认无误后点击"创建日程"，将自动解析时间</p>
      </div>

      <!-- 错误弹窗 -->
      <div v-if="error" class="error-toast">
        ⚠️ {{ error }}
        <button @click="error = ''" class="close-btn">×</button>
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
import { recognizeSpeech } from '../api/index'

export default {
  name: 'Home',
  setup() {
    // ---- 录音模块 ----
    const {
      isRecording,
      audioBlob,
      audioUrl,
      error,
      duration,
      isProcessing,
      startRecording,
      stopRecording,
      cancelRecording,
    } = useAudioRecorder()

    // ---- 额外状态 ----
    const phase = ref('idle')        // idle | recording | processing | result
    const recognizedText = ref('')

    // ---- 麦克风按钮图标/文字 ----
    const micIcon = computed(() => {
      if (isProcessing.value) return '⏳'
      if (isRecording.value) return '⏹️'
      return '🎤'
    })
    const micLabel = computed(() => {
      if (isProcessing.value) return '识别中...'
      if (isRecording.value) return '点击停止'
      return '点击录音'
    })

    // ---- 录音时长格式化 ----
    const durationText = computed(() => {
      const s = duration.value
      return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`
    })

    // ---- 点击录音按钮 ----
    async function handleMicClick() {
      if (isProcessing.value) return   // 识别中，不响应

      if (isRecording.value) {
        // 停止录音 → 发送识别
        stopRecording()
        phase.value = 'processing'
        isProcessing.value = true

        // 等一小段让 audioBlob 填充完成
        await new Promise((r) => setTimeout(r, 300))

        try {
          const result = await recognizeSpeech(audioBlob.value)
          recognizedText.value = result.text
          phase.value = 'result'
        } catch (e) {
          error.value = e.message || '语音识别失败，请重试'
          phase.value = 'idle'
        } finally {
          isProcessing.value = false
        }
      } else {
        // 开始录音
        phase.value = 'recording'
        await startRecording()
        // 如果 startRecording 出错（如拒绝权限），phase 回到 idle
        if (!isRecording.value) {
          phase.value = 'idle'
        }
      }
    }

    // ---- 从识别结果创建日程 ----
    function createEventFromText() {
      // 跳转到日历页面，并把识别文字通过路由传过去
      // PR5 会用 DeepSeek 解析这段文字
      alert('已获取文字：' + recognizedText.value + '\n\n解析功能将在 PR5 实现，敬请期待！')
    }

    // ---- 重新录音 ----
    function retry() {
      phase.value = 'idle'
      recognizedText.value = ''
      cancelRecording()
    }

    return {
      isRecording,
      error,
      duration,
      phase,
      recognizedText,
      isProcessing,
      micIcon,
      micLabel,
      durationText,
      handleMicClick,
      createEventFromText,
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
.subtitle { color: #666; margin-bottom: 40px; }

/* ===== 录音区域 ===== */
.voice-area { margin: 20px 0; }

.recorder-box {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* ===== 录音按钮（大圆） ===== */
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

.mic-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

/* 录音中状态 */
.mic-btn.recording {
  border-color: #e74c3c;
  background: #ffe8e6;
  color: #e74c3c;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.4); }
  50%      { transform: scale(1.05); box-shadow: 0 0 0 15px rgba(231, 76, 60, 0); }
}

.mic-icon { font-size: 36px; }
.mic-label { font-size: 14px; }

/* ===== 计时器 ===== */
.timer {
  margin-top: 16px;
  font-size: 28px;
  font-weight: bold;
  color: #e74c3c;
  font-family: 'Courier New', monospace;
}

.processing-text {
  margin-top: 16px;
  font-size: 16px;
  color: #4a90d9;
  animation: blink 0.8s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.3; }
}

.hint {
  color: #999;
  margin-top: 16px;
  font-size: 14px;
}

/* ===== 识别结果 ===== */
.result-box {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 12px;
  padding: 24px;
}

.result-text {
  font-size: 20px;
  color: #333;
  padding: 16px;
  background: white;
  border-radius: 8px;
  margin-bottom: 20px;
  min-height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn {
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  border: none;
  transition: opacity 0.2s;
}

.btn:hover { opacity: 0.85; }

.btn-primary {
  background: #4a90d9;
  color: white;
}

.btn-outline {
  background: white;
  color: #4a90d9;
  border: 1px solid #4a90d9;
}

/* ===== 错误提示 ===== */
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

/* ===== 快捷入口 ===== */
.quick-links {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 50px;
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
