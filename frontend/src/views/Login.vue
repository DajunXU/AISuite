<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="login-title"><span>AI</span> 知识库</h2>
      
      <div class="tab-container">
        <div class="tab-header">
          <button 
            :class="['tab-button', activeTab === 'login' ? 'active' : '']"
            @click="activeTab = 'login'"
          >
            登录
          </button>
          <button 
            :class="['tab-button', activeTab === 'register' ? 'active' : '']"
            @click="activeTab = 'register'"
          >
            注册
          </button>
        </div>
        
        <!-- 登录表单 -->
        <div v-if="activeTab === 'login'" class="form-content">
          <div class="input-group">
            <input
              v-model="loginForm.username"
              type="text"
              placeholder="用户名"
              class="custom-input"
              @focus="onInputFocus"
              @blur="onInputBlur"
            />
          </div>
          
          <div class="input-group">
            <input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              class="custom-input"
              @focus="onInputFocus"
              @blur="onInputBlur"
            />
          </div>
          
          <button
            class="login-button"
            :disabled="loading"
            @click="handleLogin"
          >
            <span v-if="!loading">登录</span>
            <span v-else class="loading-text">登录中...</span>
          </button>
        </div>
        
        <!-- 注册表单 -->
        <div v-if="activeTab === 'register'" class="form-content">
          <div class="input-group">
            <input
              v-model="registerForm.username"
              type="text"
              placeholder="用户名"
              class="custom-input"
              @focus="onInputFocus"
              @blur="onInputBlur"
            />
          </div>
            
          <div class="input-group">
            <input
              v-model="registerForm.email"
              type="email"
              placeholder="邮箱"
              class="custom-input"
              @focus="onInputFocus"
              @blur="onInputBlur"
            />
          </div>
          
          <div class="input-group">
            <input
              v-model="registerForm.password"
              type="password"
              placeholder="密码"
              class="custom-input"
              @focus="onInputFocus"
              @blur="onInputBlur"
            />
          </div>
          
          <div class="input-group">
            <input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="确认密码"
              class="custom-input"
              @focus="onInputFocus"
              @blur="onInputBlur"
            />
          </div>
          
          <button
            class="login-button"
            :disabled="loading"
            @click="handleRegister"
          >
            <span v-if="!loading">注册</span>
            <span v-else class="loading-text">注册中...</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('login')
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 输入框焦点状态
const onInputFocus = (event: Event) => {
  const input = event.target as HTMLInputElement
  input.parentElement?.classList.add('focused')
}

const onInputBlur = (event: Event) => {
  const input = event.target as HTMLInputElement
  input.parentElement?.classList.remove('focused')
}

const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  
  try {
    loading.value = true
    await userStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!registerForm.username || !registerForm.email || !registerForm.password || !registerForm.confirmPassword) {
    ElMessage.warning('请填写所有必填字段')
    return
  }
  
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.warning('两次输入密码不一致')
    return
  }
  
  try {
    loading.value = true
    await userStore.register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password
    })
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    // 清空注册表单
    Object.assign(registerForm, {
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8f9fb 0%, #eef2f7 50%, #f5f7fa 100%);
  padding: 20px;
  position: relative;
}

.login-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: 48px;
  width: 100%;
  max-width: 420px;
  min-height: 520px;
  display: flex;
  flex-direction: column;
}

.login-title {
  text-align: center;
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 40px 0;
  color: var(--color-text-primary);
  letter-spacing: -0.5px;
}

.login-title span {
  color: var(--color-accent);
}

.tab-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.tab-header {
  display: flex;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-md);
  padding: 4px;
  margin-bottom: 32px;
}

.tab-button {
  flex: 1;
  padding: 12px 20px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-normal);
}

.tab-button.active {
  background: var(--color-bg-card);
  color: var(--color-accent);
  box-shadow: var(--shadow-sm);
}

.tab-button:hover:not(.active) {
  color: var(--color-text-primary);
}

.form-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group {
  position: relative;
}

.custom-input {
  width: 100%;
  height: 52px;
  padding: 0 18px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-bg-secondary);
  font-size: 15px;
  color: var(--color-text-primary);
  transition: all var(--transition-normal);
  outline: none;
}

.custom-input::placeholder {
  color: var(--color-text-muted);
}

.custom-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-light);
}

.login-button {
  width: 100%;
  height: 52px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--color-accent);
  color: white;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-normal);
  margin-top: 12px;
}

.login-button:hover:not(:disabled) {
  background: var(--color-accent-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
</style>