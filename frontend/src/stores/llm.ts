import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '../utils/request'

interface LLMModel {
  id: number
  name: string
  provider: string
  model_name: string
  base_url?: string
  is_active: boolean
  is_default: boolean
  created_at: string
  updated_at?: string
}

interface LLMModelCreate {
  name: string
  provider: string
  model_name: string
  api_key: string
  base_url?: string
  is_active: boolean
  is_default: boolean
}

interface LLMModelUpdate {
  name?: string
  provider?: string
  model_name?: string
  api_key?: string
  base_url?: string
  is_active?: boolean
  is_default?: boolean
}

export const useLLMStore = defineStore('llm', () => {
  const llmModels = ref<LLMModel[]>([])
  const activeModels = ref<LLMModel[]>([])
  const currentModel = ref<LLMModel | null>(null)

  // 获取大模型列表
  const fetchLLMModels = async () => {
    const response = await request.get('/llm/')
    llmModels.value = response.models
    return response.models
  }

  // 获取激活的大模型列表
  const fetchActiveModels = async () => {
    const response = await request.get('/llm/active')
    activeModels.value = response
    return response
  }

  // 获取大模型详情
  const getLLMModel = async (id: number) => {
    const response = await request.get(`/llm/${id}`)
    currentModel.value = response
    return response
  }

  // 创建大模型
  const createLLMModel = async (model: LLMModelCreate) => {
    const response = await request.post('/llm/', model)
    await fetchLLMModels()
    return response
  }

  // 更新大模型
  const updateLLMModel = async (id: number, model: LLMModelUpdate) => {
    const response = await request.put(`/llm/${id}`, model)
    await fetchLLMModels()
    return response
  }

  // 删除大模型
  const deleteLLMModel = async (id: number) => {
    const response = await request.delete(`/llm/${id}`)
    await fetchLLMModels()
    return response
  }

  // 测试大模型连接
  const testLLMModel = async (id: number) => {
    const response = await request.get(`/llm/${id}/test`)
    return response
  }

  // 获取默认模型
  const getDefaultModel = () => {
    return llmModels.value.find(model => model.is_default) || null
  }

  return {
    llmModels,
    activeModels,
    currentModel,
    fetchLLMModels,
    fetchActiveModels,
    getLLMModel,
    createLLMModel,
    updateLLMModel,
    deleteLLMModel,
    testLLMModel,
    getDefaultModel
  }
})