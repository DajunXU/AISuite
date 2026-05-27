<template>
  <div class="knowledge-base">
    <div class="layout-container">
      <Sidebar />
      
      <div class="main-container">
        <PageHeader title="知识库管理" />
        
        <main class="main-content">
          <div class="knowledge-base-container">
            <div class="page-header">
              <div class="header-actions">
                <button 
                  v-if="selectedKnowledgeBases.length > 0" 
                  class="secondary-button" 
                  @click="toggleSelectAll"
                >
                  {{ selectedKnowledgeBases.length === knowledgeBases.length ? '取消全选' : '全选' }}
                </button>
                <button 
                  v-if="selectedKnowledgeBases.length > 0" 
                  class="danger-button" 
                  @click="batchDelete"
                >
                  批量删除 ({{ selectedKnowledgeBases.length }})
                </button>
                <button class="primary-button" @click="showCreateDialog = true">
                  <span class="button-icon">+</span>
                  创建知识库
                </button>
              </div>
            </div>
            
            <!-- 知识库列表 -->
            <div class="knowledge-list">
              <div class="knowledge-grid">
                <div
                  v-for="kb in knowledgeBases"
                  :key="kb.id"
                  class="knowledge-card"
                >
                  <div class="card-header">
                    <input 
                      type="checkbox" 
                      :checked="selectedKnowledgeBases.includes(kb.id)"
                      @change="toggleSelect(kb.id)"
                      @click.stop
                      class="kb-checkbox"
                    />
                    <h4 @click="viewKnowledgeBase(kb)" class="kb-name-clickable">{{ kb.name }}</h4>
                    <div class="card-actions">
                    <div class="dropdown">
                      <button class="dropdown-trigger">⋯</button>
                      <div class="dropdown-menu">
                        <button class="dropdown-item" @click="editKnowledgeBase(kb)">编辑</button>
                        <button v-if="kb.kb_type === 'file'" class="dropdown-item" @click="uploadDocument(kb)">上传文档</button>
                        <button v-if="kb.kb_type === 'db'" class="dropdown-item" @click="configureDatabase(kb)">配置数据库</button>
                        <button v-if="kb.kb_type === 'db'" class="dropdown-item" @click="viewSampleData(kb)">查看数据</button>
                        <button class="dropdown-item danger" @click="deleteKnowledgeBase(kb)">删除</button>
                      </div>
                    </div>
                  </div>
                  </div>
                  
                  <div class="card-content">
                    <p class="description">{{ kb.description || '暂无描述' }}</p>
                    
                    <div class="card-info">
                      <span class="kb-type" :class="kb.kb_type">
                        {{ kb.kb_type === 'file' ? '📄 文件向量化' : '🗃️ 数据库连接' }}
                      </span>
                      <span class="document-count" v-if="kb.kb_type === 'file'">
                        📄 {{ kb.files ? kb.files.length : 0 }} 个文档
                      </span>
                      <span class="document-count" v-if="kb.kb_type === 'db'">
                        🗃️ {{ kb.db_connections ? kb.db_connections.length : 0 }} 个数据源
                      </span>
                      <span class="visibility" :class="kb.is_public ? 'public' : 'private'">
                        {{ kb.is_public ? '公开' : '私有' }}
                      </span>
                      <span class="create-time">创建时间: {{ formatDate(kb.created_at) }}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-if="knowledgeBases.length === 0" class="empty-state">
                <div class="empty-content">
                  <div class="empty-icon">📁</div>
                  <p class="empty-text">暂无知识库</p>
                  <button class="primary-button" @click="showCreateDialog = true">创建第一个知识库</button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
    
    <!-- 创建/编辑知识库对话框 -->
    <div v-if="showCreateDialog" class="modal-overlay">
      <div class="modal">
        <div class="modal-header">
          <h3>{{ editingKnowledgeBase ? '编辑知识库' : '创建知识库' }}</h3>
          <button class="close-button" @click="closeModal">×</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">名称</label>
            <input
              v-model="knowledgeBaseForm.name"
              type="text"
              class="form-input"
              placeholder="请输入知识库名称"
            />
          </div>
          
          <div class="form-group">
            <label class="form-label">描述</label>
            <textarea
              v-model="knowledgeBaseForm.description"
              class="form-textarea"
              placeholder="请输入知识库描述"
              rows="3"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label class="form-label">知识库类型</label>
            <div class="radio-group">
              <label class="radio-label">
                <input
                  type="radio"
                  v-model="knowledgeBaseForm.kb_type"
                  value="file"
                  class="radio-input"
                />
                <span class="radio-text">文件向量化</span>
                <span class="radio-description">上传文档文件，进行向量化处理</span>
              </label>
              <label class="radio-label">
                <input
                  type="radio"
                  v-model="knowledgeBaseForm.kb_type"
                  value="db"
                  class="radio-input"
                />
                <span class="radio-text">数据库连接</span>
                <span class="radio-description">连接外部数据库，直接查询数据</span>
              </label>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">可见性</label>
            <div class="radio-group">
              <label class="radio-label">
                <input
                  type="radio"
                  v-model="knowledgeBaseForm.is_public"
                  :value="true"
                  class="radio-input"
                />
                <span class="radio-text">公开</span>
              </label>
              <label class="radio-label">
                <input
                  type="radio"
                  v-model="knowledgeBaseForm.is_public"
                  :value="false"
                  class="radio-input"
                />
                <span class="radio-text">私有</span>
              </label>
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">向量模型</label>
            <select
              v-model="knowledgeBaseForm.embedding_model_id"
              class="form-select"
            >
              <option :value="null">请选择向量模型</option>
              <option
                v-for="model in embeddingModels"
                :key="model.id"
                :value="model.id"
              >
                {{ model.name }} ({{ model.provider }} - {{ model.model_name }})
              </option>
            </select>
            <p class="form-help">选择用于文档向量化的模型，不同模型的向量维度可能不同</p>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="secondary-button" @click="closeModal">取消</button>
          <button class="primary-button" @click="saveKnowledgeBase" :disabled="saving">
            <span v-if="saving" class="loading-spinner"></span>
            {{ editingKnowledgeBase ? '更新' : '创建' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 数据库配置对话框 -->
    <DatabaseConfigDialog
      v-model:show="showDatabaseConfigDialog"
      :knowledge-base="selectedKnowledgeBase"
      @saved="onDatabaseConfigSaved"
      @open-metadata-config="openTableMetadataConfig"
    />
    
    <!-- 表元数据配置对话框 -->
    <TableMetadataConfigDialog
      v-model:show="showTableMetadataDialog"
      :knowledge-base-id="selectedTableConfig.knowledgeBaseId"
      :connection-id="selectedTableConfig.connectionId"
      :table-id="selectedTableConfig.tableId"
      :table-name="selectedTableConfig.tableName"
      :connection-name="selectedTableConfig.connectionName"
      @saved="onTableMetadataSaved"
    />
    
    <!-- 文件上传对话框 -->
    <FileUploadDialog
      v-model:show="showFileUploadDialog"
      :knowledge-base="selectedKnowledgeBase"
      @uploaded="onFileUploaded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useKnowledgeStore } from '@/stores/knowledge'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import DatabaseConfigDialog from '@/components/DatabaseConfigDialog.vue'
import TableMetadataConfigDialog from '@/components/TableMetadataConfigDialog.vue'
import FileUploadDialog from '@/components/FileUploadDialog.vue'
import Sidebar from '@/components/Sidebar.vue'
import PageHeader from '@/components/PageHeader.vue'

const router = useRouter()
const knowledgeStore = useKnowledgeStore()
const userStore = useUserStore()

// 响应式数据
const knowledgeBases = ref<any[]>([])
const selectedKnowledgeBases = ref<number[]>([])
const showCreateDialog = ref(false)
const showDatabaseConfigDialog = ref(false)
const showFileUploadDialog = ref(false)
const showTableMetadataDialog = ref(false)
const editingKnowledgeBase = ref<any>(null)
const selectedKnowledgeBase = ref<any>(null)
const selectedTableConfig = ref({
  knowledgeBaseId: 0,
  connectionId: 0,
  tableId: 0,
  tableName: '',
  connectionName: ''
})
const saving = ref(false)
const embeddingModels = ref<any[]>([])

const knowledgeBaseForm = ref({
  name: '',
  description: '',
  kb_type: 'file',
  is_public: false,
  embedding_model_id: null as number | null
})

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadKnowledgeBases(),
    loadEmbeddingModels()
  ])
})

// 方法
const loadEmbeddingModels = async () => {
  try {
    const response = await knowledgeStore.getEmbeddingModels()
    embeddingModels.value = response.models || response || []
  } catch (error) {
    console.error('加载向量模型列表失败:', error)
    embeddingModels.value = []
  }
}

const loadKnowledgeBases = async () => {
  try {
    const result = await knowledgeStore.getKnowledgeBases()
    knowledgeBases.value = Array.isArray(result) ? result : (result.data || [])
    
    // 为每个知识库加载相应的数据
    for (const kb of knowledgeBases.value) {
      if (kb.kb_type === 'file') {
        try {
          kb.files = await knowledgeStore.getKnowledgeBaseFiles(kb.id)
        } catch (error) {
          console.error(`加载知识库 ${kb.name} 的文件列表失败:`, error)
          kb.files = []
        }
      } else if (kb.kb_type === 'db') {
        // 为数据库类型的知识库加载连接信息
        try {
          const token = localStorage.getItem('token')
          const response = await fetch(`/api/knowledge/${kb.id}/database/connections`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          if (response.ok) {
            kb.db_connections = await response.json()
          }
        } catch (error) {
          console.error(`加载知识库 ${kb.name} 的数据库连接失败:`, error)
          kb.db_connections = []
        }
      }
    }
  } catch (error) {
    ElMessage.error('加载知识库失败')
    console.error(error)
  }
}

const editKnowledgeBase = (kb: any) => {
  editingKnowledgeBase.value = kb
  knowledgeBaseForm.value = {
    name: kb.name,
    description: kb.description || '',
    kb_type: kb.kb_type || 'file',
    is_public: kb.is_public,
    embedding_model_id: kb.embedding_model_id || null
  }
  showCreateDialog.value = true
}

const uploadDocument = (kb: any) => {
  selectedKnowledgeBase.value = kb
  showFileUploadDialog.value = true
}

const configureDatabase = async (kb: any) => {
  selectedKnowledgeBase.value = kb
  
  // 获取数据库连接
  try {
    const response = await fetch(`/api/knowledge/${kb.id}/database/connections`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      const connections = await response.json()
      
      if (connections && connections.length > 0) {
        const conn = connections[0]
        
        // 获取表元数据
        const tablesRes = await fetch(
          `/api/knowledge/${kb.id}/database/connections/${conn.id}/tables`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
          }
        )
        
        if (tablesRes.ok) {
          const tablesData = await tablesRes.json()
          
          // 如果有已保存的表配置，显示选择界面
          if (tablesData.tables && tablesData.tables.length > 0) {
            // 让用户选择要配置元数据的表
            const tableNames = tablesData.tables.map((t: any) => t.table_name).join('\n')
            const selectedTable = prompt(`请输入要配置元数据的表名：\n可用表：\n${tableNames}`)
            
            if (selectedTable) {
              const tableInfo = tablesData.tables.find((t: any) => t.table_name === selectedTable)
              if (tableInfo) {
                selectedTableConfig.value = {
                  knowledgeBaseId: kb.id,
                  connectionId: conn.id,
                  tableId: tableInfo.id || 0,
                  tableName: tableInfo.table_name,
                  connectionName: conn.name || conn.database
                }
                showTableMetadataDialog.value = true
              } else {
                ElMessage.warning('表名不存在')
              }
            }
            return
          }
        }
      }
    }
  } catch (error) {
    console.error('获取连接失败', error)
  }
  
  // 没有配置时，打开添加数据源对话框
  showDatabaseConfigDialog.value = true
}

const viewSampleData = (kb: any) => {
  ElMessage.info(`查看数据库样例数据: ${kb.name}`)
}

const onDatabaseConfigSaved = () => {
  ElMessage.success('数据库配置保存成功')
  loadKnowledgeBases()
  showDatabaseConfigDialog.value = false
}

const openTableMetadataConfig = (data: { kbId: number; connId: number; tableName: string; connectionName: string }) => {
  selectedTableConfig.value = {
    knowledgeBaseId: data.kbId,
    connectionId: data.connId,
    tableId: 0,
    tableName: data.tableName,
    connectionName: data.connectionName
  }
  showTableMetadataDialog.value = true
}

const onTableMetadataSaved = () => {
  ElMessage.success('元数据配置保存成功')
  loadKnowledgeBases()
}

const onFileUploaded = () => {
  ElMessage.success('文件上传成功')
  showFileUploadDialog.value = false
  // 重新加载知识库以更新文件列表
  loadKnowledgeBases()
}

const saveKnowledgeBase = async () => {
  if (!knowledgeBaseForm.value.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }

  saving.value = true
  
  try {
    if (editingKnowledgeBase.value) {
      await knowledgeStore.updateKnowledgeBase(editingKnowledgeBase.value.id, knowledgeBaseForm.value)
    } else {
      await knowledgeStore.createKnowledgeBase(knowledgeBaseForm.value)
    }
    
    showCreateDialog.value = false
    resetForm()
    ElMessage.success(editingKnowledgeBase.value ? '更新成功' : '创建成功')
    await loadKnowledgeBases()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || (editingKnowledgeBase.value ? '更新失败' : '创建失败'))
    console.error(error)
  } finally {
    saving.value = false
  }
}

const viewKnowledgeBase = (kb: any) => {
  router.push(`/knowledge/${kb.id}`)
}

const deleteKnowledgeBase = async (kb: any) => {
  if (!confirm('确定要删除这个知识库吗？')) {
    return
  }
  
  try {
    await knowledgeStore.deleteKnowledgeBase(kb.id)
    ElMessage.success('删除成功')
    await loadKnowledgeBases()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

const toggleSelectAll = () => {
  if (selectedKnowledgeBases.value.length === knowledgeBases.value.length) {
    selectedKnowledgeBases.value = []
  } else {
    selectedKnowledgeBases.value = knowledgeBases.value.map(kb => kb.id)
  }
}

const toggleSelect = (kbId: number) => {
  const index = selectedKnowledgeBases.value.indexOf(kbId)
  if (index === -1) {
    selectedKnowledgeBases.value.push(kbId)
  } else {
    selectedKnowledgeBases.value.splice(index, 1)
  }
}

const batchDelete = async () => {
  if (selectedKnowledgeBases.value.length === 0) {
    ElMessage.warning('请先选择要删除的知识库')
    return
  }
  
  if (!confirm(`确定要删除选中的 ${selectedKnowledgeBases.value.length} 个知识库吗？`)) {
    return
  }
  
  try {
    await knowledgeStore.batchDeleteKnowledgeBases(selectedKnowledgeBases.value)
    ElMessage.success('批量删除成功')
    selectedKnowledgeBases.value = []
    await loadKnowledgeBases()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
    console.error(error)
  }
}

const closeModal = () => {
  showCreateDialog.value = false
  resetForm()
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const resetForm = () => {
  knowledgeBaseForm.value = {
    name: '',
    description: '',
    kb_type: 'file',
    is_public: false
  }
  editingKnowledgeBase.value = null
}
</script>

<style scoped>
/* bigmodel.cn 风格 - 清新现代 */
.knowledge-base {
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
  overflow: hidden;
}

/* 主内容区 */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.header {
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
  padding: 0 36px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--shadow-sm);
}

.header-left h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.3px;
}

.user-dropdown {
  position: relative;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 14px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.user-info:hover {
  background: var(--color-bg-hover);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-accent), var(--color-accent-hover));
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.dropdown-arrow {
  font-size: 10px;
  color: var(--color-text-muted);
  transition: transform var(--transition-normal);
}

.user-dropdown:hover .dropdown-arrow {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  padding: 8px;
  min-width: 120px;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all var(--transition-normal);
  z-index: 100;
}

.user-dropdown:hover .dropdown-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.dropdown-item {
  width: 100%;
  padding: 10px 14px;
  border: none;
  background: none;
  text-align: left;
  border-radius: var(--radius-sm);
  font-size: 14px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.dropdown-item:hover {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
}

.main-content {
  flex: 1;
  padding: 32px;
  background: transparent;
  overflow-y: auto;
}

.knowledge-base-container {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.header-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.primary-button {
  background: var(--color-accent);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-normal);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.danger-button {
  background: var(--color-error);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-normal);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.danger-button:hover {
  background: #dc2626;
}

.primary-button:hover {
  background: var(--color-accent-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.primary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.button-icon {
  font-size: 16px;
}

.secondary-button {
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  padding: 10px 20px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.secondary-button:hover {
  background: var(--color-bg-hover);
  border-color: var(--color-text-muted);
}

/* 知识库网格 - 智谱风格 */
.knowledge-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.knowledge-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-normal);
  overflow: hidden;
}

.knowledge-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-accent-light);
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border-light);
  display: flex;
  align-items: center;
  gap: 12px;
}

.card-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.2px;
  flex: 1;
}

.kb-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.kb-name-clickable {
  cursor: pointer;
}

.kb-name-clickable:hover {
  color: var(--color-accent);
}

.card-actions {
  position: relative;
}

.dropdown-trigger {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 6px;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
}

.dropdown-trigger:hover {
  background: var(--color-bg-hover);
  color: var(--color-accent);
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
  min-width: 140px;
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: all 0.3s ease;
}

.dropdown:hover .dropdown-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  border: none;
  background: none;
  text-align: left;
  cursor: pointer;
  color: #475569;
  font-size: 14px;
  transition: background 0.2s ease;
}

.dropdown-item:hover {
  background: #f1f5f9;
  color: #1e293b;
}

.dropdown-item.danger {
  color: #dc2626;
}

.dropdown-item.danger:hover {
  background: #fef2f2;
  color: #dc2626;
}

.card-content {
  padding: 20px 24px;
}

.description {
  margin: 0 0 16px 0;
  color: #64748b;
  line-height: 1.6;
  font-size: 14px;
}

/* 文件列表样式 */
.file-list {
  margin: 16px 0;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

/* 数据库连接信息样式 */
.db-info {
  margin: 16px 0;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.db-info h5 {
  margin: 0;
  padding: 12px 16px;
  background: #f8fafc;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  border-bottom: 1px solid #e2e8f0;
}

.db-item {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.db-item:last-child {
  border-bottom: none;
}

.db-info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.db-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.db-type-badge {
  padding: 2px 8px;
  background: #409eff;
  color: white;
  border-radius: 4px;
  font-size: 12px;
}

.db-detail {
  font-size: 12px;
  color: #909399;
}

.file-list h5 {
  margin: 0;
  padding: 12px 16px;
  background: #f8fafc;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  border-bottom: 1px solid #e2e8f0;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.file-size {
  font-size: 12px;
  color: #6b7280;
}

.file-status {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.file-status.uploaded {
  background: #d1fae5;
  color: #065f46;
}

.file-status.processing {
  background: #fef3c7;
  color: #92400e;
}

.file-status.processed {
  background: #dbeafe;
  color: #1e40af;
}

.file-status.error {
  background: #fee2e2;
  color: #991b1b;
}

.card-info {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
  font-size: 13px;
  color: #64748b;
}

.kb-type {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.kb-type.file {
  background: #dbeafe;
  color: #1e40af;
}

.kb-type.db {
  background: #fef3c7;
  color: #92400e;
}

.document-count {
  display: flex;
  align-items: center;
  gap: 4px;
}

.visibility {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.visibility.public {
  background: #dcfce7;
  color: #166534;
}

.visibility.private {
  background: #f3f4f6;
  color: #6b7280;
}

.create-time {
  color: #9ca3af;
}

/* 空状态 */
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 20px;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.empty-icon {
  font-size: 64px;
  opacity: 0.3;
}

.empty-text {
  color: #64748b;
  font-size: 16px;
  font-weight: 500;
}

/* 模态框 */
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
  backdrop-filter: blur(4px);
}

.modal {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: auto;
  border: 1px solid #e2e8f0;
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: -0.3px;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #64748b;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #374151;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #374151;
  font-size: 14px;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s ease;
  box-sizing: border-box;
  font-family: inherit;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.form-select {
  width: 100%;
  padding: 10px 32px 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  background: #fafafa;
  color: #333;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23999' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  transition: all 0.2s ease;
  box-sizing: border-box;
  font-family: inherit;
}

.form-select:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
  background-color: #fff;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.radio-label {
  display: flex;
  align-items: flex-start;
  cursor: pointer;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.radio-label:hover {
  border-color: #1890ff;
  background-color: #f8fafc;
}

.radio-label:has(.radio-input:checked) {
  border-color: #1890ff;
  background-color: #f0f6ff;
}

.radio-input {
  margin: 0;
  margin-top: 2px;
}

.radio-text {
  font-size: 14px;
  color: #374151;
}

.radio-description {
  display: block;
  margin-left: 24px;
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.modal-footer {
  padding: 20px 24px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.secondary-button {
  background: #f8fafc;
  color: #374151;
  border: 1px solid #e2e8f0;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.secondary-button:hover {
  background: #f1f5f9;
  border-color: #d1d5db;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .knowledge-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .knowledge-grid {
    grid-template-columns: 1fr;
  }
  
  .main-content {
    padding: 20px;
  }
  
  .sidebar {
    width: 240px;
  }
  
  .header {
    padding: 0 20px;
  }
}
</style>