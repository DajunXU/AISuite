<template>
  <div class="permission-page">
    <div class="layout-container">
      <Sidebar />
      
      <div class="main-container">
        <PageHeader title="权限管理" />
        
        <main class="main-content">
          <div class="permission-management">
            <el-card shadow="hover" class="permission-card">
              <template #header>
                <div class="card-header">
                  <span>权限管理</span>
                </div>
              </template>
              
              <el-tabs v-model="activeTab" class="permission-tabs">
                <el-tab-pane label="角色管理" name="roles">
                  <div class="role-management">
                    <div class="role-header">
                      <el-button type="primary" @click="openRoleDialog">
                        <el-icon><Plus /></el-icon> 创建角色
                      </el-button>
                    </div>
                    
                    <el-table :data="roles" style="width: 100%">
                      <el-table-column prop="name" label="角色名称" width="180" />
                      <el-table-column prop="description" label="角色描述" />
                      <el-table-column prop="is_active" label="状态" width="100">
                        <template #default="scope">
                          <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                            {{ scope.row.is_active ? '启用' : '禁用' }}
                          </el-tag>
                        </template>
                      </el-table-column>
                      <el-table-column prop="created_at" label="创建时间" width="180">
                        <template #default="scope">
                          {{ formatDate(scope.row.created_at) }}
                        </template>
                      </el-table-column>
                      <el-table-column label="操作" width="320">
                        <template #default="scope">
                          <el-button size="small" @click="editRole(scope.row)">
                            <el-icon><Edit /></el-icon> 编辑
                          </el-button>
                          <el-button size="small" type="danger" @click="deleteRole(scope.row.id)">
                            <el-icon><Delete /></el-icon> 删除
                          </el-button>
                          <el-button size="small" type="primary" @click="assignPermissions(scope.row)">
                            <el-icon><Setting /></el-icon> 权限
                          </el-button>
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                </el-tab-pane>
                
                <el-tab-pane label="菜单管理" name="menus">
                  <div class="menu-management">
                    <div class="menu-header">
                      <el-button type="primary" @click="openMenuDialog">
                        <el-icon><Plus /></el-icon> 创建菜单
                      </el-button>
                    </div>
                    
                    <div class="menu-tree-wrapper">
                      <el-tree
                        :data="menuTree"
                        :props="menuTreeProps"
                        node-key="id"
                        default-expand-all
                        class="menu-tree"
                      >
                        <template #default="{ node, data }">
                          <div class="menu-tree-node">
                            <div class="menu-tree-node-left">
                              <span class="menu-tree-icon">{{ data.icon || '📁' }}</span>
                              <span class="menu-tree-label">{{ node.label }}</span>
                              <span class="menu-tree-path">{{ data.path }}</span>
                            </div>
                            <div class="menu-tree-node-right">
                              <el-tag :type="data.level === 1 ? 'success' : 'warning'" size="small">
                                {{ data.level === 1 ? '一级菜单' : '二级菜单' }}
                              </el-tag>
                              <el-tag :type="data.is_active ? 'success' : 'danger'" size="small">
                                {{ data.is_active ? '启用' : '禁用' }}
                              </el-tag>
                              <el-button size="small" text type="primary" @click.stop="editMenu(data)">
                                <el-icon><Edit /></el-icon>
                              </el-button>
                              <el-button size="small" text type="danger" @click.stop="deleteMenu(data.id)">
                                <el-icon><Delete /></el-icon>
                              </el-button>
                            </div>
                          </div>
                        </template>
                      </el-tree>
                    </div>
                  </div>
                </el-tab-pane>
                
                <el-tab-pane label="权限管理" name="permissions">
                  <div class="permission-config">
                    <div class="permission-config-left">
                      <div class="menu-tree-header">
                        <span class="menu-tree-title">选择菜单</span>
                      </div>
                      <el-tree
                        :data="menuTree"
                        :props="menuTreeProps"
                        node-key="id"
                        :expand-on-click-node="false"
                        :default-expand-all="true"
                        highlight-current
                        @node-click="handleMenuSelect"
                        class="permission-menu-tree"
                      >
                        <template #default="{ node, data }">
                          <div class="menu-tree-item">
                            <span class="menu-tree-item-icon">{{ data.icon || '📁' }}</span>
                            <span class="menu-tree-item-label">{{ node.label }}</span>
                          </div>
                        </template>
                      </el-tree>
                    </div>
                    
                    <div class="permission-config-right">
                      <div class="permission-header">
                        <div class="permission-header-left">
                          <span class="permission-title">{{ selectedMenu ? selectedMenu.name : '请选择菜单' }}</span>
                          <span class="permission-subtitle" v-if="selectedMenu">
                            {{ selectedMenu.path }}
                          </span>
                        </div>
                        <el-button 
                          type="primary" 
                          :disabled="!selectedMenu"
                          @click="openPermissionDialog"
                        >
                          <el-icon><Plus /></el-icon> 新增权限
                        </el-button>
                      </div>
                      
                      <div class="permission-list" v-if="selectedMenuPermissions.length > 0">
                        <div 
                          v-for="perm in selectedMenuPermissions" 
                          :key="perm.id" 
                          class="permission-item"
                          :class="{ 'is-active': perm.is_active }"
                        >
                          <div class="permission-item-info">
                            <div class="permission-item-main">
                              <span class="permission-item-name">{{ perm.name }}</span>
                              <el-switch 
                                v-model="perm.is_active" 
                                @change="togglePermission(perm)"
                                size="small"
                              />
                            </div>
                            <div class="permission-item-code">{{ perm.code }}</div>
                            <div class="permission-item-desc" v-if="perm.description">
                              {{ perm.description }}
                            </div>
                          </div>
                          <div class="permission-item-actions">
                            <el-button size="small" text type="primary" @click="editPermission(perm)">
                              <el-icon><Edit /></el-icon>
                            </el-button>
                            <el-button size="small" text type="danger" @click="deletePermission(perm.id)">
                              <el-icon><Delete /></el-icon>
                            </el-button>
                          </div>
                        </div>
                      </div>
                      
                      <el-empty 
                        v-else 
                        description="该菜单暂无权限，请点击" 
                        :image-size="80"
                      >
                        <template #default>
                          <div class="empty-tip">
                            点击上方"新增权限"按钮添加
                          </div>
                        </template>
                      </el-empty>
                    </div>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </el-card>
            
            <!-- 角色对话框 -->
            <el-dialog
              v-model="roleDialogVisible"
              :title="editingRole ? '编辑角色' : '创建角色'"
              width="500px"
            >
              <el-form :model="roleForm" label-width="80px">
                <el-form-item label="角色名称" required>
                  <el-input v-model="roleForm.name" placeholder="请输入角色名称" />
                </el-form-item>
                <el-form-item label="角色描述">
                  <el-input
                    v-model="roleForm.description"
                    type="textarea"
                    placeholder="请输入角色描述"
                    :rows="3"
                  />
                </el-form-item>
                <el-form-item label="状态">
                  <el-switch v-model="roleForm.is_active" />
                </el-form-item>
              </el-form>
              <template #footer>
                <span class="dialog-footer">
                  <el-button @click="roleDialogVisible = false">取消</el-button>
                  <el-button type="primary" @click="saveRole">保存</el-button>
                </span>
              </template>
            </el-dialog>
            
            <!-- 菜单对话框 -->
            <el-dialog
              v-model="menuDialogVisible"
              :title="editingMenu ? '编辑菜单' : '创建菜单'"
              width="500px"
            >
              <el-form :model="menuForm" label-width="80px">
                <el-form-item label="菜单名称" required>
                  <el-input v-model="menuForm.name" placeholder="请输入菜单名称" />
                </el-form-item>
                <el-form-item label="路由路径" required>
                  <el-input v-model="menuForm.path" placeholder="请输入路由路径" />
                </el-form-item>
                <el-form-item label="菜单图标">
                  <el-input v-model="menuForm.icon" placeholder="请输入菜单图标" />
                </el-form-item>
                <el-form-item label="父菜单">
                  <el-select v-model="menuForm.parent_id" placeholder="请选择父菜单">
                    <el-option label="顶级菜单" :value="null" />
                    <el-option
                      v-for="menu in rootMenus"
                      :key="menu.id"
                      :label="menu.name"
                      :value="menu.id"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="菜单级别">
                  <el-input-number v-model="menuForm.level" :min="1" :max="3" />
                </el-form-item>
                <el-form-item label="前端组件">
                  <el-input v-model="menuForm.component" placeholder="请输入前端组件路径" />
                </el-form-item>
                <el-form-item label="排序">
                  <el-input-number v-model="menuForm.sort" :min="0" />
                </el-form-item>
                <el-form-item label="状态">
                  <el-switch v-model="menuForm.is_active" />
                </el-form-item>
              </el-form>
              <template #footer>
                <span class="dialog-footer">
                  <el-button @click="menuDialogVisible = false">取消</el-button>
                  <el-button type="primary" @click="saveMenu">保存</el-button>
                </span>
              </template>
            </el-dialog>
            
            <!-- 权限对话框 -->
            <el-dialog
              v-model="permissionDialogVisible"
              :title="editingPermission ? '编辑权限' : '创建权限'"
              width="500px"
            >
              <el-form :model="permissionForm" label-width="80px">
                <el-form-item label="权限名称" required>
                  <el-input v-model="permissionForm.name" placeholder="请输入权限名称" />
                </el-form-item>
                <el-form-item label="权限编码" required>
                  <el-input v-model="permissionForm.code" placeholder="请输入权限编码" />
                </el-form-item>
                <el-form-item label="关联菜单">
                  <el-select 
                    v-model="permissionForm.menu_id" 
                    placeholder="请选择关联菜单"
                    :disabled="!!selectedMenu"
                  >
                    <el-option 
                      v-if="!selectedMenu" 
                      label="无关联菜单" 
                      :value="null" 
                    />
                    <el-option
                      v-for="menu in allMenus"
                      :key="menu.id"
                      :label="menu.name"
                      :value="menu.id"
                    />
                  </el-select>
                  <div v-if="selectedMenu" style="color: #909399; font-size: 12px; margin-top: 4px;">
                    已选择菜单：{{ selectedMenu.name }}
                  </div>
                </el-form-item>
                <el-form-item label="权限描述">
                  <el-input
                    v-model="permissionForm.description"
                    type="textarea"
                    placeholder="请输入权限描述"
                    :rows="3"
                  />
                </el-form-item>
                <el-form-item label="状态">
                  <el-switch v-model="permissionForm.is_active" />
                </el-form-item>
              </el-form>
              <template #footer>
                <span class="dialog-footer">
                  <el-button @click="permissionDialogVisible = false">取消</el-button>
                  <el-button type="primary" @click="savePermission">保存</el-button>
                </span>
              </template>
            </el-dialog>
            
            <!-- 权限分配对话框 -->
            <el-dialog
              v-model="permissionAssignDialogVisible"
              :title="`为角色分配权限 - ${selectedRole?.name}`"
              width="700px"
            >
              <div class="permission-tree-wrapper">
                <el-tree
                  ref="permissionTreeRef"
                  :data="permissionTreeData"
                  :props="permissionTreeProps"
                  show-checkbox
                  node-key="id"
                  :default-expand-all="true"
                  :expand-on-click-node="false"
                  @check="handlePermissionTreeCheck"
                  class="permission-tree"
                >
                  <template #default="{ node, data }">
                    <div class="permission-tree-item">
                      <span class="permission-tree-item-icon">{{ data.icon || (data.children ? '📁' : '🔐') }}</span>
                      <span class="permission-tree-item-label">{{ node.label }}</span>
                      <span v-if="!data.children" class="permission-tree-item-code">{{ data.code }}</span>
                    </div>
                  </template>
                </el-tree>
              </div>
              <template #footer>
                <div class="dialog-footer">
                  <span class="selected-count">已选择 {{ selectedPermissions.length }} 项权限</span>
                  <div class="dialog-footer-buttons">
                    <el-button @click="permissionAssignDialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="savePermissionAssign">保存</el-button>
                  </div>
                </div>
              </template>
            </el-dialog>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Plus, Edit, Delete, Setting } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getRoles, createRole, updateRole, deleteRole as deleteRoleApi, getMenus, createMenu, updateMenu, deleteMenu as deleteMenuApi, getPermissions, createPermission, updatePermission, deletePermission as deletePermissionApi, assignRolePermissions } from '@/utils/request'
import Sidebar from '@/components/Sidebar.vue'
import PageHeader from '@/components/PageHeader.vue'

const activeTab = ref('roles')
const roles = ref([])
const menus = ref([])
const permissions = ref([])
const selectedMenu = ref(null)

const menuTreeProps = {
  children: 'children',
  label: 'name'
}

const roleDialogVisible = ref(false)
const menuDialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const permissionAssignDialogVisible = ref(false)

const editingRole = ref(null)
const editingMenu = ref(null)
const editingPermission = ref(null)
const selectedRole = ref(null)

const roleForm = reactive({
  name: '',
  description: '',
  is_active: true
})

const menuForm = reactive({
  name: '',
  path: '',
  icon: '',
  parent_id: null,
  level: 1,
  component: '',
  sort: 0,
  is_active: true
})

const permissionForm = reactive({
  name: '',
  code: '',
  menu_id: null,
  description: '',
  is_active: true
})

const selectedPermissions = ref([])

const permissionTreeRef = ref(null)

const permissionTreeProps = {
  children: 'children',
  label: 'name'
}

const permissionTreeData = computed(() => {
  const tree = []
  
  menus.value
    .filter(menu => menu.parent_id === null)
    .forEach(menu => {
      const menuNode = {
        id: `menu_${menu.id}`,
        name: menu.name,
        icon: menu.icon,
        children: []
      }
      
      const childMenus = menus.value.filter(m => m.parent_id === menu.id)
      childMenus.forEach(childMenu => {
        const childMenuNode = {
          id: `menu_${childMenu.id}`,
          name: childMenu.name,
          icon: childMenu.icon,
          children: []
        }
        
        const menuPermissions = permissions.value.filter(p => p.menu_id === childMenu.id)
        menuPermissions.forEach(perm => {
          childMenuNode.children.push({
            id: perm.id,
            name: perm.name,
            code: perm.code,
            is_permission: true
          })
        })
        
        if (childMenuNode.children.length > 0) {
          menuNode.children.push(childMenuNode)
        }
      })
      
      const directPermissions = permissions.value.filter(p => p.menu_id === menu.id)
      directPermissions.forEach(perm => {
        menuNode.children.push({
          id: perm.id,
          name: perm.name,
          code: perm.code,
          is_permission: true
        })
      })
      
      if (menuNode.children.length > 0 || directPermissions.length > 0) {
        tree.push(menuNode)
      }
    })
  
  return tree
})

const handlePermissionTreeCheck = (data, checkedData) => {
  const checkedIds = [
    ...checkedData.checkedKeys,
    ...checkedData.halfCheckedKeys
  ].filter(id => typeof id === 'number' || id.startsWith('perm_'))
    .map(id => typeof id === 'number' ? id : parseInt(id.replace('perm_', '')))
  
  selectedPermissions.value = checkedIds
}

const selectedMenuPermissions = computed(() => {
  if (!selectedMenu.value) return []
  return permissions.value.filter(p => p.menu_id === selectedMenu.value.id)
})

const menuTree = computed(() => {
  const tree = []
  const menuMap = {}
  
  menus.value.forEach(menu => {
    menuMap[menu.id] = { ...menu, children: [] }
  })
  
  menus.value.forEach(menu => {
    if (menu.parent_id === null) {
      tree.push(menuMap[menu.id])
    } else if (menuMap[menu.parent_id]) {
      menuMap[menu.parent_id].children.push(menuMap[menu.id])
    }
  })
  
  return tree
})

const rootMenus = computed(() => {
  return menus.value.filter(menu => menu.parent_id === null)
})

const allMenus = computed(() => {
  return menus.value
})

const loadRoles = async () => {
  try {
    const response = await getRoles()
    roles.value = response
  } catch (error) {
    ElMessage.error('加载角色失败')
    console.error('加载角色失败:', error)
  }
}

const loadMenus = async () => {
  try {
    const response = await getMenus()
    menus.value = response.menus.flatMap(menu => {
      const flatten = [menu]
      if (menu.children) {
        menu.children.forEach(child => {
          flatten.push(child)
        })
      }
      return flatten
    })
  } catch (error) {
    ElMessage.error('加载菜单失败')
    console.error('加载菜单失败:', error)
  }
}

const handleMenuSelect = (data) => {
  selectedMenu.value = data
}

const togglePermission = async (permission) => {
  try {
    await updatePermission(permission.id, {
      name: permission.name,
      code: permission.code,
      menu_id: permission.menu_id,
      description: permission.description,
      is_active: permission.is_active
    })
    ElMessage.success('权限状态已更新')
  } catch (error) {
    ElMessage.error('更新权限失败')
    console.error('更新权限失败:', error)
    permission.is_active = !permission.is_active
  }
}

const loadPermissions = async () => {
  try {
    const response = await getPermissions()
    permissions.value = response.permissions
  } catch (error) {
    ElMessage.error('加载权限失败')
    console.error('加载权限失败:', error)
  }
}

const openRoleDialog = () => {
  editingRole.value = null
  Object.assign(roleForm, {
    name: '',
    description: '',
    is_active: true
  })
  roleDialogVisible.value = true
}

const editRole = (role) => {
  editingRole.value = role
  Object.assign(roleForm, {
    name: role.name,
    description: role.description,
    is_active: role.is_active
  })
  roleDialogVisible.value = true
}

const saveRole = async () => {
  try {
    if (editingRole.value) {
      await updateRole(editingRole.value.id, roleForm)
      ElMessage.success('角色更新成功')
    } else {
      await createRole(roleForm)
      ElMessage.success('角色创建成功')
    }
    roleDialogVisible.value = false
    await loadRoles()
  } catch (error) {
    ElMessage.error('保存角色失败')
    console.error('保存角色失败:', error)
  }
}

const deleteRole = async (roleId) => {
  try {
    await ElMessageBox.confirm('确定要删除该角色吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteRoleApi(roleId)
    ElMessage.success('角色删除成功')
    await loadRoles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除角色失败')
      console.error('删除角色失败:', error)
    }
  }
}

const openMenuDialog = () => {
  editingMenu.value = null
  Object.assign(menuForm, {
    name: '',
    path: '',
    icon: '',
    parent_id: null,
    level: 1,
    component: '',
    sort: 0,
    is_active: true
  })
  menuDialogVisible.value = true
}

const editMenu = (menu) => {
  editingMenu.value = menu
  Object.assign(menuForm, {
    name: menu.name,
    path: menu.path,
    icon: menu.icon,
    parent_id: menu.parent_id,
    level: menu.level,
    component: menu.component,
    sort: menu.sort,
    is_active: menu.is_active
  })
  menuDialogVisible.value = true
}

const saveMenu = async () => {
  try {
    if (editingMenu.value) {
      await updateMenu(editingMenu.value.id, menuForm)
      ElMessage.success('菜单更新成功')
    } else {
      await createMenu(menuForm)
      ElMessage.success('菜单创建成功')
    }
    menuDialogVisible.value = false
    await loadMenus()
  } catch (error) {
    ElMessage.error('保存菜单失败')
    console.error('保存菜单失败:', error)
  }
}

const deleteMenu = async (menuId) => {
  try {
    await ElMessageBox.confirm('确定要删除该菜单吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deleteMenuApi(menuId)
    ElMessage.success('菜单删除成功')
    await loadMenus()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除菜单失败')
      console.error('删除菜单失败:', error)
    }
  }
}

const openPermissionDialog = () => {
  editingPermission.value = null
  Object.assign(permissionForm, {
    name: '',
    code: '',
    menu_id: selectedMenu.value ? selectedMenu.value.id : null,
    description: '',
    is_active: true
  })
  permissionDialogVisible.value = true
}

const editPermission = (permission) => {
  editingPermission.value = permission
  Object.assign(permissionForm, {
    name: permission.name,
    code: permission.code,
    menu_id: permission.menu_id,
    description: permission.description,
    is_active: permission.is_active
  })
  permissionDialogVisible.value = true
}

const savePermission = async () => {
  try {
    if (editingPermission.value) {
      await updatePermission(editingPermission.value.id, permissionForm)
      ElMessage.success('权限更新成功')
    } else {
      await createPermission(permissionForm)
      ElMessage.success('权限创建成功')
    }
    permissionDialogVisible.value = false
    await loadPermissions()
  } catch (error) {
    ElMessage.error('保存权限失败')
    console.error('保存权限失败:', error)
  }
}

const deletePermission = async (permissionId) => {
  try {
    await ElMessageBox.confirm('确定要删除该权限吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await deletePermissionApi(permissionId)
    ElMessage.success('权限删除成功')
    await loadPermissions()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除权限失败')
      console.error('删除权限失败:', error)
    }
  }
}

const assignPermissions = (role) => {
  selectedRole.value = role
  selectedPermissions.value = role.permission_ids || []
  
  setTimeout(() => {
    if (permissionTreeRef.value) {
      const checkedKeys = role.permission_ids || []
      permissionTreeRef.value.setCheckedKeys(checkedKeys)
    }
  }, 100)
  
  permissionAssignDialogVisible.value = true
}

const savePermissionAssign = async () => {
  try {
    await assignRolePermissions(selectedRole.value.id, {
      permission_ids: selectedPermissions.value
    })
    ElMessage.success('权限分配成功')
    permissionAssignDialogVisible.value = false
    await loadRoles()
  } catch (error) {
    ElMessage.error('权限分配失败')
    console.error('权限分配失败:', error)
  }
}

onMounted(async () => {
  await loadRoles()
  await loadMenus()
  await loadPermissions()
})

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}
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
  overflow: hidden;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 36px;
}

.permission-management {
  max-width: 1400px;
  margin: 0 auto;
}

.permission-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.role-header,
.menu-header,
.permission-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.permission-header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.permission-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.permission-subtitle {
  font-size: 12px;
  color: #909399;
}

.permission-config {
  display: flex;
  gap: 20px;
  min-height: 500px;
}

.permission-config-left {
  width: 280px;
  flex-shrink: 0;
  background: white;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid #ebeef5;
}

.menu-tree-header {
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 12px;
}

.menu-tree-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.permission-menu-tree {
  background: transparent;
}

.menu-tree-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.menu-tree-item-icon {
  font-size: 14px;
}

.menu-tree-item-label {
  font-size: 14px;
}

.permission-config-right {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #ebeef5;
}

.permission-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.permission-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all 0.3s ease;
}

.permission-item:hover {
  border-color: #409eff;
  background: #ecf5ff;
}

.permission-item.is-active {
  background: #f0f9eb;
  border-color: #67c23a;
}

.permission-item-info {
  flex: 1;
}

.permission-item-main {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.permission-item-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.permission-item-code {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
  background: #e4e7ed;
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-bottom: 4px;
}

.permission-item-desc {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
}

.permission-item-actions {
  display: flex;
  gap: 8px;
}

.empty-tip {
  color: #909399;
  font-size: 14px;
}

.menu-tree-wrapper {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #ebeef5;
}

.menu-tree {
  background: transparent;
}

:deep(.el-tree-node__content) {
  height: auto;
  padding: 12px 8px;
  border-radius: 8px;
  margin-bottom: 4px;
  transition: all 0.3s ease;
}

:deep(.el-tree-node__content:hover) {
  background: #f5f7fa;
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: #e6f7ff;
}

.menu-tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 16px;
}

.menu-tree-node-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.menu-tree-icon {
  font-size: 20px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f6ff 0%, #e6f7ff 100%);
  border-radius: 8px;
}

.menu-tree-label {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.menu-tree-path {
  font-size: 13px;
  color: #909399;
  font-family: 'Monaco', 'Menlo', monospace;
  background: #f5f7fa;
  padding: 2px 10px;
  border-radius: 4px;
}

.menu-tree-node-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.permission-tabs {
  margin-top: 20px;
}

:deep(.el-table .cell) {
  word-break: break-word;
}

:deep(.el-button + .el-button) {
  margin-left: 8px;
}

.permission-tree-wrapper {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  background: #fafafa;
}

.permission-tree {
  background: transparent;
}

.permission-tree-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.permission-tree-item-icon {
  font-size: 14px;
}

.permission-tree-item-label {
  font-size: 14px;
  color: #303133;
}

.permission-tree-item-code {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
  background: #e4e7ed;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: auto;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.selected-count {
  font-size: 14px;
  color: #606266;
}

.dialog-footer-buttons {
  display: flex;
  gap: 12px;
}
</style>
