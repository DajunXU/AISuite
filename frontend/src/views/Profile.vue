<template>
  <div class="profile-page">
    <div class="layout-container">
      <Sidebar />
      
      <div class="main-container">
        <PageHeader title="个人中心" />
        
        <main class="main-content">
          <div class="profile-container">
            <el-card shadow="hover" class="profile-card">
              <template #header>
                <div class="card-header">
                  <span>个人信息</span>
                </div>
              </template>
              
              <el-form :model="profileForm" label-width="100px" class="profile-form">
                <el-form-item label="用户名">
                  <el-input v-model="profileForm.username" disabled />
                </el-form-item>
                <el-form-item label="邮箱">
                  <el-input v-model="profileForm.email" disabled />
                </el-form-item>
                <el-form-item label="姓名">
                  <el-input v-model="profileForm.full_name" placeholder="请输入姓名" />
                </el-form-item>
                <el-form-item label="角色">
                  <el-input :value="profileForm.role === 'admin' ? '管理员' : '普通用户'" disabled />
                </el-form-item>
                <el-form-item label="创建时间">
                  <el-input :value="formatDate(profileForm.created_at)" disabled />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="updateProfile" :loading="profileLoading">
                    保存修改
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
            
            <el-card shadow="hover" class="password-card">
              <template #header>
                <div class="card-header">
                  <span>修改密码</span>
                </div>
              </template>
              
              <el-form :model="passwordForm" label-width="100px" class="password-form">
                <el-form-item label="原密码">
                  <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入原密码" />
                </el-form-item>
                <el-form-item label="新密码">
                  <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="请输入新密码" />
                </el-form-item>
                <el-form-item label="确认密码">
                  <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="changePassword" :loading="passwordLoading">
                    修改密码
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import Sidebar from '@/components/Sidebar.vue'
import PageHeader from '@/components/PageHeader.vue'
import { useUserStore } from '@/stores/user'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

const profileLoading = ref(false)
const passwordLoading = ref(false)

const profileForm = reactive({
  username: '',
  email: '',
  full_name: '',
  role: '',
  created_at: ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const formatDate = (date: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const loadProfile = () => {
  if (userStore.user) {
    profileForm.username = userStore.user.username || ''
    profileForm.email = userStore.user.email || ''
    profileForm.full_name = userStore.user.full_name || ''
    profileForm.role = userStore.user.role || 'user'
    profileForm.created_at = userStore.user.created_at || ''
  }
}

const updateProfile = async () => {
  profileLoading.value = true
  try {
    const token = localStorage.getItem('token')
    const response = await axios.put('/api/users/profile', {
      full_name: profileForm.full_name
    }, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (response.data) {
      ElMessage.success('个人信息更新成功')
    }
  } catch (error: any) {
    ElMessage.error('更新失败: ' + (error.message || '未知错误'))
  } finally {
    profileLoading.value = false
  }
}

const changePassword = async () => {
  if (!passwordForm.old_password) {
    ElMessage.warning('请输入原密码')
    return
  }
  if (!passwordForm.new_password) {
    ElMessage.warning('请输入新密码')
    return
  }
  if (passwordForm.new_password.length < 6) {
    ElMessage.warning('新密码长度不能少于6位')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  
  passwordLoading.value = true
  try {
    const token = localStorage.getItem('token')
    await axios.post('/api/users/change-password', {
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    }, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    ElMessage.success('密码修改成功，请重新登录')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    
    setTimeout(() => {
      logout()
    }, 1500)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '密码修改失败')
  } finally {
    passwordLoading.value = false
  }
}

const logout = () => {
  localStorage.removeItem('token')
  userStore.logout()
  router.push('/login')
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: var(--color-bg-primary);
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

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: var(--color-bg-secondary);
  box-shadow: var(--shadow-sm);
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: var(--color-text-primary);
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
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

.user-info:hover {
  background: var(--color-bg-hover);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.user-name {
  color: var(--color-text-secondary);
}

.dropdown-arrow {
  color: var(--color-text-muted);
  font-size: 12px;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.profile-container {
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: row;
  gap: 24px;
}

.profile-card,
.password-card {
  flex: 1;
  min-width: 0;
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

.profile-form,
.password-form {
  max-width: 500px;
}
</style>
