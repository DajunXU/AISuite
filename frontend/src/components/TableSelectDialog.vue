<template>
  <el-dialog
    v-model="dialogVisible"
    title="选择要配置的表"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="table-list">
      <div
        v-for="table in tables"
        :key="table.table_name"
        :class="['table-item', { selected: selectedTable?.table_name === table.table_name, 'not-saved': !table.id }]"
        @click="handleSelect(table)"
      >
        <div class="table-info">
          <span class="table-name">{{ table.table_name }}</span>
          <span v-if="table.id" class="saved-tag">✓ 已保存</span>
          <span v-else class="unsaved-tag">需保存</span>
        </div>
        <div v-if="table.columns && table.columns.length > 0" class="column-count">
          {{ table.columns.length }} 个字段
        </div>
      </div>
    </div>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :disabled="!selectedTable" @click="handleConfirm">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{
  show: boolean
  tables: any[]
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
  (e: 'select', table: any): void
}>()

const dialogVisible = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const selectedTable = ref<any>(null)

watch(() => props.show, (val) => {
  if (val) {
    selectedTable.value = null
  }
})

const handleSelect = (table: any) => {
  selectedTable.value = table
}

const handleConfirm = () => {
  if (selectedTable.value) {
    if (!selectedTable.value.id) {
      ElMessage.warning('该表尚未保存，请先保存数据源')
      return
    }
    emit('select', selectedTable.value)
    handleClose()
  }
}

const handleClose = () => {
  dialogVisible.value = false
}
</script>

<style scoped>
.table-list {
  max-height: 400px;
  overflow-y: auto;
}

.table-item {
  padding: 12px 16px;
  margin-bottom: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.table-item:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.table-item.selected {
  border-color: #409eff;
  background: #ecf5ff;
}

.table-item.not-saved {
  opacity: 0.7;
}

.table-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.table-name {
  font-weight: 500;
  color: #303133;
}

.saved-tag {
  color: #67c23a;
  font-size: 12px;
}

.unsaved-tag {
  color: #909399;
  font-size: 12px;
}

.column-count {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
</style>
