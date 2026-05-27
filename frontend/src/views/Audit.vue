<template>
  <div class="audit-page">
    <div class="layout-container">
      <Sidebar />
      
      <div class="main-container">
        <PageHeader title="审计日志" />
        
        <main class="main-content">
          <div class="audit-management">
            <el-card shadow="hover" class="audit-card">
              <template #header>
                <div class="card-header">
                  <span>审计日志</span>
                  <div class="header-actions">
                    <el-button type="primary" @click="loadLogs">
                      <el-icon><Refresh /></el-icon> 刷新
                    </el-button>
                  </div>
                </div>
              </template>
              
              <div class="filter-section">
                <el-row :gutter="16" align="middle">
                  <el-col :span="4">
                    <el-input
                      v-model="filters.username"
                      placeholder="用户名"
                      clearable
                      @keyup.enter="loadLogs"
                    />
                  </el-col>
                  <el-col :span="4">
                    <el-select v-model="filters.action" placeholder="操作类型" clearable>
                      <el-option
                        v-for="action in actionOptions"
                        :key="action"
                        :label="action"
                        :value="action"
                      />
                    </el-select>
                  </el-col>
                  <el-col :span="10">
                    <el-date-picker
                      v-model="dateRange"
                      type="daterange"
                      range-separator="至"
                      start-placeholder="开始日期"
                      end-placeholder="结束日期"
                      value-format="YYYY-MM-DD"
                      @change="handleDateChange"
                      style="width: 100%"
                    />
                  </el-col>
                  <el-col :span="6" style="text-align: right;">
                    <el-button type="primary" @click="loadLogs">
                      <el-icon><Search /></el-icon> 查询
                    </el-button>
                  </el-col>
                </el-row>
              </div>
              
              <el-table :data="logs" v-loading="loading" style="width: 100%">
                <el-table-column prop="id" label="ID" width="60" />
                <el-table-column prop="username" label="用户" width="100" />
                <el-table-column prop="action" label="操作" width="120">
                  <template #default="scope">
                    <el-tag :type="getActionType(scope.row.action)">
                      {{ scope.row.action }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="method" label="方法" width="80" />
                <el-table-column prop="path" label="路径" min-width="200" show-overflow-tooltip />
                <el-table-column prop="ip_address" label="IP地址" width="130" />
                <el-table-column prop="response_status" label="状态" width="80">
                  <template #default="scope">
                    <el-tag :type="scope.row.response_status === 200 ? 'success' : 'danger'">
                      {{ scope.row.response_status || '-' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="时间" width="170">
                  <template #default="scope">
                    {{ formatDate(scope.row.created_at) }}
                  </template>
                </el-table-column>
                <el-table-column label="详情" width="80">
                  <template #default="scope">
                    <el-button size="small" @click="showDetail(scope.row)">
                      详情
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              
              <div class="pagination-container">
                <el-pagination
                  v-model:current-page="pagination.page"
                  v-model:page-size="pagination.pageSize"
                  :page-sizes="[20, 50, 100]"
                  :total="pagination.total"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="loadLogs"
                  @current-change="loadLogs"
                />
              </div>
            </el-card>
          </div>
        </main>
      </div>
    </div>
    
    <el-dialog v-model="detailVisible" title="日志详情" width="600px">
      <el-descriptions :column="2" border v-if="currentLog">
        <el-descriptions-item label="ID">{{ currentLog.id }}</el-descriptions-item>
        <el-descriptions-item label="用户">{{ currentLog.username || '-' }}</el-descriptions-item>
        <el-descriptions-item label="操作">{{ currentLog.action }}</el-descriptions-item>
        <el-descriptions-item label="HTTP方法">{{ currentLog.method || '-' }}</el-descriptions-item>
        <el-descriptions-item label="请求路径" :span="2">{{ currentLog.path || '-' }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentLog.ip_address || '-' }}</el-descriptions-item>
        <el-descriptions-item label="响应状态">{{ currentLog.response_status || '-' }}</el-descriptions-item>
        <el-descriptions-item label="User-Agent" :span="2">{{ currentLog.user_agent || '-' }}</el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2">{{ currentLog.error_message || '-' }}</el-descriptions-item>
        <el-descriptions-item label="时间" :span="2">{{ formatDate(currentLog.created_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, Search } from '@element-plus/icons-vue'
import Sidebar from '@/components/Sidebar.vue'
import PageHeader from '@/components/PageHeader.vue'
import { useUserStore } from '@/stores/user'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const logs = ref([])
const actionOptions = ref<string[]>([])
const dateRange = ref<[string, string] | null>(null)

const filters = reactive({
  username: '',
  action: '',
  startDate: '',
  endDate: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})

const detailVisible = ref(false)
const currentLog = ref<any>(null)

const getActionType = (action: string) => {
  const typeMap: Record<string, string> = {
    'login': 'success',
    'logout': 'info',
    'login_failed': 'danger',
    'kb_create': 'success',
    'kb_update': 'warning',
    'kb_delete': 'danger',
    'file_upload': 'success',
    'file_delete': 'danger',
    'chat_message': 'primary',
    'system_error': 'danger'
  }
  return typeMap[action] || 'info'
}

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const handleDateChange = (val: [string, string] | null) => {
  if (val) {
    filters.startDate = val[0]
    filters.endDate = val[1]
  } else {
    filters.startDate = ''
    filters.endDate = ''
  }
}

const loadLogs = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: pagination.page.toString(),
      page_size: pagination.pageSize.toString()
    })
    
    if (filters.username) params.append('username', filters.username)
    if (filters.action) params.append('action', filters.action)
    if (filters.startDate) params.append('start_date', filters.startDate)
    if (filters.endDate) params.append('end_date', filters.endDate)
    
    const response = await axios.get(`/api/audit/logs?${params}`)
    logs.value = response.data.items
    pagination.total = response.data.total
  } catch (error: any) {
    ElMessage.error('加载日志失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const loadActions = async () => {
  try {
    const response = await axios.get('/api/audit/logs/actions')
    actionOptions.value = response.data
  } catch (error) {
    console.error('加载操作类型失败:', error)
  }
}

const showDetail = (row: any) => {
  currentLog.value = row
  detailVisible.value = true
}

onMounted(() => {
  loadLogs()
  loadActions()
})
</script>

<style scoped>
.audit-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.layout-container {
  display: flex;
  min-height: 100vh;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding: 24px;
}

.audit-management {
  width: 100%;
}

.audit-card {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  font-size: 16px;
  font-weight: 600;
}

.filter-section {
  margin-bottom: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.el-table {
  max-height: 400px;
  overflow-y: auto;
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
