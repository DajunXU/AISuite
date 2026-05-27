<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal db-config-modal">
      <div class="modal-header">
        <h3>添加数据源</h3>
        <button class="close-button" @click="close">×</button>
      </div>
      
      <div class="modal-body">
        <!-- 基础信息 -->
        <div class="form-section">
          <h4 class="section-title">基础信息</h4>
          
          <div class="form-group">
            <label class="form-label">
              数据源名称 <span class="required">*</span>
            </label>
            <input
              v-model="configForm.name"
              type="text"
              class="form-input"
              placeholder="生产环境MySQL（销售额库）"
            />
          </div>
          
          <div class="form-group">
            <label class="form-label">数据源类型 <span class="required">*</span></label>
            <select v-model="configForm.db_type" class="form-select" @change="onDbTypeChange">
              <option value="mysql">MySQL</option>
              <option value="postgresql">PostgreSQL</option>
              <option value="sqlserver">SQL Server</option>
              <option value="sqlite">SQLite</option>
            </select>
            <div class="form-help">支持MySQL/PostgreSQL/SQL Server等</div>
          </div>
          
          <div class="form-group">
            <label class="form-label">描述</label>
            <textarea
              v-model="configForm.description"
              class="form-textarea"
              placeholder="存储订单、客户、产品信息"
              rows="2"
            ></textarea>
          </div>
        </div>
        
        <!-- 连接信息 -->
        <div class="form-section">
          <h4 class="section-title">连接信息</h4>
          
          <div class="form-row">
            <div class="form-group flex-2">
              <label class="form-label">
                主机地址 <span class="required">*</span>
              </label>
              <input
                v-model="configForm.host"
                type="text"
                class="form-input"
                placeholder="192.168.1.100"
              />
            </div>
            
            <div class="form-group flex-1">
              <label class="form-label">
                端口 <span class="required">*</span>
              </label>
              <input
                v-model="configForm.port"
                type="number"
                class="form-input"
                :placeholder="defaultPort"
              />
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">
              数据库名 <span class="required">*</span>
            </label>
            <input
              v-model="configForm.database"
              type="text"
              class="form-input"
              placeholder="sales_db"
            />
          </div>
          
          <div class="form-row">
            <div class="form-group flex-1">
              <label class="form-label">
                用户名 <span class="required">*</span>
              </label>
              <input
                v-model="configForm.username"
                type="text"
                class="form-input"
                placeholder="readonly_user"
              />
            </div>
            
            <div class="form-group flex-1">
              <label class="form-label">
                密码 <span class="required">*</span>
              </label>
              <input
                v-model="configForm.password"
                type="password"
                class="form-input"
                placeholder="********"
              />
            </div>
          </div>
          
          <div class="form-group">
            <label class="form-label">Schema（可选）</label>
            <input
              v-model="configForm.schema_name"
              type="text"
              class="form-input"
              placeholder="public"
            />
          </div>
          
          <div class="warning-message">
            ⚠️ 建议使用只读账号，避免数据误操作
          </div>
        </div>
        
        <!-- 高级设置 -->
        <div class="form-section">
          <h4 class="section-title">高级设置</h4>
          
          <div class="form-row">
            <div class="form-group flex-1">
              <label class="form-label">连接池大小</label>
              <input
                v-model.number="configForm.pool_size"
                type="number"
                class="form-input"
                min="1"
                max="20"
              />
            </div>
            
            <div class="form-group flex-1">
              <label class="form-label">超时时间(s)</label>
              <input
                v-model.number="configForm.timeout"
                type="number"
                class="form-input"
                min="5"
                max="300"
              />
            </div>
            
            <div class="form-group flex-1">
              <label class="form-label">最大返回行数</label>
              <input
                v-model.number="configForm.max_rows"
                type="number"
                class="form-input"
                min="100"
                max="100000"
              />
              <div class="form-help">防止一次查询拖垮数据库</div>
            </div>
          </div>
        </div>
        
        <!-- 表选择 -->
        <div v-if="showTableSelection" class="form-section">
          <h4 class="section-title">表选择</h4>
          <p class="section-desc">勾选需要接入的表（后续可修改）</p>
          
          <div class="table-list">
            <div v-if="loadingTables" class="loading-state">
              <span class="loading-spinner"></span> 加载中...
            </div>
            <div v-else-if="availableTables.length === 0" class="empty-state">
              暂无表数据，请先测试连接
            </div>
            <div v-else>
              <div class="table-header">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="allTablesSelected" @change="handleSelectAllTables" />
                  <span>全选</span>
                </label>
              </div>
              <div v-for="table in availableTables" :key="table.table_name" class="table-item">
                <label class="checkbox-label">
                  <input type="checkbox" v-model="table.is_selected" />
                  <span class="table-name">{{ table.table_name }}</span>
                </label>
              </div>
            </div>
          </div>
          
          <div class="table-selection-actions">
            <button class="secondary-button" @click="resetTableSelection">重新选择表</button>
            <button class="primary-button" @click="saveTableSelection" :disabled="savingTables">
              {{ savingTables ? '保存中...' : '保存表选择' }}
            </button>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="form-actions">
          <button class="secondary-button" @click="close">取消</button>
          <button class="secondary-button" @click="testConnection" :disabled="testing || !canTest">
            {{ testing ? '测试中...' : '测试连接' }}
          </button>
          <button class="primary-button" @click="saveConnection" :disabled="saving || !canSave">
            {{ saving ? '保存中...' : (isEditMode ? '更新数据源' : '保存数据源') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'

interface Props {
  show: boolean
  knowledgeBase: any
  editingConnection?: any
}

interface Emits {
  (e: 'update:show', value: boolean): void
  (e: 'saved'): void
  (e: 'openMetadataConfig', data: { kbId: number; connId: number; tableName: string; connectionName: string }): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const configForm = ref({
  name: '',
  description: '',
  db_type: 'mysql',
  host: 'localhost',
  port: 3306,
  database: '',
  username: '',
  password: '',
  schema_name: 'public',
  pool_size: 5,
  timeout: 30,
  max_rows: 1000
})

const testing = ref(false)
const saving = ref(false)
const loadingTables = ref(false)
const availableTables = ref<any[]>([])
const showTableSelection = ref(false)
const savedConnectionId = ref<number | null>(null)
const savingTables = ref(false)
const allTablesSelected = ref(true)

const handleSelectAllTables = () => {
  availableTables.value.forEach(t => {
    t.is_selected = allTablesSelected.value
  })
}

const resetTableSelection = async () => {
  if (savedConnectionId.value) {
    loadingTables.value = true
    try {
      const tablesRes = await fetch(
        `/api/knowledge/${props.knowledgeBase.id}/database/connections/${savedConnectionId.value}/tables`,
        { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } }
      )
      if (tablesRes.ok) {
        const tablesData = await tablesRes.json()
        availableTables.value = (tablesData.tables || []).map((t: any) => ({
          table_name: t.table_name,
          is_selected: t.is_selected !== false
        }))
      }
    } catch (error) {
      console.error('加载表列表失败', error)
    } finally {
      loadingTables.value = false
    }
  }
}

const saveTableSelection = async () => {
  if (!savedConnectionId.value) {
    ElMessage.warning('请先保存数据源')
    return
  }
  
  const selectedTables = availableTables.value.filter(t => t.is_selected)
  if (selectedTables.length === 0) {
    ElMessage.warning('请至少选择一个表')
    return
  }
  
  savingTables.value = true
  try {
    const saveRes = await fetch(
      `/api/knowledge/${props.knowledgeBase.id}/database/connections/${savedConnectionId.value}/tables`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          tables: availableTables.value
        })
      }
    )
    
    if (saveRes.ok) {
      const saveData = await saveRes.json()
      
      ElMessage.success('表选择保存成功！')
      
      const firstSelected = (saveData.tables || []).find((t: any) => t.is_selected)
      if (firstSelected) {
        const shouldConfig = confirm('是否现在配置表元数据？这对智能问数准确性很重要！')
        if (shouldConfig) {
          emit('openMetadataConfig', {
            kbId: props.knowledgeBase.id,
            connId: savedConnectionId.value,
            tableId: firstSelected.id,
            tableName: firstSelected.table_name,
            connectionName: configForm.value.name
          })
          close()
          return
        }
      }
      
      emit('saved')
      close()
    } else {
      const err = await saveRes.json()
      throw new Error(err.detail || '保存失败')
    }
  } catch (error: any) {
    ElMessage.error(`保存失败: ${error.message}`)
  } finally {
    savingTables.value = false
  }
}

const defaultPort = computed(() => {
  const ports: Record<string, string> = {
    mysql: "3306",
    postgresql: "5432",
    sqlserver: "1433",
    sqlite: "0"
  }
  return ports[configForm.value.db_type] || "3306"
})

const canTest = computed(() => {
  return configForm.value.host && 
         configForm.value.database && 
         configForm.value.username
})

const canSave = computed(() => {
  return configForm.value.name && 
         configForm.value.host && 
         configForm.value.database && 
         configForm.value.username
})

const isEditMode = computed(() => !!props.editingConnection)

const onDbTypeChange = () => {
  configForm.value.port = Number(defaultPort.value)
}

const close = () => {
  emit('update:show', false)
}

const testConnection = async () => {
  testing.value = true
  try {
    const response = await fetch(`/api/knowledge/${props.knowledgeBase.id}/database/connections`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        ...configForm.value,
        knowledge_base_id: props.knowledgeBase.id,
        is_active: true
      })
    })
    
    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || '连接失败')
    }
    
    const connData = await response.json()
    
    // 获取表列表
    const tablesRes = await fetch(
      `/api/knowledge/${props.knowledgeBase.id}/database/connections/${connData.id}/tables`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    )
    
    if (tablesRes.ok) {
      const tablesData = await tablesRes.json()
      availableTables.value = (tablesData.tables || []).map((t: any) => ({
        table_name: t.table_name,
        is_selected: true
      }))
      showTableSelection.value = true
    }
    
    ElMessage.success('连接成功！请选择需要接入的表')
  } catch (error: any) {
    ElMessage.error(`连接失败: ${error.message}`)
    console.error(error)
  } finally {
    testing.value = false
  }
}

const saveConnection = async () => {
  if (!canSave.value) {
    ElMessage.warning('请填写必填字段')
    return
  }
  
  saving.value = true
  try {
    let connData: any
    
    if (isEditMode.value && savedConnectionId.value) {
      // 编辑模式：更新连接
      const connRes = await fetch(`/api/knowledge/${props.knowledgeBase.id}/database/connections/${savedConnectionId.value}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...configForm.value,
          knowledge_base_id: props.knowledgeBase.id,
          is_active: true
        })
      })
      
      if (!connRes.ok) {
        const err = await connRes.json()
        throw new Error(err.detail || '更新失败')
      }
      
      connData = await connRes.json()
      ElMessage.success('数据源更新成功！')
    } else {
      // 新增模式：创建连接
      const connRes = await fetch(`/api/knowledge/${props.knowledgeBase.id}/database/connections`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          ...configForm.value,
          knowledge_base_id: props.knowledgeBase.id,
          is_active: true
        })
      })
      
      if (!connRes.ok) {
        const err = await connRes.json()
        throw new Error(err.detail || '保存失败')
      }
      
      connData = await connRes.json()
      savedConnectionId.value = connData.id
      
      // 保存成功后，显示表选择区域
      ElMessage.success('数据源保存成功！请选择需要接入的表')
    }
    
    // 如果还没有加载表，则加载表列表
    if (availableTables.value.length === 0) {
      await loadTablesForEdit(savedConnectionId.value)
    }
    
    showTableSelection.value = true
  } catch (error: any) {
    ElMessage.error(`保存失败: ${error.message}`)
    console.error(error)
  } finally {
    saving.value = false
  }
}

// 监听编辑连接变化
watch(() => props.editingConnection, async (newVal) => {
  if (newVal && props.show && props.knowledgeBase) {
    configForm.value = {
      name: newVal.name || '',
      description: newVal.description || '',
      db_type: newVal.db_type || 'mysql',
      host: newVal.host || 'localhost',
      port: newVal.port || 3306,
      database: newVal.database || '',
      username: newVal.username || '',
      password: '',
      schema_name: newVal.schema_name || 'public',
      pool_size: newVal.pool_size || 5,
      timeout: newVal.timeout || 30,
      max_rows: newVal.max_rows || 1000
    }
    savedConnectionId.value = newVal.id
    // 加载已有表选择
    loadingTables.value = true
    try {
      const tablesRes = await fetch(
        `/api/knowledge/${props.knowledgeBase.id}/database/connections/${newVal.id}/tables`,
        { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } }
      )
      if (tablesRes.ok) {
        const tablesData = await tablesRes.json()
        availableTables.value = (tablesData.tables || []).map((t: any) => ({
          table_name: t.table_name,
          is_selected: t.is_selected !== false
        }))
        showTableSelection.value = true
      }
    } catch (error) {
      console.error('加载表列表失败', error)
    } finally {
      loadingTables.value = false
    }
  }
}, { immediate: true })

// 监听弹窗显示（仅在新打开时重置）
watch(() => props.show, (newVal) => {
  if (newVal && !props.editingConnection) {
    configForm.value = {
      name: '',
      description: '',
      db_type: 'mysql',
      host: 'localhost',
      port: 3306,
      database: '',
      username: '',
      password: '',
      schema_name: 'public',
      pool_size: 5,
      timeout: 30,
      max_rows: 1000
    }
    availableTables.value = []
    showTableSelection.value = false
    savedConnectionId.value = null
  }
})

const loadTablesForEdit = async (connId: number) => {
  loadingTables.value = true
  try {
    const tablesRes = await fetch(
      `/api/knowledge/${props.knowledgeBase.id}/database/connections/${connId}/tables`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    )
    
    if (tablesRes.ok) {
      const tablesData = await tablesRes.json()
      availableTables.value = (tablesData.tables || []).map((t: any) => ({
        table_name: t.table_name,
        is_selected: t.is_selected !== false
      }))
      showTableSelection.value = true
    }
  } catch (error) {
    console.error('加载表列表失败', error)
  } finally {
    loadingTables.value = false
  }
}

const loadTables = async () => {
  if (!savedConnectionId.value) return
  await loadTablesForEdit(savedConnectionId.value)
}
</script>

<style scoped>
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

.modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  color: #909399;
  cursor: pointer;
  line-height: 1;
}

.close-button:hover {
  color: #303133;
}

.modal-body {
  padding: 20px;
}

.db-config-modal {
  width: 700px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.form-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
}

.form-section:last-of-type {
  border-bottom: none;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.section-desc {
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
}

.form-row {
  display: flex;
  gap: 12px;
}

.flex-1 {
  flex: 1;
}

.flex-2 {
  flex: 2;
}

.required {
  color: #f56c6c;
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #409eff;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.warning-message {
  background: #fdf6ec;
  color: #e6a23c;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  margin-top: 8px;
}

.table-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 8px;
}

.table-item {
  padding: 6px 8px;
  border-bottom: 1px solid #f5f7fa;
}

.table-item:last-child {
  border-bottom: none;
}

.table-header {
  padding: 8px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 8px;
}

.table-selection-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.table-name {
  font-size: 13px;
  color: #303133;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 20px;
  color: #909399;
  font-size: 13px;
}

.loading-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #409eff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 6px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.primary-button,
.secondary-button {
  padding: 8px 20px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.primary-button {
  background: #409eff;
  color: white;
  border: none;
}

.primary-button:hover:not(:disabled) {
  background: #66b1ff;
}

.primary-button:disabled {
  background: #a0cfff;
  cursor: not-allowed;
}

.secondary-button {
  background: white;
  color: #606266;
  border: 1px solid #dcdfe6;
}

.secondary-button:hover:not(:disabled) {
  border-color: #409eff;
  color: #409eff;
}

.secondary-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
