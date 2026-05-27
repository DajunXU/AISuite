<template>
  <div class="kb-detail">
    <div class="layout-container">
      <Sidebar />
      
      <div class="main-container">
        <PageHeader title="知识库详情" />
        
        <main class="main-content">
          <!-- 顶部导航 -->
          <div class="detail-header">
            <button class="back-btn" @click="goBack">← 返回知识库列表</button>
            <div class="kb-title">
              <h2>{{ knowledgeBase?.name }}</h2>
              <span class="kb-type-badge" :class="knowledgeBase?.kb_type">
                {{ knowledgeBase?.kb_type === 'file' ? '📄 文件向量化' : '🗃️ 数据库连接' }}
              </span>
            </div>
          </div>

          <!-- 知识库描述 -->
          <div class="kb-description" v-if="knowledgeBase?.description">
            {{ knowledgeBase.description }}
          </div>

          <!-- 统计信息 -->
          <div v-if="knowledgeBase?.kb_type === 'file'" class="stats-section">
            <div class="stat-card">
              <div class="stat-value">{{ stats.total_files }}</div>
              <div class="stat-label">总文件数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ stats.total_chunks }}</div>
              <div class="stat-label">文本块数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ stats.total_vectors }}</div>
              <div class="stat-label">向量数</div>
            </div>
            <div class="stat-card success">
              <div class="stat-value">{{ stats.processed_files }}</div>
              <div class="stat-label">已处理</div>
            </div>
            <div class="stat-card error" v-if="stats.error_files > 0">
              <div class="stat-value">{{ stats.error_files }}</div>
              <div class="stat-label">处理失败</div>
            </div>
          </div>

          <!-- 文件类型知识库 -->
          <div v-if="knowledgeBase?.kb_type === 'file'" class="content-section">
            <div class="section-header">
              <h3>📄 已上传文件</h3>
              <button class="primary-button" @click="showUploadDialog = true">+ 上传文件</button>
            </div>
            
            <div v-if="loading" class="loading-state">
              加载中...
            </div>
            
            <div v-else-if="files.length === 0" class="empty-state">
              <p>暂无上传文件</p>
              <button class="secondary-button" @click="showUploadDialog = true">上传第一个文件</button>
            </div>
            
            <div v-else class="file-table">
              <table>
                <thead>
                  <tr>
                    <th>文件名</th>
                    <th>大小</th>
                    <th>状态</th>
                    <th>上传时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="file in files" :key="file.id">
                    <td class="file-name">{{ file.original_filename }}</td>
                    <td>{{ formatFileSize(file.file_size) }}</td>
                    <td>
                      <span class="status-badge" :class="file.status">{{ file.status }}</span>
                    </td>
                    <td>{{ formatDate(file.created_at) }}</td>
                    <td>
                      <button class="danger-text-btn" @click="deleteFile(file)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 数据库类型知识库 -->
          <div v-if="knowledgeBase?.kb_type === 'db'" class="content-section">
            <div class="section-header">
              <h3>🗃️ 已配置数据源</h3>
              <button v-if="dbConnections.length === 0" class="primary-button" @click="showDbConfigDialog = true">+ 添加数据源</button>
              <span v-else class="hint-text">数据库知识库只能添加一个数据源</span>
            </div>
            
            <div v-if="loading" class="loading-state">
              加载中...
            </div>
            
            <div v-else-if="dbConnections.length === 0" class="empty-state">
              <p>暂无配置的数据源</p>
              <button class="secondary-button" @click="showDbConfigDialog = true">添加第一个数据源</button>
            </div>
            
            <div v-else class="db-list">
              <div v-for="conn in dbConnections" :key="conn.id" class="db-card">
                <div class="db-card-header">
                  <div class="db-info">
                    <span class="db-name">{{ conn.name || conn.database }}</span>
                    <span class="db-type-badge">{{ conn.db_type }}</span>
                  </div>
                  <div class="db-actions">
                    <button class="text-btn" @click="configTable(conn)">配置表</button>
                    <button class="text-btn" @click="editDbConnection(conn)">编辑</button>
                    <button class="danger-text-btn" @click="deleteDbConnection(conn)">删除</button>
                  </div>
                </div>
                <div class="db-card-body">
                  <p><strong>主机：</strong>{{ conn.host }}:{{ conn.port }}</p>
                  <p><strong>数据库：</strong>{{ conn.database }}</p>
                  <p v-if="conn.description"><strong>描述：</strong>{{ conn.description }}</p>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>

    <!-- 文件上传对话框 -->
    <FileUploadDialog
      v-if="showUploadDialog"
      :show="showUploadDialog"
      :knowledge-base="knowledgeBase"
      @update:show="showUploadDialog = $event"
      @uploaded="onFileUploaded"
    />

    <!-- 数据库配置对话框 -->
    <DatabaseConfigDialog
      v-if="showDbConfigDialog"
      :show="showDbConfigDialog"
      :knowledge-base="knowledgeBase"
      :editing-connection="selectedConnectionForEdit"
      @update:show="showDbConfigDialog = $event; selectedConnectionForEdit = null"
      @saved="onDbConfigSaved"
      @open-metadata-config="openTableMetadataConfig"
    />

    <!-- 表元数据配置对话框 -->
    <TableMetadataConfigDialog
      v-if="showTableMetadataDialog"
      :show="showTableMetadataDialog"
      :knowledge-base-id="selectedTableConfig.knowledgeBaseId"
      :connection-id="selectedTableConfig.connectionId"
      :table-id="selectedTableConfig.tableId"
      :table-name="selectedTableConfig.tableName"
      :connection-name="selectedTableConfig.connectionName"
      @update:show="showTableMetadataDialog = $event"
      @saved="onTableMetadataSaved"
    />

    <TableSelectDialog
      :show="showTableSelectDialog"
      :tables="tableListForSelect"
      @update:show="showTableSelectDialog = $event"
      @select="handleTableSelected"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import FileUploadDialog from '@/components/FileUploadDialog.vue'
import DatabaseConfigDialog from '@/components/DatabaseConfigDialog.vue'
import TableMetadataConfigDialog from '@/components/TableMetadataConfigDialog.vue'
import TableSelectDialog from '@/components/TableSelectDialog.vue'
import Sidebar from '@/components/Sidebar.vue'
import PageHeader from '@/components/PageHeader.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const navigate = (path: string) => {
  window.location.href = path
}

const knowledgeBase = ref<any>(null)
const files = ref<any[]>([])
const dbConnections = ref<any[]>([])
const loading = ref(true)
const stats = ref({
  total_files: 0,
  total_chunks: 0,
  total_vectors: 0,
  processed_files: 0,
  error_files: 0
})

const showUploadDialog = ref(false)
const showDbConfigDialog = ref(false)
const showTableMetadataDialog = ref(false)
const selectedConnectionForEdit = ref<any>(null)

const selectedTableConfig = ref({
  knowledgeBaseId: 0,
  connectionId: 0,
  tableId: 0,
  tableName: '',
  connectionName: ''
})

const kbId = Number(route.params.id)

onMounted(async () => {
  await loadKnowledgeBase()
  await loadFiles()
  await loadStats()
  await loadDbConnections()
})

const loadKnowledgeBase = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`/api/knowledge/${kbId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (response.ok) {
      knowledgeBase.value = await response.json()
    }
  } catch (error) {
    console.error('加载知识库失败', error)
  }
}

const loadFiles = async () => {
  if (knowledgeBase.value?.kb_type !== 'file') {
    loading.value = false
    return
  }
  
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`/api/knowledge/${kbId}/files`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (response.ok) {
      files.value = await response.json()
    }
  } catch (error) {
    console.error('加载文件列表失败', error)
    files.value = []
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  if (knowledgeBase.value?.kb_type !== 'file') return
  
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`/api/knowledge/${kbId}/stats`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (response.ok) {
      const data = await response.json()
      stats.value = {
        total_files: data.total_files,
        total_chunks: data.total_chunks,
        total_vectors: data.total_vectors,
        processed_files: data.processed_files,
        error_files: data.error_files
      }
    }
  } catch (error) {
    console.error('加载统计信息失败', error)
  }
}

const loadDbConnections = async () => {
  if (knowledgeBase.value?.kb_type !== 'db') return
  
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`/api/knowledge/${kbId}/database/connections`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (response.ok) {
      dbConnections.value = await response.json()
    }
  } catch (error) {
    console.error('加载数据库连接失败', error)
    dbConnections.value = []
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/knowledge')
}

const formatFileSize = (bytes: number) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(1)} ${units[i]}`
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

const deleteFile = async (file: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除文件 "${file.original_filename}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const token = localStorage.getItem('token')
    const response = await fetch(`/api/knowledge/${kbId}/files/${file.id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    if (response.ok) {
      ElMessage.success('文件删除成功')
      loadFiles()
    } else {
      const err = await response.json()
      ElMessage.error(err.detail || '删除失败')
    }
  } catch (e) {
    // 用户取消
  }
}

const onFileUploaded = () => {
  ElMessage.success('文件上传成功')
  showUploadDialog.value = false
  loadFiles()
}

const showTableSelectDialog = ref(false)
const tableListForSelect = ref<any[]>([])
const currentConnForConfig = ref<any>(null)

const handleTableSelected = (table: any) => {
  selectedTableConfig.value = {
    knowledgeBaseId: kbId,
    connectionId: currentConnForConfig.value.id,
    tableId: table.id,
    tableName: table.table_name,
    connectionName: currentConnForConfig.value.name || currentConnForConfig.value.database
  }
  showTableMetadataDialog.value = true
}

const configTable = async (conn: any) => {
  try {
    currentConnForConfig.value = conn
    const token = localStorage.getItem('token')
    const response = await fetch(
      `/api/knowledge/${kbId}/database/connections/${conn.id}/tables`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    )
    
    if (response.ok) {
      const data = await response.json()
      if (data.tables && data.tables.length > 0) {
        tableListForSelect.value = data.tables
        showTableSelectDialog.value = true
      } else {
        ElMessage.warning('暂无已配置的表，请先在数据源中添加表')
      }
    }
  } catch (error) {
    console.error('获取表列表失败', error)
  }
}

const editDbConnection = (conn: any) => {
  selectedConnectionForEdit.value = conn
  showDbConfigDialog.value = true
}

const deleteDbConnection = async (conn: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除数据源 "${conn.name || conn.database}" 吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const token = localStorage.getItem('token')
    const response = await fetch(`/api/knowledge/${kbId}/database/connections/${conn.id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    
    if (response.ok) {
      ElMessage.success('数据源删除成功')
      loadDbConnections()
    } else {
      const err = await response.json()
      ElMessage.error(err.detail || '删除失败')
    }
  } catch (e) {
    // 用户取消
  }
}

const onDbConfigSaved = () => {
  ElMessage.success('数据源保存成功')
  showDbConfigDialog.value = false
  loadDbConnections()
}

const openTableMetadataConfig = (data: any) => {
  selectedTableConfig.value = {
    knowledgeBaseId: data.kbId,
    connectionId: data.connId,
    tableId: data.tableId,
    tableName: data.tableName,
    connectionName: data.connectionName
  }
  showTableMetadataDialog.value = true
}

const onTableMetadataSaved = () => {
  showTableMetadataDialog.value = false
  loadDbConnections()
}
</script>

<style scoped>
.kb-detail {
  min-height: 100vh;
}

.layout-container {
  display: flex;
  min-height: 100vh;
  overflow: hidden;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #f0f0f0;
  padding: 0 36px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.header-left h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #262626;
  letter-spacing: -0.5px;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  position: relative;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.user-info:hover {
  background: #f5f5f5;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #1890ff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
}

.user-name {
  font-size: 14px;
  color: #333;
}

.dropdown-arrow {
  font-size: 10px;
  color: #999;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  display: none;
  min-width: 120px;
}

.user-dropdown:hover .dropdown-menu {
  display: block;
}

.dropdown-item {
  display: block;
  padding: 8px 16px;
  color: #333;
  text-decoration: none;
  font-size: 14px;
}

.dropdown-item:hover {
  background: #f5f5f5;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.back-btn {
  padding: 8px 16px;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.back-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.kb-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.kb-title h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.kb-type-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

.kb-type-badge.file {
  background: #e6f7ff;
  color: #1890ff;
}

.kb-type-badge.db {
  background: #f6ffed;
  color: #52c41a;
}

.kb-description {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  color: #606266;
  font-size: 14px;
}

.stats-section {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  background: white;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.stat-card .stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.stat-card .stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.stat-card.success .stat-value {
  color: #67c23a;
}

.stat-card.error .stat-value {
  color: #f56c6c;
}

.content-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.primary-button {
  padding: 8px 20px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.primary-button:hover {
  background: #66b1ff;
}

.secondary-button {
  padding: 8px 20px;
  background: white;
  color: #606266;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.secondary-button:hover {
  border-color: #409eff;
  color: #409eff;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.empty-state p {
  margin-bottom: 16px;
}

.file-table table {
  width: 100%;
  border-collapse: collapse;
}

.file-table th,
.file-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.file-table th {
  background: #f5f7fa;
  font-weight: 500;
  color: #606266;
  font-size: 14px;
}

.file-table td {
  color: #303133;
  font-size: 14px;
}

.file-name {
  font-weight: 500;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.processing {
  background: #fdf6ec;
  color: #e6a23c;
}

.status-badge.completed {
  background: #f0f9eb;
  color: #67c23a;
}

.status-badge.error {
  background: #fef0f0;
  color: #f56c6c;
}

.text-btn {
  background: none;
  border: none;
  color: #409eff;
  cursor: pointer;
  font-size: 13px;
  padding: 4px 8px;
}

.text-btn:hover {
  text-decoration: underline;
}

.danger-text-btn {
  background: none;
  border: none;
  color: #f56c6c;
  cursor: pointer;
  font-size: 13px;
  padding: 4px 8px;
}

.danger-text-btn:hover {
  text-decoration: underline;
}

.db-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.db-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.db-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.db-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.db-name {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.db-type-badge {
  padding: 2px 8px;
  background: #409eff;
  color: white;
  border-radius: 4px;
  font-size: 12px;
}

.db-actions {
  display: flex;
  gap: 8px;
}

.db-card-body {
  padding: 16px;
}

.db-card-body p {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #606266;
}

.db-card-body p:last-child {
  margin-bottom: 0;
}
</style>
