<template>
  <div v-if="show" class="modal-overlay">
    <div class="modal">
      <div class="modal-header">
        <h3>上传文档到知识库</h3>
        <button class="close-button" @click="close">×</button>
      </div>
      
      <div class="modal-body">
        <div class="upload-area" 
             @dragover.prevent="dragOver = true"
             @dragleave="dragOver = false"
             @drop="handleDrop"
             :class="{ 'drag-over': dragOver }">
          <div class="upload-icon">📁</div>
          <p class="upload-text">拖拽文件到这里，或点击选择文件</p>
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".pdf,.docx,.doc,.txt,.md,.csv,.xlsx,.xls"
            @change="handleFileSelect"
            style="display: none"
          />
          <button class="secondary-button" @click="triggerFileInput">选择文件</button>
        </div>
        
        <div v-if="uploadedFiles.length > 0" class="file-list">
          <h4>已选择的文件</h4>
          <div v-for="(file, index) in uploadedFiles" :key="index" class="file-item">
            <div class="file-info">
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
            </div>
            <button class="remove-button" @click="removeFile(index)">×</button>
          </div>
        </div>
        
        <div class="upload-info">
          <p class="info-text">
            <strong>支持的文件类型：</strong>PDF, Word, TXT, Markdown, CSV, Excel
          </p>
          <p class="info-text">
            <strong>文件大小限制：</strong>单个文件不超过50MB
          </p>
        </div>
      </div>
      
      <div class="modal-footer">
        <button class="secondary-button" @click="close">取消</button>
        <button class="primary-button" @click="uploadFiles" :disabled="uploading || uploadedFiles.length === 0">
          <span v-if="uploading" class="loading-spinner"></span>
          上传文件
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

interface Props {
  show: boolean
  knowledgeBase: any
}

interface Emits {
  (e: 'update:show', value: boolean): void
  (e: 'uploaded'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 响应式数据
const fileInput = ref<HTMLInputElement>()
const dragOver = ref(false)
const uploadedFiles = ref<File[]>([])
const uploading = ref(false)

// 方法
const close = () => {
  emit('update:show', false)
  uploadedFiles.value = []
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files) {
    handleFiles(Array.from(input.files))
  }
}

const handleDrop = (event: DragEvent) => {
  dragOver.value = false
  if (event.dataTransfer?.files) {
    handleFiles(Array.from(event.dataTransfer.files))
  }
}

const handleFiles = (files: File[]) => {
  const validFiles = files.filter(file => {
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain',
      'text/markdown',
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
    
    const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt', '.md', '.csv', '.xlsx', '.xls']
    const fileExtension = '.' + file.name.toLowerCase().split('.').pop()
    
    return allowedTypes.includes(file.type) || allowedExtensions.includes(fileExtension)
  })
  
  const sizeValidFiles = validFiles.filter(file => file.size <= 50 * 1024 * 1024)
  
  if (validFiles.length !== files.length) {
    ElMessage.warning('部分文件类型不支持，已自动过滤')
  }
  
  if (sizeValidFiles.length !== validFiles.length) {
    ElMessage.warning('部分文件超过50MB限制，已自动过滤')
  }
  
  uploadedFiles.value = [...uploadedFiles.value, ...sizeValidFiles]
}

const removeFile = (index: number) => {
  uploadedFiles.value.splice(index, 1)
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const uploadFiles = async () => {
  uploading.value = true
  try {
    // 调用API上传文件
    for (const file of uploadedFiles.value) {
      const formData = new FormData()
      formData.append('file', file)
      
      // 调用后端API上传文件
      const response = await fetch(`/api/knowledge/${props.knowledgeBase.id}/files/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: formData
      })
      
      if (!response.ok) {
        throw new Error(`上传失败: ${response.statusText}`)
      }
      
      const result = await response.json()
    }
    
    emit('uploaded')
    close()
  } catch (error) {
    ElMessage.error('文件上传失败: ' + error.message)
    console.error(error)
  } finally {
    uploading.value = false
  }
}

// 监听对话框显示状态
watch(() => props.show, (newVal) => {
  if (!newVal) {
    uploadedFiles.value = []
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}

.close-button:hover {
  background: #f3f4f6;
  color: #374151;
}

.modal-body {
  padding: 24px;
}

.upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
}

.upload-area:hover,
.upload-area.drag-over {
  border-color: #1890ff;
  background-color: #f8fafc;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.upload-text {
  margin: 0 0 16px 0;
  color: #6b7280;
  font-size: 16px;
}

.file-list {
  margin-top: 24px;
}

.file-list h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  margin-bottom: 8px;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-name {
  font-weight: 500;
  color: #374151;
}

.file-size {
  font-size: 12px;
  color: #6b7280;
}

.remove-button {
  background: none;
  border: none;
  font-size: 18px;
  color: #6b7280;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.remove-button:hover {
  background: #f3f4f6;
  color: #374151;
}

.upload-info {
  margin-top: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 6px;
}

.info-text {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #6b7280;
}

.info-text:last-child {
  margin-bottom: 0;
}

.modal-footer {
  padding: 20px 24px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.primary-button, .secondary-button {
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  font-size: 14px;
}

.primary-button {
  background: #1890ff;
  color: white;
}

.primary-button:hover:not(:disabled) {
  background: #40a9ff;
}

.primary-button:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}

.secondary-button {
  background: #f3f4f6;
  color: #374151;
}

.secondary-button:hover {
  background: #e5e7eb;
}

.loading-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>