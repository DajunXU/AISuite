<template>
  <div class="page-layout">
    <div class="layout-container">
      <Sidebar />
      
      <div class="main-container">
        <header class="page-header">
          <div class="header-left">
            <h2>{{ title }}</h2>
          </div>
          
          <div class="header-right">
            <div class="user-dropdown">
              <div class="user-info" @click="showDropdown = !showDropdown">
                <div class="user-avatar">{{ userStore.user?.username?.charAt(0) }}</div>
                <span class="user-name">{{ userStore.user?.username }}</span>
                <span class="dropdown-arrow">▼</span>
              </div>
              <div class="dropdown-menu" v-show="showDropdown" @click="showDropdown = false">
                <button class="dropdown-item" @click="logout">退出登录</button>
              </div>
            </div>
          </div>
        </header>
        
        <main class="page-content">
          <slot></slot>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import Sidebar from '@/components/Sidebar.vue'

defineProps<{
  title: string
}>()

const router = useRouter()
const userStore = useUserStore()
const showDropdown = ref(false)

const logout = async () => {
  await userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.page-layout {
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, var(--color-bg-primary) 0%, var(--color-bg-tertiary) 100%);
  font-family: var(--font-family);
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

.page-header {
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
  padding: 0 32px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--shadow-sm);
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.user-dropdown {
  position: relative;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
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
  font-size: 15px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.dropdown-arrow {
  font-size: 10px;
  color: var(--color-text-muted);
  transition: transform var(--transition-fast);
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
  z-index: 100;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-8px);
  transition: all var(--transition-normal);
}

.user-dropdown:hover .dropdown-menu,
.dropdown-menu:hover {
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

.page-content {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
}
</style>
