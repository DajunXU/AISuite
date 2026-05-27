<template>
  <div class="permission-page">
    <div class="layout-container">
      <Sidebar />
      
      <div class="main-container">
        <PageHeader title="知识库权限配置" />
        
        <main class="main-content">
          <div class="kb-permission-container">
            <!-- 左侧：知识库列表 -->
            <div class="kb-list-panel">
              <div class="panel-header">
                <h3>知识库列表</h3>
              </div>
              <div class="kb-list">
                <div 
                  v-for="kb in knowledgeBases" 
                  :key="kb.id"
                  :class="['kb-item', selectedKb?.id === kb.id ? 'active' : '']"
                  @click="selectKnowledgeBase(kb)"
                >
                  <span class="kb-icon">📁</span>
                  <span class="kb-name">{{ kb.name }}</span>
                  <span class="kb-role-count">{{ getKbRoleCount(kb.id) }}</span>
                </div>
                <div v-if="knowledgeBases.length === 0" class="empty-tip">
                  暂无可配置的知识库
                </div>
              </div>
            </div>
            
            <!-- 右侧：角色配置 -->
            <div class="role-config-panel">
              <div class="panel-header">
                <h3>可访问角色</h3>
                <el-button 
                  v-if="selectedKb" 
                  type="primary" 
                  size="small"
                  @click="openAddRoleDialog"
                >
                  <el-icon><Plus /></el-icon> 添加角色
                </el-button>
              </div>
              
              <div v-if="selectedKb" class="role-list">
                <div 
                  v-for="kbRole in selectedKbRoles" 
                  :key="kbRole.id"
                  class="role-item"
                >
                  <div class="role-info">
                    <el-tag class="role-tag">{{ kbRole.role_name }}</el-tag>
                  </div>
                  <el-button 
                    type="danger" 
                    size="small" 
                    link
                    @click="removeRole(kbRole)"
                  >
                    <el-icon><Delete /></el-icon> 移除
                  </el-button>
                </div>
                <div v-if="selectedKbRoles.length === 0" class="empty-tip">
                  暂未配置访问角色，所有用户均不可访问
                </div>
              </div>
              
              <div v-else class="empty-panel">
                <span>请选择左侧知识库进行配置</span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
    
    <!-- 添加角色对话框 -->
    <el-dialog
      v-model="showAddRoleDialog"
      title="添加可访问角色"
      width="400px"
    >
      <div class="add-role-dialog">
        <p class="dialog-tip">选择可以访问「{{ selectedKb?.name }}」的角色：</p>
        <el-checkbox-group v-model="selectedRoleIds" class="role-checkbox-group">
          <el-checkbox 
            v-for="role in availableRoles" 
            :key="role.id" 
            :label="role.id"
            :disabled="isRoleAdded(role.id)"
          >
            {{ role.name }}
          </el-checkbox>
        </el-checkbox-group>
      </div>
      <template #footer>
        <el-button @click="showAddRoleDialog = false">取消</el-button>
        <el-button type="primary" @click="addRoles" :disabled="selectedRoleIds.length === 0">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import Sidebar from '@/components/Sidebar.vue'
import PageHeader from '@/components/PageHeader.vue'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()

interface KnowledgeBase {
  id: number
  name: string
}

interface KnowledgeBaseRole {
  id: number
  knowledge_base_id: number
  role_id: number
  knowledge_base_name?: string
  role_name?: string
}

interface Role {
  id: number
  name: string
}

const knowledgeBases = ref<KnowledgeBase[]>([])
const kbRoles = ref<KnowledgeBaseRole[]>([])
const roles = ref<Role[]>([])
const selectedKb = ref<KnowledgeBase | null>(null)
const showAddRoleDialog = ref(false)
const selectedRoleIds = ref<number[]>([])

const selectedKbRoles = computed(() => {
  if (!selectedKb.value) return []
  return kbRoles.value.filter(kr => kr.knowledge_base_id === selectedKb.value!.id)
})

const availableRoles = computed(() => {
  return roles.value
})

const isRoleAdded = (roleId: number) => {
  return selectedKbRoles.value.some(kr => kr.role_id === roleId)
}

const getKbRoleCount = (kbId: number) => {
  const count = kbRoles.value.filter(kr => kr.knowledge_base_id === kbId).length
  return count > 0 ? count : ''
}

const loadKnowledgeBases = async () => {
  try {
    const response = await request.get('/knowledge/')
    knowledgeBases.value = response || []
  } catch (error) {
    console.error('加载知识库失败:', error)
    knowledgeBases.value = []
  }
}

const loadKbRoles = async () => {
  try {
    const response = await request.get('/permission/knowledge-base-roles')
    kbRoles.value = response.knowledge_base_roles || []
  } catch (error: any) {
    console.error('加载知识库角色失败:', error)
    console.error('错误详情:', error.response?.data || error.message)
    kbRoles.value = []
  }
}

const loadRoles = async () => {
  try {
    const response = await request.get('/permission/roles/')
    roles.value = Array.isArray(response) ? response : (response.roles || [])
  } catch (error) {
    console.error('加载角色失败:', error)
    roles.value = []
  }
}

const selectKnowledgeBase = (kb: KnowledgeBase) => {
  selectedKb.value = kb
}

const openAddRoleDialog = () => {
  selectedRoleIds.value = []
  showAddRoleDialog.value = true
}

const addRoles = async () => {
  if (!selectedKb.value || selectedRoleIds.value.length === 0) return
  
  try {
    for (const roleId of selectedRoleIds.value) {
      await request.post('/permission/knowledge-base-roles', {
        knowledge_base_id: selectedKb.value.id,
        role_id: roleId
      })
    }
    ElMessage.success('添加成功')
    showAddRoleDialog.value = false
    loadKbRoles()
  } catch (error: any) {
    ElMessage.error(error.detail || '添加失败')
  }
}

const removeRole = async (kbRole: KnowledgeBaseRole) => {
  try {
    await ElMessageBox.confirm(
      `确定要移除角色「${kbRole.role_name}」对「${selectedKb.value?.name}」的访问权限吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await request.delete(`/permission/knowledge-base-roles/${kbRole.id}`)
    ElMessage.success('移除成功')
    loadKbRoles()
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  loadKnowledgeBases()
  loadKbRoles()
  loadRoles()
})
</script>

<style scoped>
.permission-page {
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #f8fafc 0%, #f0f6ff 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
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
  background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
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
  gap: 14px;
  padding: 10px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.user-info:hover {
  background: #f0f6ff;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff, #36cfc9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 18px;
}

.user-name {
  font-size: 15px;
  font-weight: 600;
  color: #595959;
}

.dropdown-arrow {
  font-size: 12px;
  color: #8c8c8c;
  transition: transform 0.3s ease;
}

.user-dropdown:hover .dropdown-arrow {
  transform: rotate(180deg);
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
  padding: 10px;
  min-width: 140px;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: all 0.3s ease;
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
  border-radius: 8px;
  font-size: 14px;
  color: #595959;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dropdown-item:hover {
  background: #f0f6ff;
  color: #1890ff;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 36px;
}

.kb-permission-container {
  display: flex;
  gap: 24px;
  height: 100%;
}

.kb-list-panel,
.role-config-panel {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.kb-list-panel {
  width: 320px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.role-config-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
}

.kb-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.kb-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 4px;
}

.kb-item:hover {
  background: #f5f7fa;
}

.kb-item.active {
  background: #e6f4ff;
  color: #1890ff;
}

.kb-icon {
  font-size: 18px;
}

.kb-name {
  flex: 1;
  font-size: 14px;
  color: #262626;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-role-count {
  background: #1890ff;
  color: white;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.role-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.role-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 10px;
  margin-bottom: 12px;
}

.role-tag {
  font-size: 14px;
}

.empty-tip,
.empty-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 120px;
  color: #8c8c8c;
  font-size: 14px;
}

.empty-panel {
  flex: 1;
}

.add-role-dialog {
  padding: 10px 0;
}

.dialog-tip {
  margin: 0 0 16px 0;
  color: #595959;
  font-size: 14px;
}

.role-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.role-checkbox-group .el-checkbox {
  margin-right: 0;
  padding: 10px;
  border-radius: 8px;
}

.role-checkbox-group .el-checkbox:hover {
  background: #f5f7fa;
}
</style>
