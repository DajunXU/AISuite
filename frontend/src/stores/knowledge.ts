import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export interface EmbeddingModel {
  id: number
  name: string
  provider: string
  model_name: string
  base_url?: string
  dimensions: number
  max_tokens: number
  is_active: boolean
  is_default: boolean
  is_api: boolean
}

export interface KnowledgeBase {
  id: number
  name: string
  description?: string
  owner_id: number
  is_public: boolean
  embedding_model_id?: number
  embedding_model?: EmbeddingModel
  created_at: string
  updated_at?: string
}

export const useKnowledgeStore = defineStore('knowledge', () => {
  const knowledgeBases = ref<KnowledgeBase[]>([])
  const currentKnowledgeBase = ref<KnowledgeBase | null>(null)

  const fetchKnowledgeBases = async () => {
    const response = await request.get('/knowledge/')
    knowledgeBases.value = response
    return response
  }

  const getKnowledgeBases = async () => {
    if (knowledgeBases.value.length === 0) {
      return await fetchKnowledgeBases()
    }
    return knowledgeBases.value
  }

  const createKnowledgeBase = async (data: {
    name: string
    description?: string
    is_public?: boolean
  }) => {
    const response = await request.post('/knowledge/', data)
    knowledgeBases.value.push(response)
    return response
  }

  const updateKnowledgeBase = async (id: number, data: {
    name?: string
    description?: string
    is_public?: boolean
  }) => {
    const response = await request.put(`/knowledge/${id}`, data)
    const index = knowledgeBases.value.findIndex(kb => kb.id === id)
    if (index !== -1) {
      knowledgeBases.value[index] = response
    }
    return response
  }

  const deleteKnowledgeBase = async (id: number) => {
    await request.delete(`/knowledge/${id}`)
    knowledgeBases.value = knowledgeBases.value.filter(kb => kb.id !== id)
  }

  const batchDeleteKnowledgeBases = async (ids: number[]) => {
    await request.post('/knowledge/batch-delete', { kb_ids: ids })
    knowledgeBases.value = knowledgeBases.value.filter(kb => !ids.includes(kb.id))
  }

  const getKnowledgeBase = async (id: number) => {
    const response = await request.get(`/knowledge/${id}`)
    currentKnowledgeBase.value = response
    return response
  }

  const uploadDocument = async (id: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await request.post(`/knowledge/${id}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    return response
  }

  const grantPermission = async (kbId: number, userId: number, canRead: boolean, canWrite: boolean) => {
    const response = await request.post(`/knowledge/${kbId}/permissions`, {
      user_id: userId,
      knowledge_base_id: kbId,
      can_read: canRead,
      can_write: canWrite
    })
    
    return response
  }

  const getKnowledgeBaseFiles = async (kbId: number) => {
    const response = await request.get(`/knowledge/${kbId}/files`)
    return response
  }

  const getAccessibleKnowledgeBases = async () => {
    const response = await request.get('/permission/knowledge-bases/accessible/')
    return response
  }

  const getEmbeddingModels = async () => {
    const response = await request.get('/embedding/')
    return response.models || []
  }

  const getActiveEmbeddingModels = async () => {
    const response = await request.get('/embedding/active')
    return response
  }

  return {
    knowledgeBases,
    currentKnowledgeBase,
    fetchKnowledgeBases,
    getKnowledgeBases,
    getAccessibleKnowledgeBases,
    getEmbeddingModels,
    getActiveEmbeddingModels,
    createKnowledgeBase,
    updateKnowledgeBase,
    deleteKnowledgeBase,
    batchDeleteKnowledgeBases,
    getKnowledgeBase,
    uploadDocument,
    grantPermission,
    getKnowledgeBaseFiles
  }
})