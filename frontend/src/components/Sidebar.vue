<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h3><span>AI</span> 知识库</h3>
    </div>
    
    <nav class="sidebar-menu">
      <template v-if="permissionStore.menus && permissionStore.menus.length > 0">
        <template v-for="menu in permissionStore.menus" :key="menu.path">
          <!-- 一级菜单 -->
          <div 
            v-if="!menu.children || menu.children.length === 0"
            :class="['menu-item', isActive(menu.path) ? 'active' : '']"
            @click="navigate(menu.path)"
          >
            <span class="menu-icon">{{ menu.icon || '📄' }}</span>
            <span class="menu-text">{{ menu.name }}</span>
          </div>
          
          <!-- 有子菜单的一级菜单 -->
          <div v-else class="menu-group">
            <div 
              :class="['menu-item', isActive(menu.path) || hasActiveChild(menu.children) ? 'active' : '', expandedMenus[menu.path] ? 'expanded' : '']"
              @click="toggleSubmenu(menu.path)"
            >
              <span class="menu-icon">{{ menu.icon || '📁' }}</span>
              <span class="menu-text">{{ menu.name }}</span>
              <span class="menu-arrow">▶</span>
            </div>
            
            <!-- 子菜单 -->
            <div v-show="expandedMenus[menu.path]" class="submenu">
              <div 
                v-for="child in menu.children" 
                :key="child.path"
                :class="['submenu-item', isActive(child.path) ? 'active' : '']"
                @click.stop="navigate(child.path)"
              >
                <span class="menu-icon">{{ child.icon || '📄' }}</span>
                <span class="menu-text">{{ child.name }}</span>
              </div>
            </div>
          </div>
        </template>
      </template>
      <div v-else class="no-menu">
        <span v-if="permissionStore.loading">加载中...</span>
        <span v-else>暂无可用菜单</span>
      </div>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRoute } from 'vue-router'
import { usePermissionStore } from '@/stores/permission'

const route = useRoute()
const permissionStore = usePermissionStore()

const expandedMenus = reactive<Record<string, boolean>>({})

const isActive = (path: string) => {
  return route.path === path || route.path.startsWith(path + '/')
}

const hasActiveChild = (children: any[]) => {
  return children?.some((child: any) => isActive(child.path))
}

const toggleSubmenu = (path: string) => {
  expandedMenus[path] = !expandedMenus[path]
}

const navigate = (path: string) => {
  if (path) {
    window.location.href = path
  }
}

watch(() => route.path, (newPath) => {
  permissionStore.menus.forEach((menu: any) => {
    if (menu.children && menu.children.length > 0) {
      const hasActive = menu.children.some((child: any) => 
        newPath === child.path || newPath.startsWith(child.path + '/')
      )
      if (hasActive) {
        expandedMenus[menu.path] = true
      }
    }
  })
}, { immediate: true })
</script>

<style scoped>
.sidebar {
  width: 240px;
  height: 100vh;
  background: var(--color-bg-secondary);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--color-border);
  flex-shrink: 0;
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid var(--color-border-light);
}

.sidebar-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.3px;
}

.sidebar-header h3 span {
  color: var(--color-accent);
}

.sidebar-menu {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: all var(--transition-fast);
  border-radius: var(--radius-md);
  font-size: 14px;
  cursor: pointer;
  position: relative;
}

.menu-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  background: var(--color-accent);
  border-radius: 0 2px 2px 0;
  transition: height var(--transition-fast);
}

.menu-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-primary);
}

.menu-item.active {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  font-weight: 500;
}

.menu-item.active::before {
  height: 20px;
}

.menu-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.menu-text {
  flex: 1;
}

.menu-arrow {
  font-size: 10px;
  color: var(--color-text-muted);
  transition: transform var(--transition-fast);
}

.menu-group .menu-item .menu-arrow {
  transform: rotate(0deg);
}

.menu-group .menu-item.expanded .menu-arrow {
  transform: rotate(90deg);
}

.menu-group {
  position: relative;
}

.submenu {
  padding-left: 20px;
  margin-top: 4px;
}

.submenu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  color: var(--color-text-tertiary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--transition-fast);
  border-radius: var(--radius-md);
}

.submenu-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-text-secondary);
}

.submenu-item.active {
  color: var(--color-accent);
  background: var(--color-accent-subtle);
  font-weight: 500;
}

.no-menu {
  padding: 20px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 14px;
}
</style>
