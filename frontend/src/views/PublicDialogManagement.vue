<template>
  <div class="dashboard">
    <div class="layout-container">
      <Sidebar />
      
      <div class="main-container">
        <PageHeader title="公开对话管理" />
        
        <main class="main-content">
          <div class="public-dialog-management">
            <div class="page-header">
              <div class="header-title">
                <h3>公开对话列表</h3>
                <p class="subtitle">管理和发布无需登录即可访问的AI对话</p>
              </div>
              <el-button type="primary" class="create-btn" @click="showCreateDialog = true">
                <span class="btn-icon">+</span>
                创建公开对话
              </el-button>
            </div>

            <el-table :data="dialogs" style="width: 100%" v-loading="loading" class="custom-table">
              <el-table-column prop="name" label="名称" min-width="150" />
              <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
              <el-table-column label="访问链接" min-width="200">
                <template #default="{ row }">
                  <div class="link-cell">
                    <el-link type="primary" :href="`/dialog/${row.dialog_code}`" target="_blank" class="dialog-link">
                      /dialog/{{ row.dialog_code }}
                    </el-link>
                    <el-button size="small" text @click="copyLink(row.dialog_code)">复制</el-button>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="visit_count" label="访问次数" width="100" align="center" />
              <el-table-column label="状态" width="80" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.is_active ? 'success' : 'info'" size="small" class="status-tag">
                    {{ row.is_active ? '启用' : '禁用' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="创建时间" width="160">
                <template #default="{ row }">
                  {{ formatDate(row.created_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="160" align="center">
                <template #default="{ row }">
                  <el-button size="small" class="action-btn" @click="editDialog(row)">编辑</el-button>
                  <el-button size="small" type="danger" plain class="action-btn" @click="deleteDialog(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="pagination-wrapper">
              <el-pagination
                v-model:current-page="currentPage"
                :page-size="pageSize"
                :total="total"
                layout="total, prev, pager, next"
                @current-change="loadDialogs"
              />
            </div>
          </div>
        </main>
      </div>
    </div>

    <el-dialog v-model="showCreateDialog" title="创建公开对话" width="700px" :close-on-click-modal="false" class="custom-dialog">
      <el-form :model="form" label-width="120px" ref="formRef" class="dialog-form">
        <el-form-item label="对话框名称" required>
          <el-input v-model="form.name" placeholder="例如：产品咨询客服" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="2" placeholder="简短描述此对话的用途" />
        </el-form-item>
        <el-form-item label="欢迎语">
          <el-input v-model="form.welcome_message" type="textarea" rows="2" placeholder="用户打开对话时显示的欢迎信息" />
        </el-form-item>
        <el-form-item label="关联知识库" required>
          <el-select v-model="form.knowledge_base_ids" multiple placeholder="选择知识库" style="width: 100%">
            <el-option
              v-for="kb in knowledgeBases"
              :key="kb.id"
              :label="`${kb.name} (${kb.kb_type === 'file' ? '文本' : '数据库'})`"
              :value="kb.id"
            />
          </el-select>
          <div class="form-tip">选择该对话可以访问的知识库</div>
        </el-form-item>
        <el-form-item label="使用模型">
          <el-select v-model="form.model_id" placeholder="使用默认模型" clearable style="width: 100%">
            <el-option
              v-for="model in models"
              :key="model.id"
              :label="model.name"
              :value="model.id"
            />
          </el-select>
          <div class="form-tip">选择要使用的AI模型，默认为系统默认模型</div>
        </el-form-item>
        <el-form-item label="推荐问题">
          <div v-for="(q, index) in form.recommended_questions" :key="index" style="display: flex; gap: 8px; margin-bottom: 8px">
            <el-input v-model="form.recommended_questions[index]" placeholder="问题内容" />
            <el-button type="danger" @click="removeQuestion(index)">删除</el-button>
          </div>
          <el-button size="small" @click="addQuestion">添加问题</el-button>
          <div class="form-tip">用户打开对话时可见的推荐问题</div>
        </el-form-item>
        <el-form-item label="自定义提示词">
          <el-input v-model="form.custom_prompt" type="textarea" rows="3" placeholder="可设置系统提示词，影响AI回答风格" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="语言">
              <el-select v-model="form.language" style="width: 100%">
                <el-option label="中文" value="zh" />
                <el-option label="English" value="en" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用反馈">
              <el-switch v-model="form.feedback_enabled" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="过期时间">
          <el-date-picker
            v-model="form.expires_at"
            type="datetime"
            placeholder="选择过期时间（可选）"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
          <div class="form-tip">超过此时间后对话将不可访问</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">创建</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="showEditDialog" title="编辑公开对话" width="700px" :close-on-click-modal="false" class="custom-dialog">
      <el-form :model="editForm" label-width="120px" ref="editFormRef" class="dialog-form">
        <el-form-item label="对话框名称" required>
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item label="欢迎语">
          <el-input v-model="editForm.welcome_message" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item label="关联知识库" required>
          <el-select v-model="editForm.knowledge_base_ids" multiple placeholder="选择知识库" style="width: 100%">
            <el-option
              v-for="kb in knowledgeBases"
              :key="kb.id"
              :label="`${kb.name} (${kb.kb_type === 'file' ? '文本' : '数据库'})`"
              :value="kb.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="使用模型">
          <el-select v-model="editForm.model_id" placeholder="使用默认模型" clearable style="width: 100%">
            <el-option
              v-for="model in models"
              :key="model.id"
              :label="model.name"
              :value="model.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="推荐问题">
          <div v-for="(q, index) in editForm.recommended_questions" :key="index" style="display: flex; gap: 8px; margin-bottom: 8px">
            <el-input v-model="editForm.recommended_questions[index]" placeholder="问题内容" />
            <el-button type="danger" @click="removeEditQuestion(index)">删除</el-button>
          </div>
          <el-button size="small" @click="addEditQuestion">添加问题</el-button>
        </el-form-item>
        <el-form-item label="自定义提示词">
          <el-input v-model="editForm.custom_prompt" type="textarea" rows="3" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="语言">
              <el-select v-model="editForm.language" style="width: 100%">
                <el-option label="中文" value="zh" />
                <el-option label="English" value="en" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用反馈">
              <el-switch v-model="editForm.feedback_enabled" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="启用状态">
          <el-switch v-model="editForm.is_active" />
        </el-form-item>
        <el-form-item label="过期时间">
          <el-date-picker
            v-model="editForm.expires_at"
            type="datetime"
            placeholder="选择过期时间"
            style="width: 100%"
            value-format="YYYY-MM-DD HH:mm:ss"
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="submitEditForm" :loading="submitting">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'
import Sidebar from '../components/Sidebar.vue'
import PageHeader from '@/components/PageHeader.vue'

const loading = ref(false)
const submitting = ref(false)
const dialogs = ref<any[]>([])
const knowledgeBases = ref<any[]>([])
const models = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const showCreateDialog = ref(false)
const showEditDialog = ref(false)

const form = reactive({
  name: '',
  description: '',
  welcome_message: '您好！有什么可以帮助您的？',
  recommended_questions: [] as string[],
  custom_prompt: '',
  knowledge_base_ids: [] as number[],
  model_id: null as number | null,
  language: 'zh',
  feedback_enabled: false,
  expires_at: null as string | null
})

const editForm = reactive({
  id: 0,
  name: '',
  description: '',
  welcome_message: '',
  recommended_questions: [] as string[],
  custom_prompt: '',
  knowledge_base_ids: [] as number[],
  model_id: null as number | null,
  language: 'zh',
  feedback_enabled: false,
  is_active: true,
  expires_at: null as string | null
})

const loadDialogs = async () => {
  loading.value = true
  try {
    const res = await request.get('/public-dialog/', {
      params: {
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value
      }
    })
    dialogs.value = (res as any)?.dialogs || (res as any)?.data?.dialogs || []
    total.value = (res as any)?.total || (res as any)?.data?.total || 0
  } catch (error) {
    ElMessage.error('加载对话列表失败')
  } finally {
    loading.value = false
  }
}

const loadKnowledgeBases = async () => {
  try {
    const res = await request.get('/knowledge/')
    knowledgeBases.value = res?.data || res || []
  } catch (error) {
    console.error('加载知识库失败:', error)
  }
}

const loadModels = async () => {
  try {
    const result = await request.get('/llm/models')
    models.value = result || []
  } catch (error) {
    console.error('加载模型失败:', error)
  }
}

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const copyLink = (code: string) => {
  const link = `${window.location.origin}/dialog/${code}`
  navigator.clipboard.writeText(link)
  ElMessage.success('链接已复制到剪贴板')
}

const addQuestion = () => {
  form.recommended_questions.push('')
}

const removeQuestion = (index: number) => {
  form.recommended_questions.splice(index, 1)
}

const addEditQuestion = () => {
  editForm.recommended_questions.push('')
}

const removeEditQuestion = (index: number) => {
  editForm.recommended_questions.splice(index, 1)
}

const submitForm = async () => {
  if (!form.name) {
    ElMessage.warning('请输入对话框名称')
    return
  }
  if (form.knowledge_base_ids.length === 0) {
    ElMessage.warning('请至少选择一个知识库')
    return
  }

  submitting.value = true
  try {
    const data = {
      ...form,
      recommended_questions: form.recommended_questions.filter(q => q.trim())
    }
    await request.post('/public-dialog/', data)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    loadDialogs()
    resetForm()
  } catch (error) {
    ElMessage.error('创建失败')
  } finally {
    submitting.value = false
  }
}

const editDialog = async (row: any) => {
  editForm.id = row.id
  editForm.name = row.name
  editForm.description = row.description || ''
  editForm.welcome_message = row.welcome_message || ''
  editForm.recommended_questions = row.recommended_questions || []
  editForm.custom_prompt = row.custom_prompt || ''
  editForm.knowledge_base_ids = row.knowledge_base_ids || []
  editForm.model_id = row.model_id || null
  editForm.language = row.language || 'zh'
  editForm.feedback_enabled = row.feedback_enabled || false
  editForm.is_active = row.is_active
  editForm.expires_at = row.expires_at
  showEditDialog.value = true
}

const submitEditForm = async () => {
  if (!editForm.name) {
    ElMessage.warning('请输入对话框名称')
    return
  }
  if (editForm.knowledge_base_ids.length === 0) {
    ElMessage.warning('请至少选择一个知识库')
    return
  }

  submitting.value = true
  try {
    const data = {
      name: editForm.name,
      description: editForm.description,
      welcome_message: editForm.welcome_message,
      recommended_questions: editForm.recommended_questions.filter(q => q.trim()),
      custom_prompt: editForm.custom_prompt,
      knowledge_base_ids: editForm.knowledge_base_ids,
      model_id: editForm.model_id,
      language: editForm.language,
      feedback_enabled: editForm.feedback_enabled,
      is_active: editForm.is_active,
      expires_at: editForm.expires_at
    }
    await request.put(`/public-dialog/${editForm.id}`, data)
    ElMessage.success('保存成功')
    showEditDialog.value = false
    loadDialogs()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    submitting.value = false
  }
}

const deleteDialog = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除这个公开对话吗？', '提示', {
      type: 'warning'
    })
    await request.delete(`/public-dialog/${row.id}`)
    ElMessage.success('删除成功')
    loadDialogs()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const resetForm = () => {
  form.name = ''
  form.description = ''
  form.welcome_message = '您好！有什么可以帮助您的？'
  form.recommended_questions = []
  form.custom_prompt = ''
  form.knowledge_base_ids = []
  form.model_id = null
  form.language = 'zh'
  form.feedback_enabled = false
  form.expires_at = null
}

onMounted(() => {
  loadDialogs()
  loadKnowledgeBases()
  loadModels()
})
</script>

<style scoped>
.layout-container {
  display: flex;
  min-height: 100vh;
  overflow: hidden;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #f8fafc 0%, #f0f6ff 100%);
  margin-left: 0;
  min-width: 0;
}

.main-content {
  flex: 1;
  padding: 36px;
  background: transparent;
  overflow-y: auto;
}

.public-dialog-management {
  background: white;
  border-radius: 12px;
  padding: 32px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.header-title h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  color: #303133;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  font-size: 13px;
  color: #909399;
}

.create-btn {
  background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);
  border: none;
  padding: 12px 24px;
  font-weight: 600;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
  transition: all 0.3s ease;
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.4);
}

.btn-icon {
  margin-right: 6px;
}

.custom-table {
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
}

.custom-table :deep(.el-table__header-wrapper) {
  background: #fafafa;
}

.custom-table :deep(th) {
  background: #fafafa !important;
  color: #595959;
  font-weight: 600;
  font-size: 14px;
}

.custom-table :deep(td) {
  padding: 16px 0;
}

.link-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dialog-link {
  font-size: 13px;
}

.status-tag {
  font-weight: 500;
}

.action-btn {
  margin: 0 4px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.dialog-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.custom-dialog .el-dialog__header) {
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 16px;
}

:deep(.custom-dialog .el-dialog__title) {
  font-weight: 600;
  color: #303133;
}
</style>
