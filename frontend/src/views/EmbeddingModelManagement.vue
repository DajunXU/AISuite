<template>
  <div class="embedding-management">
    <div class="layout-container">
      <Sidebar />
      
      <div class="main-container">
        <PageHeader title="向量模型管理" />
        
        <main class="main-content">
          <div class="page-header">
            <button class="btn-primary" @click="showCreateDialog = true">
              <span>+</span> 添加向量模型
            </button>
          </div>

          <div class="embedding-list">
            <div v-for="model in embeddingModels" :key="(model as any).id" class="embedding-card">
              <div class="card-header">
                <h4>{{ (model as any).name || '未知模型' }}</h4>
                <div class="card-actions">
                  <button class="btn-icon" @click="editModel(model)" title="编辑">✏️</button>
                  <button class="btn-icon danger" @click="deleteModel(model)" title="删除">🗑️</button>
                </div>
              </div>
              
              <div class="card-content">
                <div class="model-info">
                  <div class="info-item">
                    <label>提供商:</label>
                    <span>{{ (model as any).provider || '未知' }}</span>
                  </div>
                  <div class="info-item">
                    <label>模型名称:</label>
                    <span>{{ (model as any).model_name || '未知' }}</span>
                  </div>
                  <div class="info-item">
                    <label>向量维度:</label>
                    <span>{{ (model as any).dimensions || '未知' }}</span>
                  </div>
                  <div class="info-item">
                    <label>状态:</label>
                    <span :class="(model as any).is_active ? 'status-active' : 'status-inactive'">
                      {{ (model as any).is_active ? '激活' : '禁用' }}
                    </span>
                  </div>
                  <div class="info-item">
                    <label>默认模型:</label>
                    <span :class="(model as any).is_default ? 'status-default' : ''">
                      {{ (model as any).is_default ? '是' : '否' }}
                    </span>
                  </div>
                  <div v-if="(model as any).base_url" class="info-item">
                    <label>API地址:</label>
                    <span class="base-url">{{ (model as any).base_url || '未知' }}</span>
                  </div>
                </div>
                
                <div class="card-actions">
                  <button class="btn-secondary" @click="testModel((model as any).id)">测试连接</button>
                  <button 
                    v-if="!(model as any).is_default" 
                    class="btn-secondary" 
                    @click="setAsDefault((model as any).id)"
                  >
                    设为默认
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- 创建/编辑对话框 -->
          <div v-if="showCreateDialog || showEditDialog" class="modal-overlay">
            <div class="modal-content">
              <div class="modal-header">
                <h3>{{ showEditDialog ? '编辑向量模型' : '添加向量模型' }}</h3>
                <button class="btn-close" @click="closeDialog">×</button>
              </div>
              
              <div class="modal-body">
                <form @submit.prevent="submitForm">
                  <div class="form-group">
                    <label>模型名称 *</label>
                    <input 
                      v-model="form.name" 
                      type="text" 
                      placeholder="例如：text-embedding-v4"
                      required
                    >
                  </div>
                  
                  <div class="form-group">
                    <label>提供商 *</label>
                    <select v-model="form.provider" required @change="onProviderChange">
                      <option value="">请选择提供商</option>
                      <option value="openai">OpenAI</option>
                      <option value="qwen">阿里云 (Qwen)</option>
                      <option value="zhipu">智谱AI</option>
                      <option value="custom">自定义</option>
                    </select>
                  </div>
                  
                  <!-- 自定义提供商输入框 -->
                  <div v-if="form.provider === 'custom'" class="form-group">
                    <label>自定义提供商名称 *</label>
                    <input 
                      v-model="form.custom_provider" 
                      type="text" 
                      placeholder="输入自定义提供商名称"
                      required
                    >
                  </div>
                  
                  <div class="form-group">
                    <label>模型标识 *</label>
                    <div class="field-help">
                      <span>这是API调用时使用的实际模型名称</span>
                    </div>
                    <input 
                      v-model="form.model_name" 
                      type="text" 
                      placeholder="例如：text-embedding-3-small"
                      required
                    >
                  </div>
                  
                  <div class="form-group">
                    <label>API密钥</label>
                    <input 
                      v-model="form.api_key" 
                      type="password" 
                      placeholder="输入API密钥（可选）"
                    >
                  </div>
                  
                  <div class="form-group">
                    <label>API地址</label>
                    <input 
                      v-model="form.base_url" 
                      type="text" 
                      placeholder="可选，例如：https://dashscope.aliyuncs.com/compatible-mode/v1"
                    >
                  </div>
                  
                  <div class="form-group">
                    <label>向量维度</label>
                    <input 
                      v-model.number="form.dimensions" 
                      type="number" 
                      placeholder="默认：1024"
                    >
                  </div>
                  
                  <div class="form-group">
                    <label>最大输入token</label>
                    <input 
                      v-model.number="form.max_tokens" 
                      type="number" 
                      placeholder="默认：8192"
                    >
                  </div>
                  
                  <div class="form-group checkbox-group">
                    <label class="checkbox">
                      <input v-model="form.is_active" type="checkbox">
                      <span>激活模型</span>
                    </label>
                    <label class="checkbox">
                      <input v-model="form.is_default" type="checkbox">
                      <span>设为默认模型</span>
                    </label>
                  </div>
                  
                  <div class="form-actions">
                    <button type="button" class="btn-secondary" @click="closeDialog">取消</button>
                    <button type="submit" class="btn-primary" :disabled="loading">
                      {{ loading ? '保存中...' : '保存' }}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import Sidebar from '@/components/Sidebar.vue'
import PageHeader from '@/components/PageHeader.vue'
import axios from 'axios'

const userStore = useUserStore()
const router = useRouter()

const embeddingModels = ref([])
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const loading = ref(false)
const editingModelId = ref<number | null>(null)

const form = reactive({
  name: '',
  provider: '',
  custom_provider: '',
  model_name: '',
  api_key: '',
  base_url: '',
  dimensions: 1024,
  max_tokens: 8192,
  is_active: true,
  is_default: false,
  is_api: true
})

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

const onProviderChange = () => {
  if (form.provider !== 'custom') {
    form.custom_provider = ''
  }
}

const loadEmbeddingModels = async () => {
  try {
    const response = await api.get('/embedding/')
    embeddingModels.value = response.data?.models || []
  } catch (error) {
    ElMessage.error('加载向量模型列表失败')
    console.error(error)
  }
}

const editModel = (model: any) => {
  editingModelId.value = model.id
  
  const isCustomProvider = !['openai', 'qwen', 'zhipu'].includes(model.provider)
  
  Object.assign(form, {
    name: model.name,
    provider: isCustomProvider ? 'custom' : model.provider,
    custom_provider: isCustomProvider ? model.provider : '',
    model_name: model.model_name,
    api_key: '',
    base_url: model.base_url || '',
    dimensions: model.dimensions || 1024,
    max_tokens: model.max_tokens || 8192,
    is_active: model.is_active,
    is_default: model.is_default,
    is_api: model.is_api
  })
  showEditDialog.value = true
}

const deleteModel = async (model: any) => {
  if (!confirm(`确定要删除向量模型"${model.name}"吗？`)) return
  
  try {
    await api.delete(`/embedding/${model.id}`)
    ElMessage.success('删除成功')
    await loadEmbeddingModels()
  } catch (error: any) {
    const msg = error.response?.data?.detail || '删除失败'
    ElMessage.error(msg)
    console.error(error)
  }
}

const testModel = async (modelId: number) => {
  try {
    const result = await api.get(`/embedding/${modelId}/test`)
    if (result.data?.success) {
      ElMessage.success(`测试成功: ${result.data.message}`)
    } else {
      ElMessage.error(`测试失败: ${result.data?.message}`)
    }
  } catch (error: any) {
    const msg = error.response?.data?.detail || '测试失败'
    ElMessage.error(msg)
    console.error(error)
  }
}

const setAsDefault = async (modelId: number) => {
  try {
    await api.put(`/embedding/${modelId}`, { is_default: true })
    ElMessage.success('设置成功')
    await loadEmbeddingModels()
  } catch (error) {
    ElMessage.error('设置失败')
    console.error(error)
  }
}

const closeDialog = () => {
  showCreateDialog.value = false
  showEditDialog.value = false
  editingModelId.value = null
  Object.assign(form, {
    name: '',
    provider: '',
    custom_provider: '',
    model_name: '',
    api_key: '',
    base_url: '',
    dimensions: 1024,
    max_tokens: 8192,
    is_active: true,
    is_default: false,
    is_api: true
  })
}

const submitForm = async () => {
  loading.value = true
  
  const provider = form.provider === 'custom' ? form.custom_provider : form.provider
  
  const data = {
    name: form.name,
    provider: provider,
    model_name: form.model_name,
    api_key: form.api_key || null,
    base_url: form.base_url || null,
    dimensions: form.dimensions,
    max_tokens: form.max_tokens,
    is_active: form.is_active,
    is_default: form.is_default,
    is_api: form.is_api
  }
  
  try {
    if (editingModelId.value) {
      await api.put(`/embedding/${editingModelId.value}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/embedding/', data)
      ElMessage.success('创建成功')
    }
    closeDialog()
    await loadEmbeddingModels()
  } catch (error: any) {
    const msg = error.response?.data?.detail || '操作失败'
    ElMessage.error(msg)
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadEmbeddingModels()
})
</script>

<style scoped>
.embedding-management {
  height: 100vh;
  display: flex;
}

.layout-container {
  display: flex;
  width: 100%;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.page-header {
  margin-bottom: 20px;
}

.btn-primary {
  background: #409eff;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-primary:hover {
  background: #66b1ff;
}

.embedding-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.embedding-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.card-header h4 {
  margin: 0;
  font-size: 16px;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
}

.btn-icon.danger:hover {
  color: #f56c6c;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.info-item label {
  color: #909399;
  min-width: 80px;
}

.status-active {
  color: #67c23a;
}

.status-inactive {
  color: #909399;
}

.status-default {
  color: #409eff;
  font-weight: bold;
}

.base-url {
  word-break: break-all;
  font-size: 12px;
  color: #606266;
}

.btn-secondary {
  background: #f5f7fa;
  color: #606266;
  border: 1px solid #dcdfe6;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-secondary:hover {
  background: #e9eef3;
}

.card-actions {
  margin-top: 12px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #909399;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #409eff;
}

.field-help {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
  color: #909399;
}

.checkbox-group {
  display: flex;
  gap: 20px;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
</style>
