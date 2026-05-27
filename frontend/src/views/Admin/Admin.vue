<template>
  <div class="dashboard">
    <div class="layout-container">
      <Sidebar />
      
      <div class="main-container">
        <PageHeader title="用户管理" />
        
        <main class="main-content">
          <div class="user-management">
            <div class="user-management-header">
              <div class="header-left">
                <h3>用户列表</h3>
                <span class="user-count">共 {{ users.length }} 位用户</span>
              </div>
              <div class="header-right">
                <el-button type="primary" @click="openUserDialog">
                  <el-icon><Plus /></el-icon>
                  新增用户
                </el-button>
                <el-input
                  v-model="searchKeyword"
                  placeholder="搜索用户名或邮箱..."
                  clearable
                  class="search-input"
                  @input="handleSearch"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
              </div>
            </div>
            
            <el-table :data="filteredUsers" style="width: 100%" class="user-table">
              <el-table-column prop="username" label="用户名" min-width="120">
                <template #default="scope">
                  <div class="user-info-cell">
                    <div class="user-avatar">{{ scope.row.username?.charAt(0).toUpperCase() }}</div>
                    <span class="username">{{ scope.row.username }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="email" label="邮箱" min-width="180" />
              <el-table-column prop="role" label="角色" width="180">
                <template #default="scope">
                  <div class="role-cell">
                    <el-tag 
                      v-for="role in (scope.row.roles || [])" 
                      :key="role.id" 
                      size="small" 
                      class="role-tag"
                    >
                      {{ role.name }}
                    </el-tag>
                    <span v-if="!scope.row.roles || scope.row.roles.length === 0" class="no-role">
                      未分配
                    </span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="is_active" label="状态" width="100">
                <template #default="scope">
                  <el-switch
                    v-model="scope.row.is_active"
                    @change="updateUserStatus(scope.row)"
                    :loading="scope.row.switchLoading"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="注册时间" width="140">
                <template #default="scope">
                  <span class="date-text">{{ formatDate(scope.row.created_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="220" fixed="right">
                <template #default="scope">
                  <el-button 
                    type="primary" 
                    link 
                    @click="openUserDialog(scope.row)"
                  >
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-button 
                    type="primary" 
                    link 
                    @click="openRoleDialog(scope.row)"
                  >
                    角色
                  </el-button>
                  <el-button 
                    v-if="scope.row.role !== 'admin'" 
                    type="danger" 
                    link 
                    @click="deleteUser(scope.row)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            
            <el-empty v-if="filteredUsers.length === 0" description="暂无用户数据" />
            
            <!-- 角色分配对话框 -->
            <el-dialog
              v-model="roleDialogVisible"
              :title="`分配角色 - ${selectedUser?.username}`"
              width="500px"
            >
              <div class="role-assign-content">
                <p class="role-assign-tip">请选择要分配给该用户的角色：</p>
                <el-checkbox-group v-model="selectedRoleIds" class="role-checkbox-group">
                  <el-checkbox
                    v-for="role in roles"
                    :key="role.id"
                    :label="role.id"
                    :disabled="role.name === 'admin'"
                  >
                    {{ role.name }}
                    <span v-if="role.description" class="role-desc">({{ role.description }})</span>
                  </el-checkbox>
                </el-checkbox-group>
                <el-empty v-if="roles.length === 0" description="暂无角色数据" />
              </div>
              <template #footer>
                <el-button @click="roleDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="saveUserRoles" :loading="roleLoading">保存</el-button>
              </template>
            </el-dialog>
            
            <!-- 用户新增/编辑对话框 -->
            <el-dialog
              v-model="userDialogVisible"
              :title="userDialogTitle"
              width="500px"
            >
              <el-form :model="userForm" label-width="80px" class="user-form">
                <el-form-item label="用户名" required>
                  <el-input v-model="userForm.username" placeholder="请输入用户名" :disabled="!!userForm.id" />
                </el-form-item>
                <el-form-item label="邮箱" required>
                  <el-input v-model="userForm.email" placeholder="请输入邮箱" />
                </el-form-item>
                <el-form-item v-if="!userForm.id" label="密码" required>
                  <el-input v-model="userForm.password" type="password" placeholder="请输入密码" show-password />
                </el-form-item>
                <el-form-item v-if="userForm.id" label="新密码">
                  <el-input v-model="userForm.password" type="password" placeholder="留空则不修改密码" show-password />
                </el-form-item>
                <el-form-item label="姓名">
                  <el-input v-model="userForm.full_name" placeholder="请输入姓名" />
                </el-form-item>
                <el-form-item label="状态">
                  <el-switch v-model="userForm.is_active" />
                </el-form-item>
              </el-form>
              <template #footer>
                <el-button @click="userDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="saveUser" :loading="userFormLoading">保存</el-button>
              </template>
            </el-dialog>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Delete, Edit, Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import request, { getUserRoles, assignUserRoles } from '@/utils/request'
import Sidebar from '@/components/Sidebar.vue'
import PageHeader from '@/components/PageHeader.vue'

const userStore = useUserStore()
const router = useRouter()

// 响应式数据
const users = ref<any[]>([])
const roles = ref<any[]>([])
const searchKeyword = ref('')
const roleDialogVisible = ref(false)
const selectedUser = ref(null)
const selectedRoleIds = ref<number[]>([])
const roleLoading = ref(false)

const userDialogVisible = ref(false)
const userDialogTitle = ref('新增用户')
const userForm = ref({
  id: null,
  username: '',
  email: '',
  password: '',
  full_name: '',
  is_active: true
})
const userFormLoading = ref(false)

const filteredUsers = computed(() => {
  if (!searchKeyword.value) return users.value
  const keyword = searchKeyword.value.toLowerCase()
  return users.value.filter(user => 
    user.username?.toLowerCase().includes(keyword) || 
    user.email?.toLowerCase().includes(keyword)
  )
})

const handleSearch = () => {
}

// 生命周期
onMounted(() => {
  loadUsers()
  loadRoles()
})

// 方法
const loadUsers = async () => {
  try {
    const response = await request.get('/users/')
    users.value = response
  } catch (error) {
    ElMessage.error('加载用户列表失败')
    console.error(error)
  }
}

const loadRoles = async () => {
  try {
    const response = await request.get('/permission/roles')
    roles.value = Array.isArray(response) ? response : (response.roles || [])
  } catch (error) {
    ElMessage.error('加载角色列表失败')
    console.error(error)
  }
}

const updateUserStatus = async (user: any) => {
  try {
    await request.put(`/users/${user.id}`, {
      is_active: user.is_active
    })
    ElMessage.success('用户状态更新成功')
  } catch (error) {
    ElMessage.error('更新用户状态失败')
    console.error(error)
    // 回滚状态
    user.is_active = !user.is_active
  }
}

const deleteUser = async (user: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除用户 "${user.username}" 吗？`, '提示', {
      type: 'warning'
    })
    
    await request.delete(`/users/${user.id}`)
    ElMessage.success('用户删除成功')
    await loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除用户失败')
      console.error(error)
    }
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const openRoleDialog = async (user: any) => {
  selectedUser.value = user
  selectedRoleIds.value = []
  roleLoading.value = true
  
  try {
    const response = await getUserRoles(user.id)
    if (response.roles) {
      selectedRoleIds.value = response.roles.map((r: any) => r.id)
    }
  } catch (error) {
    console.error('获取用户角色失败:', error)
  } finally {
    roleLoading.value = false
  }
  
  roleDialogVisible.value = true
}

const saveUserRoles = async () => {
  try {
    await assignUserRoles(selectedUser.value.id, {
      role_ids: selectedRoleIds.value
    })
    ElMessage.success('用户角色分配成功')
    roleDialogVisible.value = false
    await loadUsers()
  } catch (error) {
    ElMessage.error('分配角色失败')
    console.error(error)
  }
}

const openUserDialog = (user?: any) => {
  if (user) {
    userDialogTitle.value = '编辑用户'
    userForm.value = {
      id: user.id,
      username: user.username,
      email: user.email,
      password: '',
      full_name: user.full_name || '',
      is_active: user.is_active
    }
  } else {
    userDialogTitle.value = '新增用户'
    userForm.value = {
      id: null,
      username: '',
      email: '',
      password: '',
      full_name: '',
      is_active: true
    }
  }
  userDialogVisible.value = true
}

const saveUser = async () => {
  if (!userForm.value.username || !userForm.value.email) {
    ElMessage.warning('请填写用户名和邮箱')
    return
  }
  
  if (!userForm.value.id && !userForm.value.password) {
    ElMessage.warning('请填写密码')
    return
  }
  
  userFormLoading.value = true
  try {
    const data: any = {
      email: userForm.value.email,
      full_name: userForm.value.full_name,
      is_active: userForm.value.is_active
    }
    
    if (userForm.value.password) {
      data.password = userForm.value.password
    }
    
    if (userForm.value.id) {
      await request.put(`/users/${userForm.value.id}`, data)
      ElMessage.success('用户更新成功')
    } else {
      data.username = userForm.value.username
      data.password = userForm.value.password
      await request.post('/users/', data)
      ElMessage.success('用户创建成功')
    }
    
    userDialogVisible.value = false
    await loadUsers()
  } catch (error) {
    ElMessage.error(userForm.value.id ? '更新用户失败' : '创建用户失败')
    console.error(error)
  } finally {
    userFormLoading.value = false
  }
}
</script>

<style scoped>
/* 智谱AI风格 - 清新现代 */
.admin {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: linear-gradient(135deg, #f8fafc 0%, #f0f6ff 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
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

.header-left {
  display: flex;
  align-items: center;
  gap: 28px;
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

/* 用户下拉菜单 - 智谱风格 */
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
  transition: all 0.3s ease;
}

.dropdown-item:hover {
  background: #f0f6ff;
  color: #1890ff;
}

/* 主内容 */
.main-content {
  flex: 1;
  background: transparent;
  overflow-y: auto;
  padding: 36px;
}

/* 用户管理样式 */
.user-management {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.user-management-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.user-management-header .header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-management-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #262626;
}

.user-count {
  font-size: 14px;
  color: #909399;
  background: #f5f7fa;
  padding: 4px 12px;
  border-radius: 20px;
}

.search-input {
  width: 280px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-form .el-input {
  width: 100%;
}

.user-table {
  border-radius: 12px;
  overflow: hidden;
}

.user-info-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info-cell .user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1890ff, #36cfc9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.user-info-cell .username {
  font-weight: 500;
  color: #303133;
}

.date-text {
  color: #606266;
  font-size: 14px;
}

.role-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.role-tag {
  margin-right: 0;
}

.no-role {
  color: #c0c4cc;
  font-size: 13px;
}

.role-assign-content {
  padding: 10px 0;
}

.role-assign-tip {
  color: #606266;
  margin-bottom: 16px;
}

.role-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.role-checkbox-group .el-checkbox {
  margin-right: 0;
  padding: 8px 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  transition: all 0.3s;
}

.role-checkbox-group .el-checkbox:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.role-desc {
  color: #909399;
  font-size: 12px;
  margin-left: 6px;
}

.admin-container {
  max-width: 1200px;
  margin: 0 auto;
}

.admin-section {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 28px;
  margin-bottom: 28px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.admin-section h3 {
  margin: 0 0 24px 0;
  font-size: 22px;
  font-weight: 700;
  color: #262626;
  border-bottom: 2px solid rgba(240, 240, 240, 0.6);
  padding-bottom: 14px;
}

/* 自定义表格样式 - 智谱风格 */
.custom-table {
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  overflow: hidden;
}

.table-header {
  background: #f0f6ff;
  border-bottom: 1px solid #f0f0f0;
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 1.5fr 1fr 1fr 1.5fr 1fr;
  gap: 1px;
  background: #f0f6ff;
}

.table-cell {
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.95);
  font-size: 15px;
  color: #262626;
  display: flex;
  align-items: center;
}

.table-header .table-cell {
  font-weight: 700;
  background: #f0f6ff;
  color: #595959;
}

.role-badge {
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.role-badge.admin {
  background: #ffccc7;
  color: #a8071a;
}

.role-badge.user {
  background: #bae7ff;
  color: #0050b3;
}

/* 开关样式 - 智谱风格 */
.switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 26px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #d9d9d9;
  transition: .4s;
  border-radius: 26px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 20px;
  width: 20px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #1890ff;
}

input:checked + .slider:before {
  transform: translateX(22px);
}

/* 按钮样式 - 智谱风格 */
.delete-button {
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.delete-button:hover {
  background: #d9363e;
  transform: translateY(-2px);
}

.edit-button {
  background: linear-gradient(135deg, #1890ff, #36cfc9);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.edit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(24, 144, 255, 0.3);
}

/* 统计卡片 - 智谱风格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 24px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 28px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: transform 0.4s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
}

.stat-value {
  font-size: 36px;
  font-weight: 800;
  color: #1890ff;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 15px;
  color: #8c8c8c;
  font-weight: 600;
}

/* 表单样式 - 智谱风格 */
.settings-form {
  max-width: 500px;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
  color: #262626;
  font-size: 15px;
}

.form-input {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.9);
}

.form-input:focus {
  outline: none;
  border-color: #1890ff;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.1);
}

.number-input-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.number-input {
  width: 100px;
  padding: 12px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 10px;
  font-size: 15px;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.9);
}

.number-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.unit {
  font-size: 14px;
  color: #64748b;
}

.form-actions {
  margin-top: 24px;
}

.primary-button {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.primary-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .table-row {
    grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .sidebar {
    width: 240px;
  }
  
  .header {
    padding: 0 20px;
  }
  
  .table-row {
    grid-template-columns: 1fr;
    gap: 0;
  }
  
  .table-cell {
    border-bottom: 1px solid #e2e8f0;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .main-content {
    padding: 16px;
  }
}
</style>
