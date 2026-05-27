<template>
  <header class="page-header">
    <div class="header-left">
      <h2>{{ title }}</h2>
    </div>
    
    <div class="header-right">
      <div class="user-dropdown" @click="showDropdown = !showDropdown">
        <div class="user-info">
          <div class="user-avatar">{{ userStore.user?.username?.charAt(0) }}</div>
          <span class="user-name">{{ userStore.user?.username }}</span>
          <span class="dropdown-arrow">▼</span>
        </div>
        <div class="dropdown-menu" v-show="showDropdown" @click.stop="handleLogout">
          <button class="dropdown-item">退出登录</button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

defineProps<{
  title: string
}>()

const router = useRouter()
const userStore = useUserStore()
const showDropdown = ref(false)

const handleLogout = async () => {
  showDropdown.value = false
  await userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.page-header {
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border-light);
  padding: 0 32px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--shadow-sm);
  flex-shrink: 0;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.user-dropdown {
  position: relative;
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  border-radius: var(--radius-md);
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
</style>
