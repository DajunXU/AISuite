<template>
  <div class="chat">
    <div class="layout-container">
      <!-- 侧边栏 -->
      <Sidebar />
      
      <!-- 主内容区 -->
      <div class="main-container">
        <!-- 左侧对话列表 -->
        <aside class="conversation-sidebar">
          <div class="sidebar-header">
            <h2>智能对话</h2>
            <button class="new-chat-btn" @click="createNewConversation">
              <span class="plus-icon">+</span>
              新建对话
            </button>
          </div>
          
          <div class="search-box">
            <input 
              type="text" 
              v-model="searchKeyword" 
              placeholder="搜索对话..."
              class="search-input"
            />
          </div>
          
          <div class="conversation-list">
            <div class="conversation-group">
              <div class="group-title" @click="toggleGroup('favorites')">
                <span class="group-icon">📌</span>
                收藏的对话
                <span class="expand-icon" :class="{ expanded: expandedGroups.favorites }">▼</span>
              </div>
              <div class="group-items" v-show="expandedGroups.favorites">
                <div 
                  v-for="conv in filteredFavoriteConversations" 
                  :key="conv.id"
                  :class="['conversation-item', { active: currentConversation?.id === conv.id }]"
                  @click="selectConversation(conv)"
                >
                  <span class="conv-icon">⭐</span>
                  <span class="conv-title">{{ conv.title }}</span>
                  <div class="conv-actions">
                    <button class="action-btn" @click.stop="toggleFavorite(conv)" title="取消收藏">
                      ⭐
                    </button>
                    <button class="action-btn delete" @click.stop="deleteConversation(conv)" title="删除">
                      🗑️
                    </button>
                  </div>
                </div>
                <div v-if="filteredFavoriteConversations.length === 0" class="empty-tip">
                  暂无收藏对话
                </div>
              </div>
            </div>
            
            <div class="conversation-group">
              <div class="group-title" @click="toggleGroup('all')">
                <span class="group-icon">📁</span>
                所有对话
                <span class="expand-icon" :class="{ expanded: expandedGroups.all }">▼</span>
              </div>
              <div class="group-items" v-show="expandedGroups.all">
                <div 
                  v-for="conv in filteredConversations" 
                  :key="conv.id"
                  :class="['conversation-item', { active: currentConversation?.id === conv.id }]"
                  @click="selectConversation(conv)"
                >
                  <span class="conv-icon">💬</span>
                  <span class="conv-title">{{ conv.title }}</span>
                  <div class="conv-actions">
                    <button class="action-btn" @click.stop="toggleFavorite(conv)" title="收藏">
                      ☆
                    </button>
                    <button class="action-btn delete" @click.stop="deleteConversation(conv)" title="删除">
                      🗑️
                    </button>
                  </div>
                </div>
                <div v-if="filteredConversations.length === 0" class="empty-tip">
                  暂无对话
                </div>
              </div>
            </div>
          </div>
        </aside>
        
        <!-- 右侧对话区域 -->
        <main class="chat-main">
          <header class="chat-header">
            <div class="header-left">
              <h3 v-if="currentConversation">{{ currentConversation.title }}</h3>
              <h3 v-else>智能对话</h3>
            </div>
            <div class="header-right">
              <div class="knowledge-base-selector">
                <div class="kb-selector-group">
                  <span class="kb-type-label">
                    <span class="kb-icon">📄</span>
                    文本
                  </span>
                  <select v-model="selectedTextKnowledgeBase" @change="onTextKbChange" class="custom-select" :class="{ active: selectedTextKnowledgeBase }">
                    <option value="">选择文本知识库</option>
                    <option
                      v-for="kb in textKnowledgeBases"
                      :key="kb.id"
                      :value="kb.id"
                    >{{ kb.name }}</option>
                  </select>
                </div>
                <span class="kb-divider">或</span>
                <div class="kb-selector-group">
                  <span class="kb-type-label">
                    <span class="kb-icon">🗄️</span>
                    数据库
                  </span>
                  <select v-model="selectedDbKnowledgeBase" @change="onDbKbChange" class="custom-select" :class="{ active: selectedDbKnowledgeBase }">
                    <option value="">选择数据库知识库</option>
                    <option
                      v-for="kb in dbKnowledgeBases"
                      :key="kb.id"
                      :value="kb.id"
                    >{{ kb.name }}</option>
                  </select>
                </div>
                <div v-if="selectedTextKnowledgeBase || selectedDbKnowledgeBase" class="selected-kb-info">
                  <span class="mode-badge" :class="selectedTextKnowledgeBase ? 'text-mode' : 'db-mode'">
                    {{ selectedTextKnowledgeBase ? '📄 文本检索模式' : '🗄️ 数据库查询模式' }}
                  </span>
                </div>
              </div>
              
              <div class="user-dropdown">
                <div class="user-info">
                  <div class="user-avatar">{{ userStore.user?.username?.charAt(0) }}</div>
                  <span class="user-name">{{ userStore.user?.username }}</span>
                  <span class="dropdown-arrow">▼</span>
                </div>
                <div class="dropdown-menu">
                  <button class="dropdown-item" @click="logout">退出登录</button>
                </div>
              </div>
            </div>
          </header>
          
          <div class="chat-container">
            <!-- 聊天历史 -->
            <div class="chat-history" ref="chatHistoryRef">
              <div v-if="!currentConversation" class="welcome-tip">
                <div class="welcome-icon">🤖</div>
                <h3>欢迎使用智能对话</h3>
                <p>选择一个对话或创建新对话开始聊天</p>
                <button class="start-btn" @click="createNewConversation">
                  开始新对话
                </button>
              </div>
              
              <template v-else>
                <div
                  v-for="message in chatHistory"
                  :key="message.id"
                  :class="['message', message.is_user ? 'user-message' : 'ai-message']"
                >
                  <div class="message-avatar">
                    <span v-if="message.is_user">👤</span>
                    <span v-else>🤖</span>
                  </div>
                  <div class="message-content">
                    <div class="message-text">{{ message.content }}</div>
                    <div class="message-meta">
                      <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                      <span v-if="message.duration" class="duration-tag">{{ message.duration }}ms</span>
                      <span v-if="message.answer_source === 1" class="cache-tag exact">精确匹配</span>
                      <span v-if="message.answer_source === 2" class="cache-tag similar">相似匹配</span>
                      <span v-if="message.model_name" class="model-tag">{{ message.model_name }}</span>
                    </div>
                    <div v-if="!message.is_user" class="message-actions">
                      <button 
                        class="feedback-btn" 
                        :class="{ active: message.user_feedback === 1 }"
                        @click="submitFeedback(message.id, 1)"
                        title="赞"
                      >👍</button>
                      <button 
                        class="feedback-btn" 
                        :class="{ active: message.user_feedback === 0 }"
                        @click="submitFeedback(message.id, 0)"
                        title="踩"
                      >👎</button>
                    </div>
                  </div>
                </div>
                
                <!-- 加载状态 -->
                <div v-if="isLoading" class="loading-message">
                  <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </template>
            </div>

            <!-- 输入区域 -->
            <div class="chat-input-area">
              <div class="input-wrapper">
                <textarea
                  v-model="userInput"
                  class="chat-textarea"
                  placeholder="请输入您的问题..."
                  rows="3"
                  @keydown="handleKeydown"
                  :disabled="!currentConversation"
                ></textarea>
                
                <!-- 输入框内工具栏 -->
                <div class="input-inner-toolbar">
                  <div class="toolbar-left">
                    <!-- 模型选择器 -->
                    <div class="model-dropdown" ref="modelDropdownRef">
                      <button class="toolbar-btn model-btn" @click="toggleModelDropdown" :disabled="!currentConversation">
                        <span class="model-icon">◇</span>
                        <span class="model-name">{{ currentModelName }}</span>
                        <span class="dropdown-arrow">▼</span>
                      </button>
                      <div class="model-dropdown-menu" v-if="showModelDropdown">
                        <div 
                          v-for="model in activeModels" 
                          :key="(model as any).id"
                          class="model-dropdown-item"
                          :class="{ active: (model as any).id === selectedModelId }"
                          @click="selectModel((model as any).id)"
                        >
                          {{ (model as any).name }}
                          <span class="check-icon" v-if="(model as any).id === selectedModelId">✓</span>
                        </div>
                      </div>
                    </div>
                    <!-- 预留：附件按钮 -->
                    <button class="toolbar-btn future-btn" title="附件 (即将上线)">
                      <span class="attach-icon">📎</span>
                    </button>
                  </div>
                  <div class="toolbar-right">
                    <!-- 预留：Agent设置 -->
                    <button class="toolbar-btn future-btn" title="Agent设置 (即将上线)">
                      <span class="agent-icon">⚙</span>
                    </button>
                  </div>
                </div>
                
                <button
                  class="send-button"
                  :disabled="isLoading || !userInput.trim() || !currentConversation"
                  @click="sendMessage"
                >
                  <span v-if="!isLoading">发送</span>
                  <span v-else class="loading-spinner"></span>
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '../stores/chat'
import { useKnowledgeStore } from '../stores/knowledge'
import { useUserStore } from '../stores/user'
import { useLLMStore } from '../stores/llm'
import { ElMessage, ElMessageBox } from 'element-plus'
import Sidebar from '@/components/Sidebar.vue'
import request from '@/utils/request'

const chatStore = useChatStore()
const knowledgeStore = useKnowledgeStore()
const userStore = useUserStore()
const llmStore = useLLMStore()
const router = useRouter()

// 对话列表相关
const conversations = ref<any[]>([])
const currentConversation = ref<any>(null)
const searchKeyword = ref('')
const expandedGroups = ref({
  favorites: true,
  all: true
})

// 聊天相关
const userInput = ref('')
const selectedTextKnowledgeBase = ref('')
const selectedDbKnowledgeBase = ref('')
const selectedModelId = ref('')
const knowledgeBases = ref<any[]>([])
const textKnowledgeBases = ref<any[]>([])
const dbKnowledgeBases = ref<any[]>([])
const chatHistory = ref<any[]>([])
const activeModels = ref<any[]>([])
const isLoading = ref(false)
const chatHistoryRef = ref<HTMLElement | null>(null)

// 模型下拉相关
const showModelDropdown = ref(false)
const modelDropdownRef = ref<HTMLElement | null>(null)

// 计算属性
const currentModelName = computed(() => {
  if (!selectedModelId.value) return '选择模型'
  const model = activeModels.value.find(m => (m as any).id === selectedModelId.value)
  return model ? (model as any).name : '选择模型'
})
const favoriteConversations = computed(() => 
  conversations.value.filter(c => c.is_favorite)
)

const filteredConversations = computed(() => {
  if (!searchKeyword.value) return conversations.value
  return conversations.value.filter(c => 
    c.title.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

const filteredFavoriteConversations = computed(() => {
  if (!searchKeyword.value) return favoriteConversations.value
  return favoriteConversations.value.filter(c => 
    c.title.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

// 生命周期
onMounted(() => {
  loadKnowledgeBases()
  loadActiveModels()
  loadConversations()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 对话管理方法
const loadConversations = async () => {
  try {
    const response = await request.get('/chat/conversations')
    const responseData = response?.data || response
    conversations.value = responseData?.conversations || responseData?.data?.conversations || []
    
    if (conversations.value.length > 0) {
      selectConversation(conversations.value[0])
    }
  } catch (error) {
    console.error('加载对话列表失败:', error)
  }
}

const createNewConversation = async () => {
  try {
    const response = await request.post('/chat/conversations', { title: '新对话' })
    const newConv = response
    conversations.value.unshift(newConv)
    selectConversation(newConv)
    ElMessage.success('新对话已创建')
  } catch (error) {
    console.error('创建对话失败:', error)
    ElMessage.error('创建对话失败')
  }
}

const selectConversation = async (conv: any) => {
  currentConversation.value = conv
  await loadConversationMessages(conv.id)
}

const toggleGroup = (group: string) => {
  expandedGroups.value[group as keyof typeof expandedGroups.value] = !expandedGroups.value[group as keyof typeof expandedGroups.value]
}

const loadConversationMessages = async (conversationId: number) => {
  try {
    const response = await request.get(`/chat/conversations/${conversationId}/messages`)
    
    const messages = response || []
    
    const allMessages = [] as {id: string | number, content: string, is_user: boolean, timestamp: Date, is_ai?: boolean, message_id?: string, conversation_message_id?: number, duration?: number, answer_source?: number, user_feedback?: number, model_name?: string}[]
    ;(messages).forEach((msg: any) => {
      allMessages.push({
        id: msg.id + '_user',
        content: msg.question_text,
        is_user: true,
        timestamp: new Date(msg.created_time),
        is_ai: false
      })
      allMessages.push({
        id: msg.id,
        content: msg.answer_text,
        is_user: false,
        timestamp: new Date(msg.created_time),
        is_ai: true,
        message_id: msg.message_id,
        conversation_message_id: msg.id,
        duration: msg.total_duration,
        answer_source: msg.answer_source,
        user_feedback: msg.user_feedback,
        model_name: msg.model_name
      })
    })
    allMessages.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())
    chatHistory.value = allMessages
    
    await nextTick()
    scrollToBottom()
  } catch (error) {
    console.error('加载对话消息失败:', error)
  }
}

const toggleFavorite = async (conv: any) => {
  try {
    await request.put(`/chat/conversations/${conv.id}`, { is_favorite: !conv.is_favorite })
    conv.is_favorite = !conv.is_favorite
    ElMessage.success(conv.is_favorite ? '已收藏' : '已取消收藏')
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

const deleteConversation = async (conv: any) => {
  try {
    await ElMessageBox.confirm('确定要删除这个对话吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await request.delete(`/chat/conversations/${conv.id}`)
    
    const index = conversations.value.findIndex(c => c.id === conv.id)
    if (index > -1) {
      conversations.value.splice(index, 1)
    }
    
    if (currentConversation.value?.id === conv.id) {
      currentConversation.value = null
      chatHistory.value = []
      if (conversations.value.length > 0) {
        selectConversation(conversations.value[0])
      }
    }
    
    ElMessage.success('对话已删除')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除对话失败:', error)
      ElMessage.error('删除对话失败')
    }
  }
}

// 知识库和模型方法
const loadKnowledgeBases = async () => {
  try {
    const allKbs = await knowledgeStore.getAccessibleKnowledgeBases()
    knowledgeBases.value = (allKbs as unknown) as any[]
    textKnowledgeBases.value = ((allKbs as unknown) as any[]).filter((kb: any) => kb.kb_type === 'text' || kb.kb_type === 'file' || !kb.kb_type)
    dbKnowledgeBases.value = ((allKbs as unknown) as any[]).filter((kb: any) => kb.kb_type === 'db')
  } catch (error) {
    console.error('加载知识库失败', error)
  }
}

const loadActiveModels = async () => {
  try {
    const models = await llmStore.fetchActiveModels()
    activeModels.value = Array.isArray(models) ? (models as any[]) : []

    const defaultModel = activeModels.value.find(model => (model as any).is_default)
    if (defaultModel) {
      selectedModelId.value = (defaultModel as any).id
    }
  } catch (error) {
    console.error('加载大模型失败', error)
  }
}

const onModelChange = () => {
}

const toggleModelDropdown = () => {
  if (!currentConversation.value) return
  showModelDropdown.value = !showModelDropdown.value
}

const selectModel = (modelId: number) => {
  selectedModelId.value = modelId
  showModelDropdown.value = false
  onModelChange()
}

// 点击外部关闭下拉菜单
const handleClickOutside = (event: MouseEvent) => {
  if (modelDropdownRef.value && !modelDropdownRef.value.contains(event.target as Node)) {
    showModelDropdown.value = false
  }
}

const onTextKbChange = () => {
  if (selectedTextKnowledgeBase.value) {
    selectedDbKnowledgeBase.value = ''
  }
}

const onDbKbChange = () => {
  if (selectedDbKnowledgeBase.value) {
    selectedTextKnowledgeBase.value = ''
  }
}

// 提交反馈
const submitFeedback = async (messageId: string | number, feedback: number) => {
  try {
    const message = chatHistory.value.find(m => m.id === messageId)
    const feedbackMessageId = message?.message_id || message?.conversation_message_id || String(messageId)
    
    const token = localStorage.getItem('token')
    const response = await fetch('/api/chat/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message_id: String(feedbackMessageId),
        feedback: feedback
      })
    })
    
    if (response.status === 401 || response.status === 403) {
      const errorData = await response.json()
      if (errorData.detail === '无法验证凭据' || response.status === 401) {
        ElMessage.error('认证失败，请重新登录')
        const userStore = useUserStore()
        userStore.logout()
        router.push('/login')
        return
      }
    }
    
    if (response.ok) {
      const message = chatHistory.value.find(m => m.id === messageId)
      if (message) {
        message.user_feedback = feedback
      }
      ElMessage.success('反馈成功')
    } else if (response.status === 404) {
      ElMessage.warning('消息不存在或已反馈')
    } else {
      const errorData = await response.json()
      ElMessage.error(errorData.detail || '反馈失败')
    }
  } catch (error) {
    console.error('反馈失败:', error)
    ElMessage.error('反馈失败')
  }
}

// 发送消息
const sendMessage = async () => {
  if (!userInput.value.trim()) {
    return
  }

  if (!currentConversation.value) {
    await createNewConversation()
  }

  const question = userInput.value.trim()
  userInput.value = ''

  if (!selectedModelId.value) {
    ElMessage.warning('请先选择一个大模型')
    return
  }

  // 添加用户消息
  const userMessage = {
    id: Date.now(),
    content: question,
    is_user: true,
    timestamp: new Date()
  }
  chatHistory.value.push(userMessage)

  isLoading.value = true

  await nextTick()
  scrollToBottom()

  try {
    const textKbId = selectedTextKnowledgeBase.value ? parseInt(selectedTextKnowledgeBase.value) : undefined
    const dbKbId = selectedDbKnowledgeBase.value ? parseInt(selectedDbKnowledgeBase.value) : undefined
    const modelId = selectedModelId.value ? parseInt(selectedModelId.value) : undefined
    
    const response = await request.post('/chat/', {
      question,
      text_kb_id: textKbId,
      db_kb_id: dbKbId,
      model_id: modelId,
      conversation_id: currentConversation.value.id
    })

    const responseData = response

    // 添加AI回复
    const aiMessage = {
      id: responseData?.id || 0,
      content: responseData?.answer_text || '',
      is_user: false,
      timestamp: new Date(responseData?.created_time || ''),
      duration: responseData?.total_duration || null,
      answer_source: responseData?.answer_source || 0,
      model_name: responseData?.model_name || '',
      message_id: responseData?.message_id,
      conversation_message_id: responseData?.id,
      user_feedback: responseData?.user_feedback
    }
    chatHistory.value.push(aiMessage)
    
    // 更新当前对话标题
    currentConversation.value.title = responseData?.answer_text ? 
      (responseData?.answer_text.substring(0, 20) + (responseData?.answer_text.length > 20 ? '...' : '')) : 
      currentConversation.value.title || ''

  } catch (error: any) {
    console.error('发送消息失败:', error)
    ElMessage.error(error.response?.data?.detail || '发送消息失败')
    
    const errorMessage = {
      id: Date.now() + 1,
      content: '抱歉，我暂时无法回答您的问题。请稍后再试。',
      is_user: false,
      timestamp: new Date()
    }
    chatHistory.value.push(errorMessage)
  } finally {
    isLoading.value = false
    
    await nextTick()
    scrollToBottom()
  }
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const scrollToBottom = () => {
  if (chatHistoryRef.value) {
    chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
  }
}

const formatTime = (timestamp: Date | undefined | null) => {
  if (!timestamp) return ''
  return timestamp.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const logout = async () => {
  await userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.chat {
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, var(--color-bg-primary) 0%, var(--color-bg-tertiary) 100%);
  font-family: var(--font-family);
  line-height: 1.6;
}

.layout-container {
  height: 100%;
  width: 100%;
  display: flex;
}

.main-container {
  flex: 1;
  display: flex;
  min-width: 0;
}

.conversation-sidebar {
  width: 280px;
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border-light);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--color-border-light);
}

.sidebar-header h2 {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.new-chat-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--color-accent);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.new-chat-btn:hover {
  background: var(--color-accent-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.plus-icon {
  font-size: 16px;
}

.search-box {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border-light);
}

.search-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 14px;
  background: #fafafa;
  transition: all 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: #1677ff;
  background: #fff;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 0;
}

.conversation-group {
  margin-bottom: 8px;
}

.group-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 600;
  color: #8c8c8c;
  cursor: pointer;
  transition: all 0.2s ease;
}

.group-title:hover {
  background: var(--color-bg-hover);
}

.group-title:hover {
  background: var(--color-bg-hover);
}

.group-icon {
  font-size: 14px;
}

.expand-icon {
  margin-left: auto;
  font-size: 10px;
  transition: transform 0.2s ease;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.group-items {
  padding: 0 8px;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
}

.conversation-item:hover {
  background: var(--color-bg-hover);
}

.conversation-item.active {
  background: var(--color-accent-subtle);
  border: 1px solid var(--color-accent-light);
}

.conv-icon {
  font-size: 14px;
}

.conv-title {
  flex: 1;
  font-size: 14px;
  color: #262626;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-actions {
  display: none;
  gap: 4px;
}

.conversation-item:hover .conv-actions {
  display: flex;
}

.action-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  font-size: 12px;
  opacity: 0.6;
  transition: all 0.2s ease;
}

.action-btn:hover {
  opacity: 1;
}

.action-btn.delete:hover {
  color: #ff4d4f;
}

.empty-tip {
  padding: 16px;
  text-align: center;
  color: #8c8c8c;
  font-size: 13px;
}

/* 右侧聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: transparent;
  overflow: hidden;
}

.chat-header {
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.chat-header .header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.knowledge-base-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.kb-selector-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.kb-type-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #666;
  font-weight: 500;
  white-space: nowrap;
}

.kb-icon {
  font-size: 14px;
}

.kb-divider {
  color: #999;
  font-size: 12px;
}

.custom-select {
  padding: 8px 32px 8px 12px;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
  font-size: 13px;
  background: #fafafa;
  color: #999;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23999' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  transition: all 0.2s ease;
}

.custom-select.active {
  background-color: #fff;
  color: #333;
  border-color: #3b82f6;
}

.selected-kb-info {
  display: flex;
  align-items: center;
}

.mode-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.mode-badge.text-mode {
  background: #e6f4ff;
  color: #0958d9;
}

.mode-badge.db-mode {
  background: #f6ffed;
  color: #389e0d;
}

/* 用户下拉菜单 */
.user-dropdown {
  position: relative;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-info:hover {
  background: #f0f6ff;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff, #36cfc9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 14px;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #595959;
}

.dropdown-arrow {
  font-size: 10px;
  color: #8c8c8c;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  padding: 8px;
  min-width: 120px;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all 0.3s ease;
}

.user-dropdown:hover .dropdown-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.dropdown-item {
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: none;
  text-align: left;
  border-radius: 6px;
  font-size: 13px;
  color: #595959;
  cursor: pointer;
}

.dropdown-item:hover {
  background: #f0f6ff;
  color: #1890ff;
}

/* 聊天容器 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: 0;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 20px 24px 40px;
  background: transparent;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
  min-height: 0;
}

.welcome-tip {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #64748b;
}

.welcome-icon {
  font-size: 56px;
  margin-bottom: 20px;
}

.welcome-tip h3 {
  margin: 0 0 12px 0;
  font-size: 22px;
  color: #1e293b;
  font-weight: 600;
}

.welcome-tip p {
  margin: 0 0 28px 0;
  font-size: 14px;
  color: #64748b;
}

.start-btn {
  padding: 14px 36px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35);
}

.start-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

/* 消息样式 */
.message {
  display: flex;
  margin-bottom: 24px;
  gap: 12px;
  max-width: 100%;
  align-items: flex-start;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-message .message-avatar {
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
}

.ai-message .message-avatar {
  background: linear-gradient(135deg, #10b981, #34d399);
  color: white;
}

.message-content {
  background: white;
  padding: 12px 16px;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04);
  max-width: 75%;
  border: 1px solid #e2e8f0;
}

.user-message .message-content {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border: none;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}

.message-text {
  line-height: 1.6;
  font-size: 14px;
  color: #334155;
}

.user-message .message-text {
  color: white;
}

.message-time {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 6px;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.duration-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: #e0e7ff;
  color: #4338ca;
  font-weight: 500;
}

.cache-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.cache-tag.exact {
  background: #dcfce7;
  color: #166534;
}

.cache-tag.similar {
  background: #fef3c7;
  color: #92400e;
}

.model-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: #f1f5f9;
  color: #64748b;
}

.message-actions {
  display: flex;
  gap: 4px;
  margin-top: 6px;
}

.feedback-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 4px;
  border-radius: 4px;
  opacity: 0.5;
  transition: all 0.2s;
}

.feedback-btn:hover {
  background: #f1f5f9;
  opacity: 0.8;
}

.feedback-btn.active {
  opacity: 1;
  background: #e0f2fe;
}

.user-message .message-time {
  color: rgba(255, 255, 255, 0.7);
}

/* 加载状态 */
.loading-message {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 20px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  background: white;
  padding: 12px 16px;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid #e2e8f0;
}

.typing-indicator span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #3b82f6;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

/* 输入区域 */
.chat-input-area {
  background: white;
  border-top: 1px solid #e2e8f0;
  padding: 16px 24px 20px;
}

.input-container {
  display: none;
}

.input-wrapper {
  position: relative;
  display: flex;
  gap: 12px;
  align-items: flex-end;
  max-width: 900px;
  margin: 0 auto;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 8px 12px 8px 16px;
  transition: all 0.2s ease;
}

.input-wrapper:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.chat-textarea {
  flex: 1;
  border: none;
  border-radius: 0;
  padding: 10px 0;
  font-size: 14px;
  resize: none;
  font-family: inherit;
  line-height: 1.5;
  background: transparent;
  transition: all 0.2s ease;
  min-height: 24px;
  max-height: 120px;
}

.chat-textarea:focus {
  outline: none;
  box-shadow: none;
}

.chat-textarea:disabled {
  background: transparent;
  cursor: not-allowed;
}

.chat-textarea::placeholder {
  color: #94a3b8;
}

/* 输入框内工具栏 */
.input-inner-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
  border-top: 1px solid #f1f5f9;
  margin-top: 8px;
}

.send-button {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border: none;
  border-radius: 14px;
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
  align-self: flex-end;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.send-button:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.loading-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid transparent;
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.model-selector-container {
  display: none;
}

/* 底部工具栏 - 已移入输入框内部 */
.input-toolbar {
  display: none;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 模型下拉 */
.model-dropdown {
  position: relative;
}

.model-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  min-width: 120px;
}

.model-btn:hover:not(:disabled) {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.model-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.model-icon {
  font-size: 14px;
  flex-shrink: 0;
}

.model-name {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-arrow {
  font-size: 10px;
  color: #94a3b8;
  flex-shrink: 0;
}

.model-dropdown-menu {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin-bottom: 8px;
  min-width: 220px;
  max-width: 280px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  z-index: 100;
}

.model-dropdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  font-size: 13px;
  color: #334155;
  cursor: pointer;
  transition: background 0.15s ease;
}

.model-dropdown-item:hover {
  background: #f8fafc;
}

.model-dropdown-item.active {
  background: #eff6ff;
  color: #3b82f6;
  font-weight: 500;
}

.check-icon {
  font-size: 12px;
  color: #3b82f6;
}

/* 工具栏按钮 */
.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toolbar-btn:hover:not(:disabled) {
  background: #f1f5f9;
}

.future-btn {
  opacity: 0.5;
}

.future-btn:hover {
  opacity: 0.7;
}

.attach-icon,
.agent-icon {
  font-size: 16px;
}
</style>
