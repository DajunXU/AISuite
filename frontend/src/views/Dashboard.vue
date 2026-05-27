<template>
  <div class="dashboard">
    <div class="layout-container">
      <Sidebar />
      
      <div class="main-container">
        <PageHeader title="仪表盘" />
        
        <main class="main-content">
          <!-- 统计卡片 -->
          <div class="stats-section">
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-content">
                  <div class="stat-icon knowledge-icon">📁</div>
                  <div class="stat-info">
                    <div class="stat-value">{{ stats.knowledgeBases }}</div>
                    <div class="stat-label">知识库数量</div>
                  </div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-content">
                  <div class="stat-icon chat-icon">💬</div>
                  <div class="stat-info">
                    <div class="stat-value">{{ stats.chatMessages }}</div>
                    <div class="stat-label">对话数量</div>
                  </div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-content">
                  <div class="stat-icon user-icon">👥</div>
                  <div class="stat-info">
                    <div class="stat-value">{{ stats.activeUsers }}</div>
                    <div class="stat-label">活跃用户</div>
                  </div>
                </div>
              </div>
              
              <div class="stat-card">
                <div class="stat-content">
                  <div class="stat-icon document-icon">📄</div>
                  <div class="stat-info">
                    <div class="stat-value">{{ stats.documents }}</div>
                    <div class="stat-label">文档数量</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="recent-activities">
            <div class="activity-card">
              <div class="card-header">
                <h3>最近活动</h3>
              </div>
              
              <div class="activity-list">
                <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
                  <div class="activity-time">{{ activity.time }}</div>
                  <div class="activity-content">{{ activity.content }}</div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { usePermissionStore } from '@/stores/permission'
import request from '@/utils/request'
import Sidebar from '@/components/Sidebar.vue'
import PageHeader from '@/components/PageHeader.vue'

const router = useRouter()
const userStore = useUserStore()
const permissionStore = usePermissionStore()

const stats = ref({
  knowledgeBases: 0,
  chatMessages: 0,
  activeUsers: 0,
  documents: 0
})

const recentActivities = ref([
  {
    id: 1,
    time: '2024-01-15 14:30',
    content: '创建了新的知识库 "产品文档"'
  },
  {
    id: 2,
    time: '2024-01-15 10:15',
    content: '上传了文档 "用户手册.pdf"'
  },
  {
    id: 3,
    time: '2024-01-14 16:45',
    content: '进行了智能对话，询问产品功能'
  }
])

onMounted(async () => {
  await permissionStore.loadUserPermissions()
  
  try {
    const res = await request.get('/chat/stats')
    stats.value = res.stats || res.data?.stats || {}
    recentActivities.value = (res.recentActivities || res.data?.recentActivities || []).map((a: any) => ({
      id: a.id,
      time: a.time,
      content: a.content
    }))
  } catch (error) {
    console.error('加载统计数据失败:', error)
    stats.value = {
      knowledgeBases: 0,
      chatMessages: 0,
      activeUsers: 0,
      documents: 0
    }
  }
})
</script>

<style scoped>
/* bigmodel.cn 风格 - 清新现代 */
.dashboard {
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, var(--color-bg-primary) 0%, var(--color-bg-tertiary) 100%);
  font-family: var(--font-family);
  line-height: 1.6;
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

.main-content {
  flex: 1;
  padding: 32px;
  background: transparent;
  overflow-y: auto;
}

.stats-section {
  margin-bottom: 32px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 24px;
}

.stat-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
  border: 1px solid var(--color-border-light);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-accent-light);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 24px;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--color-accent-subtle);
  color: var(--color-accent);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-accent);
  line-height: 1.2;
  margin-bottom: 4px;
  letter-spacing: -0.5px;
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-tertiary);
  font-weight: 500;
}

.recent-activities {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border-light);
}

.card-header {
  margin-bottom: 20px;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.2px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border-light);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-time {
  font-size: 13px;
  color: var(--color-text-muted);
  min-width: 130px;
  font-weight: 500;
  line-height: 1.4;
}

.activity-content {
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  flex: 1;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>