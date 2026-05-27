<template>
  <div class="llm-management">
    <div class="layout-container">
      <Sidebar />
      
      <div class="main-container">
        <PageHeader title="大模型管理" />
        
        <main class="main-content">
          <div class="page-header">
            <button class="btn-primary" @click="showCreateDialog = true">
              <span>+</span> 添加大模型
            </button>
          </div>

          <div class="llm-list">
            <div v-for="model in llmModels" :key="(model as any).id" class="llm-card">
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
                    v-if="(model as any).is_default" 
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
                <h3>{{ showEditDialog ? '编辑大模型' : '添加大模型' }}</h3>
                <button class="btn-close" @click="closeDialog">×</button>
              </div>
              
              <div class="modal-body">
                <form @submit.prevent="submitForm">
                  <div class="form-group">
                    <label>模型名称 *</label>
                    <input 
                      v-model="form.name" 
                      type="text" 
                      placeholder="例如：GPT-3.5 Turbo"
                      required
                    >
                  </div>
                  
                  <div class="form-group">
                    <label>提供商 *</label>
                    <select v-model="form.provider" required @change="onProviderChange">
                      <option value="">请选择提供商</option>
                      <option value="openai">OpenAI</option>
                      <option value="azure">Azure OpenAI</option>
                      <option value="anthropic">Anthropic</option>
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
                      <div class="help-tooltip">
                        <span class="help-icon">?</span>
                        <div class="tooltip-content">
                          <p><strong>模型标识说明：</strong></p>
                          <ul>
                            <li>OpenAI: gpt-3.5-turbo, gpt-4, gpt-4-turbo</li>
                            <li>Azure OpenAI: 部署名称</li>
                            <li>Anthropic: claude-3-sonnet, claude-3-haiku</li>
                            <li>自定义: 您自定义的模型名称</li>
                          </ul>
                          <p>这个标识将用于实际的API调用</p>
                        </div>
                      </div>
                    </div>
                    <input 
                      v-model="form.model_name" 
                      type="text" 
                      placeholder="例如：gpt-3.5-turbo"
                      required
                    >
                  </div>
                  
                  <div class="form-group">
                    <label>API密钥 *</label>
                    <input 
                      v-model="form.api_key" 
                      type="password" 
                      placeholder="输入API密钥"
                      required
                    >
                  </div>
                  
                  <div class="form-group">
                    <label>API地址</label>
                    <input 
                      v-model="form.base_url" 
                      type="text" 
                      placeholder="可选，例如：https://api.openai.com/v1"
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
import { useLLMStore } from '../stores/llm'
import Sidebar from '@/components/Sidebar.vue'
import PageHeader from '@/components/PageHeader.vue'

const llmStore = useLLMStore()
const userStore = useUserStore()
const router = useRouter()

const llmModels = ref([])
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
  is_active: true,
  is_default: false
})

// 提供商变更处理
const onProviderChange = () => {
  if (form.provider !== 'custom') {
    form.custom_provider = ''
  }
}

// 加载大模型列表
const loadLLMModels = async () => {
  try {
    const response = await llmStore.fetchLLMModels()
    // 后端返回 { models: [...], total: n }，需要取 response.models
    llmModels.value = response?.models || response || []
  } catch (error) {
    ElMessage.error('加载大模型列表失败')
    console.error(error)
  }
}

// 编辑模型
const editModel = (model: any) => {
  editingModelId.value = model.id
  
  // 判断是否为自定义提供商
  const isCustomProvider = !['openai', 'azure', 'anthropic'].includes(model.provider)
  
  Object.assign(form, {
    name: model.name,
    provider: isCustomProvider ? 'custom' : model.provider,
    custom_provider: isCustomProvider ? model.provider : '',
    model_name: model.model_name,
    api_key: '', // 不显示原密钥
    base_url: model.base_url || '',
    is_active: model.is_active,
    is_default: model.is_default
  })
  showEditDialog.value = true
}

// 删除模型
const deleteModel = async (model: any) => {
  if (!confirm(`确定要删除大模型"${model.name}"吗？`)) return
  
  try {
    await llmStore.deleteLLMModel(model.id)
    ElMessage.success('删除成功')
    await loadLLMModels()
  } catch (error) {
    ElMessage.error('删除失败')
    console.error(error)
  }
}

// 测试模型连接
const testModel = async (modelId: number) => {
  try {
    const result = await llmStore.testLLMModel(modelId)
    if ((result as any).success) {
      ElMessage.success(`测试成功: ${result.data}`)
    } else {
      ElMessage.error(`测试失败: ${result.data}`)
    }
  } catch (error) {
    ElMessage.error('测试失败')
    console.error(error)
  }
}

// 设为默认模型
const setAsDefault = async (modelId: number) => {
  try {
    await llmStore.updateLLMModel(modelId, { is_default: true })
    ElMessage.success('设置成功')
    await loadLLMModels()
  } catch (error) {
    ElMessage.error('设置失败')
    console.error(error)
  }
}

// 提交表单
const submitForm = async () => {
  loading.value = true
  
  try {
    // 处理自定义提供商
    const submitData = { ...form }
    if (form.provider === 'custom' && form.custom_provider) {
      submitData.provider = form.custom_provider
    }
    
    if (showEditDialog.value && editingModelId.value) {
      await llmStore.updateLLMModel(editingModelId.value, submitData)
      ElMessage.success('更新成功')
    } else {
      await llmStore.createLLMModel(submitData)
      ElMessage.success('创建成功')
    }
    
    closeDialog()
    await loadLLMModels()
  } catch (error) {
    ElMessage.error(showEditDialog.value ? '更新失败' : '创建失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 关闭对话框
const closeDialog = () => {
  showCreateDialog.value = false
  showEditDialog.value = false
  editingModelId.value = null
  Object.assign(form, {
    name: '',
    provider: '',
    model_name: '',
    api_key: '',
    base_url: '',
    is_active: true,
    is_default: false
  })
}

onMounted(() => {
  loadLLMModels()
})
</script>

<style scoped>
.llm-management {
  height: 100vh;
}

.layout-container {
  height: 100%;
  width: 100%;
  display: flex;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

/* 主内容区 - 智谱风格 */
.main-content {
  flex: 1;
  padding: 36px;
  overflow-y: auto;
  background: transparent;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.llm-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
  gap: 24px;
}

.llm-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border-light);
  overflow: hidden;
  transition: all var(--transition-normal);
}

.llm-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-accent-light);
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--color-bg-tertiary);
}

.card-header h4 {
  margin: 0;
  color: var(--color-accent);
  font-size: 18px;
  font-weight: 600;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  background: rgba(24, 144, 255, 0.1);
  border: none;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--color-accent);
  transition: all 0.3s ease;
}

.btn-icon:hover {
  background: rgba(24, 144, 255, 0.2);
  transform: scale(1.05);
}

.btn-icon.danger {
  background: rgba(255, 77, 79, 0.1);
  color: #ff4d4f;
}

.btn-icon.danger:hover {
  background: rgba(255, 77, 79, 0.2);
}

.card-content {
  padding: 20px 24px;
}

.model-info {
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 14px;
  line-height: 1.5;
}

.info-item label {
  font-weight: 500;
  color: #8c8c8c;
  min-width: 80px;
}

.info-item span {
  color: #262626;
  font-weight: 400;
}

.status-active {
  color: #52c41a;
  font-weight: 600;
  padding: 4px 8px;
  background: rgba(82, 196, 26, 0.1);
  border-radius: 4px;
}

.status-inactive {
  color: #ff4d4f;
  font-weight: 600;
  padding: 4px 8px;
  background: rgba(255, 77, 79, 0.1);
  border-radius: 4px;
}

.status-default {
  color: var(--color-accent);
  font-weight: 600;
  padding: 4px 8px;
  background: rgba(24, 144, 255, 0.1);
  border-radius: 4px;
}

.base-url {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
  font-size: 12px;
  background: rgba(24, 144, 255, 0.05);
  padding: 4px 8px;
  border-radius: 4px;
  color: var(--color-accent);
}

/* 模态框样式 - 智谱风格 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  width: 500px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
  border: 1px solid rgba(24, 144, 255, 0.2);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(20px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  padding: 24px 28px;
  border-bottom: 1px solid rgba(24, 144, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.02) 0%, rgba(54, 207, 201, 0.02) 100%);
}

.modal-header h3 {
  margin: 0;
  color: var(--color-accent);
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.2px;
}

.btn-close {
  background: var(--color-accent-light);
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--color-accent);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.btn-close:hover {
  background: rgba(24, 144, 255, 0.2);
  transform: rotate(90deg);
}

.modal-body {
  padding: 28px;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #262626;
  font-size: 14px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid rgba(24, 144, 255, 0.3);
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.8);
  transition: all 0.3s ease;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-light);
  background: white;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px 0;
  transition: all 0.3s ease;
}

.checkbox:hover {
  background: rgba(24, 144, 255, 0.05);
  border-radius: 8px;
  padding: 8px 12px;
}

.checkbox input {
  width: 18px;
  height: 18px;
  margin: 0;
  accent-color: var(--color-accent);
  cursor: pointer;
}

.checkbox span {
  font-weight: 500;
  color: var(--color-text-primary);
}

.form-actions {
  display: flex;
  gap: 16px;
  justify-content: flex-end;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(24, 144, 255, 0.1);
}

/* 按钮样式 - 智谱风格 */
.btn-primary, .btn-secondary {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 0.5px;
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-hover) 100%);
  color: white;
  box-shadow: 0 4px 12px var(--color-accent-light);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px var(--color-accent-light);
}

.btn-primary:disabled {
  background: var(--color-text-muted);
  cursor: not-allowed;
  box-shadow: none;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.9);
  color: var(--color-accent);
  border: 1px solid var(--color-accent-light);
  backdrop-filter: blur(10px);
}

.btn-secondary:hover {
  background: var(--color-accent-light);
  border-color: var(--color-accent);
}

/* 字段帮助和工具提示样式 - 智谱风格 */
.field-help {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.field-help span {
  font-size: 12px;
  color: #8c8c8c;
  font-weight: 500;
}

.help-tooltip {
  position: relative;
  display: inline-block;
}

.help-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: var(--color-accent);
  color: white;
  border-radius: 50%;
  font-size: 11px;
  font-weight: 700;
  cursor: help;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.help-icon:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.4);
}

.tooltip-content {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(24, 144, 255, 0.95);
  backdrop-filter: blur(20px);
  color: white;
  padding: 16px;
  border-radius: 12px;
  font-size: 12px;
  width: 300px;
  box-shadow: 0 12px 32px rgba(24, 144, 255, 0.2);
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.help-tooltip:hover .tooltip-content {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) translateY(-4px);
}

.tooltip-content p {
  margin: 0 0 12px 0;
  font-weight: 600;
  font-size: 13px;
}

.tooltip-content ul {
  margin: 0;
  padding-left: 16px;
}

.tooltip-content li {
  margin-bottom: 6px;
  line-height: 1.4;
}

.tooltip-content li:last-child {
  margin-bottom: 0;
}

</style>