<template>
  <div class="public-dialog-page">
    <div class="dialog-container">
      <header class="dialog-header">
        <h1>{{ dialog?.name || '智能对话' }}</h1>
        <p v-if="dialog?.description">{{ dialog.description }}</p>
      </header>

      <div class="chat-area" ref="chatAreaRef">
        <div v-if="!messages.length" class="welcome-area">
          <div class="welcome-icon">🤖</div>
          <h2>{{ dialog?.welcome_message || '您好！有什么可以帮助您的？' }}</h2>
          
          <div v-if="recommendedQuestions.length" class="recommended-questions">
            <p>推荐问题：</p>
            <div class="question-list">
              <button 
                v-for="(q, index) in recommendedQuestions" 
                :key="index"
                class="question-btn"
                @click="sendRecommendedQuestion(q)"
              >
                {{ q }}
              </button>
            </div>
          </div>
        </div>

        <div v-else class="message-list">
          <div 
            v-for="msg in messages" 
            :key="msg.id"
            :class="['message', msg.isUser ? 'user-message' : 'ai-message']"
          >
            <div class="message-avatar">
              <span v-if="msg.isUser">👤</span>
              <span v-else>🤖</span>
            </div>
            <div class="message-content">
              <div class="message-text">{{ msg.content }}</div>
              <div v-if="msg.sources && msg.sources.length" class="message-sources">
                <span class="sources-label">参考：</span>
                <span v-for="(s, i) in msg.sources" :key="i" class="source-item">{{ s }}</span>
              </div>
            </div>
          </div>

          <div v-if="isLoading" class="loading-message">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <textarea
          v-model="userInput"
          class="chat-input"
          placeholder="请输入您的问题..."
          rows="2"
          @keydown.enter.ctrl="sendMessage"
          :disabled="isLoading"
        ></textarea>
        <button 
          class="send-btn" 
          @click="sendMessage"
          :disabled="isLoading || !userInput.trim()"
        >
          <span v-if="!isLoading">发送</span>
          <span v-else class="loading-spinner"></span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

const route = useRoute()

const dialogCode = computed(() => route.params.code as string)
const dialog = ref<any>(null)
const messages = ref<any[]>([])
const userInput = ref('')
const isLoading = ref(false)
const chatAreaRef = ref<HTMLElement>()

const recommendedQuestions = computed(() => {
  return dialog.value?.recommended_questions || []
})

const loadDialog = async () => {
  try {
    const res = await request.get(`/public-dialog/by-code/${dialogCode.value}`)
    dialog.value = res
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '对话加载失败')
  }
}

const loadMessages = async () => {
  // 公开对话不显示历史记录，每次都是全新会话
  messages.value = []
}

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return

  const question = userInput.value.trim()
  userInput.value = ''

  messages.value.push({
    id: Date.now(),
    content: question,
    isUser: true
  })

  isLoading.value = true
  scrollToBottom()

  try {
    const res = await request.post(`/public-dialog/by-code/${dialogCode.value}/chat`, {
      question
    })

    messages.value.push({
      id: res.message_id || 0,
      content: res.answer || '',
      isUser: false,
      sources: res.sources || []
    })
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '发送消息失败')
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

const sendRecommendedQuestion = async (question: string) => {
  userInput.value = question
  await sendMessage()
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatAreaRef.value) {
    chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
  }
}

onMounted(async () => {
  await loadDialog()
  if (dialog.value) {
    await loadMessages()
  }
})
</script>

<style scoped>
.public-dialog-page {
  min-height: 100vh;
  background: #f8f9fb;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.dialog-container {
  width: 100%;
  max-width: 720px;
  height: 88vh;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dialog-header {
  padding: 24px 28px;
  background: #ffffff;
  border-bottom: 1px solid #f0f0f0;
}

.dialog-header h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.dialog-header p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #999999;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #ffffff;
}

.welcome-area {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon {
  font-size: 52px;
  margin-bottom: 16px;
}

.welcome-area h2 {
  color: #333333;
  font-size: 16px;
  font-weight: 400;
  margin-bottom: 24px;
  line-height: 1.6;
}

.recommended-questions {
  margin-top: 32px;
}

.recommended-questions p {
  color: #999999;
  font-size: 12px;
  margin-bottom: 12px;
}

.question-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.question-btn {
  padding: 8px 16px;
  background: #f5f7fa;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  color: #666666;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
}

.question-btn:hover {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #ffffff;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message.user-message {
  flex-direction: row-reverse;
  align-self: flex-end;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.user-message .message-avatar {
  background: #3b82f6;
}

.ai-message .message-avatar {
  background: #f0f0f0;
}

.message-content {
  flex: 1;
  padding: 12px 16px;
  border-radius: 12px;
}

.user-message .message-content {
  background: #3b82f6;
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.ai-message .message-content {
  background: #f8f9fb;
  color: #333333;
  border-bottom-left-radius: 4px;
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
}

.message-sources {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #eeeeee;
  font-size: 12px;
  color: #999999;
}

.sources-label {
  margin-right: 4px;
}

.source-item {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 4px;
  margin-right: 4px;
  font-size: 11px;
}

.loading-message {
  display: flex;
  align-items: center;
  padding: 12px 16px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #cccccc;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

.input-area {
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  gap: 12px;
  align-items: flex-end;
  background: #ffffff;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  resize: none;
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
  background: #fafafa;
  color: #333333;
}

.chat-input::placeholder {
  color: #999999;
}

.chat-input:focus {
  border-color: #3b82f6;
  background: #ffffff;
}

.chat-input:disabled {
  background: #f5f5f5;
}

.send-btn {
  padding: 12px 24px;
  background: #3b82f6;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.send-btn:hover:not(:disabled) {
  background: #2563eb;
}

.send-btn:disabled {
  background: #94c1f8;
  cursor: not-allowed;
}

.loading-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #ffffff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
