import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export interface ChatMessage {
  id: number
  user_id: number
  knowledge_base_id?: number
  question: string
  answer: string
  sources?: string
  created_at: string
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const currentMessage = ref('')
  const isStreaming = ref(false)
  const streamContent = ref('')

  const sendMessage = async (question: string, textKbId?: number, dbKbId?: number, modelId?: number) => {
    const response = await request.post('/chat/', {
      question,
      text_kb_id: textKbId,
      db_kb_id: dbKbId,
      model_id: modelId
    })
    
    messages.value.unshift(response)
    return response
  }

  const sendMessageStream = async (question: string, textKbId?: number, dbKbId?: number, modelId?: number) => {
    isStreaming.value = true
    streamContent.value = ''
    
    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          question,
          text_kb_id: textKbId,
          db_kb_id: dbKbId,
          model_id: modelId
        })
      })

      const reader = response.body?.getReader()
      if (!reader) return

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = new TextDecoder().decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data) {
              const parsed = JSON.parse(data)
              if (parsed.content) {
                streamContent.value += parsed.content
              }
              if (parsed.is_final) {
                isStreaming.value = false
                
                // 保存到消息历史
                const newMessage: ChatMessage = {
                  id: Date.now(),
                  user_id: 0, // 会在后端设置
                  knowledge_base_id: knowledgeBaseId,
                  question,
                  answer: streamContent.value,
                  sources: parsed.sources ? JSON.stringify(parsed.sources) : undefined,
                  created_at: new Date().toISOString()
                }
                
                messages.value.unshift(newMessage)
                streamContent.value = ''
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Stream error:', error)
      isStreaming.value = false
    }
  }

  const fetchChatHistory = async (knowledgeBaseId?: number, skip: number = 0, limit: number = 50) => {
    const params = new URLSearchParams()
    if (knowledgeBaseId) params.append('knowledge_base_id', knowledgeBaseId.toString())
    params.append('skip', skip.toString())
    params.append('limit', limit.toString())
    
    const response = await request.get(`/chat/history?${params}`)
    messages.value = response
    return response
  }

  const getChatHistory = async () => {
    if (messages.value.length === 0) {
      return await fetchChatHistory()
    }
    return messages.value
  }

  const deleteChatHistory = async (chatId: number) => {
    await request.delete(`/chat/history/${chatId}`)
    messages.value = messages.value.filter(msg => msg.id !== chatId)
  }

  const clearCurrentMessage = () => {
    currentMessage.value = ''
  }

  const stopStreaming = () => {
    isStreaming.value = false
    streamContent.value = ''
  }

  return {
    messages,
    currentMessage,
    isStreaming,
    streamContent,
    sendMessage,
    sendMessageStream,
    fetchChatHistory,
    getChatHistory,
    deleteChatHistory,
    clearCurrentMessage,
    stopStreaming
  }
})