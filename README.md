# AISuite

简体中文 | [English](./README_EN.md)

**AISuite（AI套件）** 是一款面向中大型企业的**企业AI应用平台**，以知识库智能问答为第一个模块，未来可扩展数据分析、流程助手等模块，帮助企业构建完整的 AI 能力矩阵。

## 当前功能

### 📚 文档知识库问答
支持 PDF、Word、TXT、Markdown 等文档上传，自动向量化存储与语义检索

### 📊 数据库自然语言查询
连接业务数据库，通过自然语言转 SQL 进行智能数据查询

### 💬 对话管理与公开分享
多会话支持、对话收藏、公开链接分享（无需登录即可咨询）

### 🔐 权限管理与审计日志
基于角色的权限控制，支持菜单权限和数据隔离；完整操作审计记录

## 技术栈

### 后端

| 技术 | 说明 |
|------|------|
| FastAPI | 高性能 Python Web 框架 |
| PostgreSQL + pgvector | 向量数据库，支持语义检索 |
| SQLAlchemy + Alembic | ORM 与数据库迁移 |
| LangChain | LLM 应用开发框架 |
| JWT | 用户认证与授权 |
| Pydantic | 数据验证与配置管理 |

### 前端

| 技术 | 说明 |
|------|------|
| Vue 3 + TypeScript | 现代前端开发框架 |
| Element Plus | 企业级 UI 组件库 |
| Pinia | 状态管理 |
| Vite | 快速构建工具 |
| Axios | HTTP 客户端 |

## 项目架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (Vue3)                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │  Dashboard │  │ Knowledge │  │   Chat   │  │  Admin   │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
└─────────────────────────────────────────────────────────┘
                           │ HTTP + JWT
┌─────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                    │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │   Auth   │  │Knowledge │  │   Chat   │  │Permission│ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │
│                         │                              │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Services (RAG/SQL/Agent)            │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                    PostgreSQL + pgvector               │
└─────────────────────────────────────────────────────────┘
```

## 目录结构

```
AISuite/
├── backend/                    # 后端项目
│   ├── app/
│   │   ├── api/
│   │   │   ├── endpoints/     # API 端点
│   │   │   │   ├── auth.py           # 认证接口
│   │   │   │   ├── users.py          # 用户管理
│   │   │   │   ├── knowledge.py      # 知识库管理
│   │   │   │   ├── chat.py           # 智能对话
│   │   │   │   ├── llm.py            # 大模型管理
│   │   │   │   ├── embedding.py      # Embedding 模型管理
│   │   │   │   ├── permission.py     # 权限管理
│   │   │   │   ├── audit.py          # 审计日志
│   │   │   │   ├── kb_stats.py       # 知识库统计
│   │   │   │   └── public_dialog.py  # 公开对话
│   │   │   └── deps.py       # 依赖注入
│   │   ├── core/             # 核心配置
│   │   │   ├── config.py     # 配置管理
│   │   │   ├── database.py   # 数据库连接
│   │   │   ├── security.py   # 安全工具
│   │   │   └── logger.py     # 日志配置
│   │   ├── models/           # 数据模型
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # 业务逻辑
│   │   │   ├── rag.py        # RAG 服务
│   │   │   ├── sql_agent.py  # SQL 代理
│   │   │   ├── file_processor.py   # 文件处理
│   │   │   ├── document.py   # 文档管理
│   │   │   ├── intent_classifier.py # 意图分类
│   │   │   ├── database_service.py  # 数据库服务
│   │   │   ├── audit_service.py     # 审计日志
│   │   │   ├── cache.py      # 缓存服务
│   │   │   ├── vectorization_task.py # 向量化任务
│   │   │   ├── agent.py      # Agent 核心
│   │   │   ├── agent_service.py    # Agent 服务
│   │   │   └── agent_tools.py      # Agent 工具集
│   │   └── main.py           # 应用入口
│   ├── uploads/              # 上传文件目录
│   ├── requirements.txt      # Python 依赖
│   ├── init_db.py           # 数据库初始化
│   ├── database_schema.sql  # 数据库建表脚本
│   └── alembic/              # 数据库迁移
│
├── frontend/                 # 前端项目
│   ├── src/
│   │   ├── components/      # 公共组件
│   │   │   ├── Sidebar.vue
│   │   │   ├── FileUploadDialog.vue
│   │   │   ├── DatabaseConfigDialog.vue
│   │   │   └── ...
│   │   ├── views/           # 页面组件
│   │   │   ├── Login.vue
│   │   │   ├── Dashboard.vue
│   │   │   ├── KnowledgeBase.vue
│   │   │   ├── KnowledgeBaseDetail.vue
│   │   │   ├── KnowledgeBaseAuthority.vue
│   │   │   ├── Chat.vue
│   │   │   ├── LLMManagement.vue
│   │   │   └── Admin/
│   │   │       ├── Admin.vue
│   │   │       └── PermissionManagement.vue
│   │   ├── stores/           # Pinia 状态管理
│   │   ├── router/          # 路由配置
│   │   ├── utils/           # 工具函数
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   ├── vite.config.ts
│   └── .env
│
├── docker-compose.yml         # Docker 编排配置
├── README.md                  # 中文说明
└── README_EN.md               # English
```

## 环境要求

- **Python**: 3.10+
- **Node.js**: 18+
- **PostgreSQL**: 14+ (需要 pgvector 扩展)

## 快速开始

### 1. Docker 部署（推荐）

```bash
# 克隆项目
git clone <your-repo-url>
cd AISuite

# 启动所有服务
docker-compose up -d

# 访问服务
# - 前端: http://localhost:3000
# - 后端: http://localhost:8000
# - API文档: http://localhost:8000/docs
```

默认测试账号：
- 用户名：`test`
- 密码：`test123`

### 2. 手动部署

#### 2.1 数据库初始化

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建数据库（PostgreSQL）
createdb aisuite -U postgres

# 导入数据库schema
psql -U postgres -d aisuite -f database_schema.sql

# 初始化数据并创建测试用户
python init_db.py
```

#### 2.2 配置环境变量

在 `backend` 目录创建 `.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://postgres:123456@localhost:5432/aisuite

# JWT 密钥（请修改为安全的随机字符串）
SECRET_KEY=your-super-secret-key-change-in-production

# JWT 算法
ALGORITHM=HS256

# Token 过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI API Key
OPENAI_API_KEY=your-openai-api-key

# Embedding 模型
EMBEDDING_MODEL=text-embedding-ada-002

# 上传文件目录
UPLOAD_DIR=./uploads

# 文本分块配置
CHUNK_SIZE=500
CHUNK_OVERLAP=50

# 限流配置
RATE_LIMIT_ENABLED=True
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_WINDOW=60

# 存储配置（local/s3/minio）
STORAGE_TYPE=local

# CORS 配置
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# 前端URL（用于生成公开对话链接）
FRONTEND_URL=http://localhost:3000
```

#### 2.3 启动后端

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

后端将在 http://localhost:8000 运行

API 文档：http://localhost:8000/docs

#### 2.4 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量 (.env.local)
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_TITLE=AISuite

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:3000 运行

### 3. 对象存储配置（如需使用）

#### S3 配置

```env
STORAGE_TYPE=s3
S3_BUCKET=your-bucket
S3_REGION=us-east-1
S3_ACCESS_KEY=your-access-key
S3_SECRET_KEY=your-secret-key
S3_ENDPOINT=https://s3.amazonaws.com
```

#### MinIO 配置

```env
STORAGE_TYPE=minio
MINIO_BUCKET=your-bucket
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_SECURE=false
```

## 数据库表结构

完整的建表 SQL 请参考 [database_schema.sql](./backend/database_schema.sql)

### 核心表说明

| 表名                           | 说明            |
| ---------------------------- | ------------- |
| users                        | 用户表          |
| roles                        | 角色表          |
| permissions                  | 权限表          |
| menus                        | 菜单表          |
| user_roles                   | 用户角色关联      |
| role_permissions             | 角色权限关联      |
| knowledge_bases              | 知识库表         |
| user_kb_permissions          | 用户知识库权限    |
| knowledge_base_roles         | 知识库角色关联    |
| document_chunks              | 文档分块表（向量） |
| conversations                | 对话会话表        |
| conversations_meta           | 会话元信息表      |
| conversation_message         | 对话消息明细表    |
| conversation_vector_metadata | 向量元数据管理表   |
| llm_models                  | 大模型配置表      |
| embedding_models            | Embedding 模型表 |
| uploaded_files               | 上传文件表        |
| database_connections         | 数据库连接配置表   |
| table_metadata               | 数据库表元数据表   |
| column_metadata              | 数据库字段元数据表  |
| metric_definitions           | 指标口径定义表     |
| audit_logs                   | 审计日志表        |
| public_dialogs               | 公开对话配置表    |
| public_dialog_messages       | 公开对话消息记录表  |

## API 接口文档

启动后端后访问：http://localhost:8000/docs

### 核心接口

| 模块       | 方法   | 路径                              | 说明           |
| -------- | ---- | -------------------------------- | ------------ |
| 认证      | POST | /api/auth/login                  | 用户登录        |
| 认证      | POST | /api/auth/logout                 | 用户登出        |
| 用户管理   | GET  | /api/users/                      | 获取用户列表      |
| 用户管理   | POST | /api/users/                      | 创建用户        |
| 知识库    | GET  | /api/knowledge/                 | 获取知识库列表    |
| 知识库    | POST | /api/knowledge/                 | 创建知识库       |
| 知识库    | GET  | /api/knowledge/{id}             | 获取知识库详情    |
| 知识库    | DELETE | /api/knowledge/{id}            | 删除知识库       |
| 对话      | POST | /api/chat/                       | 发送聊天消息     |
| 对话      | GET  | /api/chat/conversations          | 获取对话列表     |
| 对话      | POST | /api/chat/conversations          | 创建新对话       |
| 大模型    | GET  | /api/llm/models                 | 获取模型列表     |
| 大模型    | POST | /api/llm/models                  | 添加模型配置      |
| Embedding | GET  | /api/embedding/models            | 获取 Embedding 列表 |
| Embedding | POST | /api/embedding/models             | 添加 Embedding 配置 |
| 权限      | GET  | /api/permission/roles            | 获取角色列表      |
| 权限      | POST | /api/permission/roles            | 创建角色        |
| 权限      | GET  | /api/permission/menus            | 获取菜单列表      |
| 审计      | GET  | /api/audit/logs                 | 获取审计日志      |
| 公开对话  | GET  | /api/public-dialog/dialogs      | 获取公开对话列表   |
| 公开对话  | POST | /api/public-dialog/dialogs      | 创建公开对话      |
| 公开对话  | GET  | /api/public-dialog/dialogs/{code} | 通过链接访问对话  |

## 常见问题

### 1. 数据库连接失败

- 检查 PostgreSQL 是否启动
- 确认用户名、密码、数据库名是否正确
- 确保数据库用户有创建表的权限

### 2. 向量化功能报错

- 确认 API Key 正确配置
- 检查网络连接是否正常

### 3. 前端无法访问后端

- 确认后端服务已启动
- 检查 CORS 配置是否正确
- 确认 .env 中的 API 地址配置正确

### 4. pgvector 扩展未安装

```sql
-- 在 PostgreSQL 中执行
CREATE EXTENSION IF NOT EXISTS vector;
```

## 项目预览

![Dashboard](./docs/images/dashboard.png)
![Chat](./docs/images/chat.png)
![Knowledge](./docs/images/knowledge.png)

## 开源协议

MIT License

## 贡献指南

欢迎提交 Issue 和 Pull Request！

---

**AISuite - 企业AI套件，一个平台多种AI能力**

如果本项目对你有帮助，请点亮 Star ⭐
