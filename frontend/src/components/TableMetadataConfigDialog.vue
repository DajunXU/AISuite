<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal metadata-modal">
      <div class="modal-header">
        <h3>配置元数据：{{ connectionName }}.{{ tableName }}</h3>
        <button class="close-button" @click="close">×</button>
      </div>
      
      <div class="modal-body">
        <!-- 表信息设置 -->
        <div class="form-section">
          <h4 class="section-title">表信息设置</h4>
          
          <div class="form-group">
            <label class="form-label">表中文名</label>
            <input
              v-model="metadataForm.table_name_cn"
              type="text"
              class="form-input"
              placeholder="订单表"
            />
          </div>
          
          <div class="form-group">
            <label class="form-label">表描述</label>
            <textarea
              v-model="metadataForm.description"
              class="form-textarea"
              placeholder="存储所有客户订单信息，每行代表一个订单"
              rows="2"
            ></textarea>
          </div>
          
          <div class="form-group">
            <label class="form-label">业务标签</label>
            <input
              v-model="metadataForm.business_tags"
              type="text"
              class="form-input"
              placeholder="核心表、交易数据、分析重点"
            />
            <div class="form-help">多个标签用逗号分隔</div>
          </div>
        </div>
        
        <!-- 字段信息设置 -->
        <div class="form-section">
          <h4 class="section-title">字段信息设置（可批量编辑）</h4>
          
          <div class="table-container">
            <table class="metadata-table">
              <thead>
                <tr>
                  <th style="width: 40px;">
                    <input type="checkbox" v-model="allSelected" @change="handleSelectAll" />
                  </th>
                  <th>字段名</th>
                  <th>类型</th>
                  <th>字段注释</th>
                  <th>同义词</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="col in columns" :key="col.column_name">
                  <td>
                    <input type="checkbox" v-model="col.is_selected" />
                  </td>
                  <td>{{ col.column_name }}</td>
                  <td>{{ col.column_type }}</td>
                  <td>
                    <input
                      v-model="col.column_comment"
                      type="text"
                      class="table-input"
                      placeholder="字段注释"
                    />
                  </td>
                  <td>
                    <input
                      v-model="col.synonyms"
                      type="text"
                      class="table-input"
                      placeholder="同义词"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- 指标口径定义 -->
        <div class="form-section">
          <h4 class="section-title">指标口径定义（Text2Metrics核心！）</h4>
          
          <div class="metrics-container">
            <div v-for="(metric, index) in metrics" :key="index" class="metric-item">
              <div class="metric-row">
                <div class="form-group flex-1">
                  <label class="form-label">指标名称</label>
                  <input
                    v-model="metric.metric_name"
                    type="text"
                    class="form-input"
                    placeholder="销售额"
                  />
                </div>
                <div class="form-group flex-2">
                  <label class="form-label">口径定义（SQL片段）</label>
                  <input
                    v-model="metric.metric_definition"
                    type="text"
                    class="form-input"
                    placeholder="SUM(CASE WHEN pay_status=1 THEN amount ELSE 0 END)"
                  />
                </div>
                <button class="delete-btn" @click="removeMetric(index)" v-if="metrics.length > 1">×</button>
              </div>
              <div class="form-group">
                <label class="form-label">描述</label>
                <input
                  v-model="metric.description"
                  type="text"
                  class="form-input"
                  placeholder="已支付才算销售额"
                />
              </div>
            </div>
            
            <button class="add-metric-btn" @click="addMetric">+ 添加指标</button>
          </div>
        </div>
        
        <!-- 推荐问题 -->
        <div class="form-section">
          <h4 class="section-title">推荐问题（自动生成的示例问题）</h4>
          
          <div class="form-group">
            <textarea
              v-model="metadataForm.recommended_questions"
              class="form-textarea"
              placeholder="上周销售额是多少？&#10;销量前10的产品有哪些？&#10;华东区Q3的客单价趋势？"
              rows="3"
            ></textarea>
            <div class="form-help">每行一个问题</div>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <div class="form-actions">
          <button class="secondary-button" @click="close">取消</button>
          <button class="primary-button" @click="save" :disabled="saving">
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

interface Props {
  show: boolean
  knowledgeBaseId: number
  connectionId: number
  tableId: number
  tableName: string
  connectionName: string
}

interface Emits {
  (e: 'update:show', value: boolean): void
  (e: 'saved'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const saving = ref(false)

const metadataForm = ref({
  table_name_cn: '',
  description: '',
  business_tags: '',
  recommended_questions: ''
})

const columns = ref<any[]>([])
const allSelected = ref(true)

const handleSelectAll = () => {
  columns.value.forEach(col => {
    col.is_selected = allSelected.value
  })
}

const metrics = ref<any[]>([
  { metric_name: '', metric_definition: '', description: '' }
])

const loadMetadata = async () => {
  try {
    const response = await fetch(
      `/api/knowledge/${props.knowledgeBaseId}/database/connections/${props.connectionId}/metadata/${props.tableId}`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    )
    
    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || '加载失败')
    }
    
    const data = await response.json()
    
    // 设置表信息
    if (data.table) {
      metadataForm.value = {
        table_name_cn: data.table.table_name_cn || '',
        description: data.table.description || '',
        business_tags: data.table.business_tags || '',
        recommended_questions: data.table.recommended_questions || ''
      }
    }
    
    // 设置字段信息 - 同时加载远程字段进行合并
    await loadAndMergeColumns(data.columns || [])
    
    // 设置指标
    if (data.metrics && data.metrics.length > 0) {
      metrics.value = data.metrics
    }
    
  } catch (error: any) {
    console.error('加载元数据失败', error)
    // 如果加载失败，尝试获取远程字段并合并
    await loadAndMergeColumns([])
  }
}

const loadAndMergeColumns = async (savedColumns: any[]) => {
  try {
    // 创建已保存字段的映射
    const savedMap = new Map()
    savedColumns.forEach((col: any) => {
      savedMap.set(col.column_name, col)
    })
    
    // 获取远程数据库的字段
    const response = await fetch(
      `/api/knowledge/${props.knowledgeBaseId}/database/connections/${props.connectionId}/tables`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      }
    )
    
    if (response.ok) {
      const data = await response.json()
      
      // 兼容不同的返回格式
      let tableList = []
      if (Array.isArray(data)) {
        tableList = data
      } else if (data.tables) {
        tableList = data.tables
      }
      
      const table = tableList.find((t: any) => t.table_name === props.tableName)
      if (table && table.columns) {
        // 合并字段信息：使用远程的类型，保留已保存的注释和同义词
        columns.value = table.columns.map((col: any) => {
          const saved = savedMap.get(col.column_name)
          return {
            column_name: col.column_name,
            column_type: col.column_type,
            column_comment: saved?.column_comment || col.column_comment || '',
            synonyms: saved?.synonyms || '',
            is_selected: saved?.is_selected ?? true
          }
        })
      }
    }
  } catch (error) {
    console.error('获取远程字段失败', error)
    // 如果获取失败，使用已保存的字段
    if (savedColumns.length > 0) {
      columns.value = savedColumns
    }
  }
}

const addMetric = () => {
  metrics.value.push({ metric_name: '', metric_definition: '', description: '' })
}

const removeMetric = (index: number) => {
  metrics.value.splice(index, 1)
}

const close = () => {
  emit('update:show', false)
}

const save = async () => {
  saving.value = true
  try {
    const response = await fetch(
      `/api/knowledge/${props.knowledgeBaseId}/database/connections/${props.connectionId}/metadata/${props.tableId}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          table_name_cn: metadataForm.value.table_name_cn,
          description: metadataForm.value.description,
          business_tags: metadataForm.value.business_tags,
          recommended_questions: metadataForm.value.recommended_questions,
          columns: columns.value,
          metrics: metrics.value
        })
      }
    )
    
    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || '保存失败')
    }
    
    ElMessage.success('元数据保存成功！')
    emit('saved')
    close()
  } catch (error: any) {
    ElMessage.error(`保存失败: ${error.message}`)
    console.error(error)
  } finally {
    saving.value = false
  }
}

// 监听弹窗显示
watch(() => props.show, (newVal, oldVal) => {
  if (newVal) {
    // 如果有tableId，用tableId；如果没有但有tableName，也尝试加载
    if (props.tableId || props.tableName) {
      loadMetadata()
    }
  }
}, { immediate: true })
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

.metadata-modal {
  width: 900px;
  max-width: 95vw;
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

.form-group {
  margin-bottom: 12px;
}

.form-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.flex-1 {
  flex: 1;
}

.flex-2 {
  flex: 2;
}

.form-label {
  display: block;
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #409eff;
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.table-container {
  overflow-x: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.metadata-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.metadata-table th,
.metadata-table td {
  padding: 8px 12px;
  text-align: left;
  border-bottom: 1px solid #ebeef5;
}

.metadata-table th {
  background: #f5f7fa;
  font-weight: 500;
  color: #606266;
}

.metadata-table td {
  color: #303133;
}

.table-input {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid #dcdfe6;
  border-radius: 3px;
  font-size: 12px;
}

.metrics-container {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 12px;
}

.metric-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 12px;
}

.metric-item:last-of-type {
  margin-bottom: 0;
}

.metric-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.delete-btn {
  width: 28px;
  height: 28px;
  border: none;
  background: #f56c6c;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
}

.delete-btn:hover {
  background: #f78989;
}

.add-metric-btn {
  width: 100%;
  padding: 8px;
  border: 1px dashed #dcdfe6;
  background: white;
  color: #409eff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  margin-top: 12px;
}

.add-metric-btn:hover {
  border-color: #409eff;
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

.secondary-button:hover {
  border-color: #409eff;
  color: #409eff;
}
</style>
