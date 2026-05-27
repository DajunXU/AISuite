-- ============================================================
-- AI 知识库智能对话系统 - 完整数据库脚本
-- ============================================================
-- 创建数据库: CREATE DATABASE knowledge_base;
-- 执行方式: psql -U postgres -d knowledge_base -f database_schema.sql
-- ============================================================

-- ============================================================
-- 用户与角色表
-- ============================================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    full_name VARCHAR(100),
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 权限表
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 菜单表
CREATE TABLE IF NOT EXISTS menus (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    path VARCHAR(100),
    icon VARCHAR(50),
    parent_id INTEGER,
    sort_order INTEGER DEFAULT 0,
    is_visible BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE(user_id, role_id)
);

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE(role_id, permission_id)
);

-- 角色菜单关联表
-- 注意：该表已在代码中弃用，仅保留结构以兼容旧数据
-- CREATE TABLE IF NOT EXISTS role_menus (
--     id SERIAL PRIMARY KEY,
--     role_id INTEGER NOT NULL,
--     menu_id INTEGER NOT NULL,
--     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
--     FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE,
--     UNIQUE(role_id, menu_id)
-- );

-- ============================================================
-- 知识库表
-- ============================================================

-- 知识库表
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    kb_type VARCHAR(20) DEFAULT 'file',
    is_public BOOLEAN DEFAULT FALSE,
    config JSONB,
    embedding_model_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (embedding_model_id) REFERENCES embedding_models(id) ON DELETE SET NULL
);

-- 用户知识库权限表
CREATE TABLE IF NOT EXISTS user_kb_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    knowledge_base_id INTEGER NOT NULL,
    can_read BOOLEAN DEFAULT TRUE,
    can_write BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    UNIQUE(user_id, knowledge_base_id)
);

-- 知识库角色关联表（用于知识库数据隔离）
CREATE TABLE IF NOT EXISTS knowledge_base_roles (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE(knowledge_base_id, role_id)
);

-- 上传文件表
CREATE TABLE IF NOT EXISTS uploaded_files (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    file_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
);

-- 文档分块表（用于向量存储）
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    chunk_metadata TEXT,
    chunk_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
);

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    username VARCHAR(100),
    action VARCHAR(50),
    method VARCHAR(10),
    path VARCHAR(500),
    request_body TEXT,
    response_status INTEGER,
    ip_address VARCHAR(50),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据库连接配置表
CREATE TABLE IF NOT EXISTS database_connections (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER NOT NULL,
    connection_name VARCHAR(100),
    db_type VARCHAR(20) DEFAULT 'postgresql',
    host VARCHAR(100),
    port INTEGER,
    database_name VARCHAR(100),
    username VARCHAR(100),
    password VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE
);

-- 数据库表元数据表
CREATE TABLE IF NOT EXISTS table_metadata (
    id SERIAL PRIMARY KEY,
    connection_id INTEGER NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    table_comment TEXT,
    columns JSONB,
    is_selected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (connection_id) REFERENCES database_connections(id) ON DELETE CASCADE
);

-- 数据库字段元数据表
CREATE TABLE IF NOT EXISTS column_metadata (
    id SERIAL PRIMARY KEY,
    table_id INTEGER NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    column_type VARCHAR(50),
    column_comment VARCHAR(500),
    synonyms VARCHAR(500),
    is_selected BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (table_id) REFERENCES table_metadata(id) ON DELETE CASCADE
);

-- 指标口径定义表
CREATE TABLE IF NOT EXISTS metric_definitions (
    id SERIAL PRIMARY KEY,
    table_id INTEGER NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_definition TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (table_id) REFERENCES table_metadata(id) ON DELETE CASCADE
);

-- ============================================================
-- 对话相关表
-- ============================================================

-- 会话元信息表（聚合统计）
CREATE TABLE IF NOT EXISTS conversations_meta (
    id BIGSERIAL PRIMARY KEY,
    conversation_id VARCHAR(64) UNIQUE NOT NULL,
    user_key VARCHAR(128) NOT NULL,
    module_key VARCHAR(64) DEFAULT 'chat',
    source_system VARCHAR(64) DEFAULT 'web',
    title VARCHAR(255),
    session_type SMALLINT DEFAULT 0,
    status SMALLINT DEFAULT 1,
    message_count INTEGER DEFAULT 0,
    total_tokens BIGINT DEFAULT 0,
    first_message_at TIMESTAMP,
    last_message_time TIMESTAMP,
    model_name VARCHAR(64),
    model_provider VARCHAR(32),
    model_config VARCHAR(2000),
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 对话消息明细表
CREATE TABLE IF NOT EXISTS conversation_message (
    id BIGSERIAL PRIMARY KEY,
    message_id VARCHAR(64) UNIQUE NOT NULL,
    conversation_id VARCHAR(64) NOT NULL,
    user_key VARCHAR(128) NOT NULL,
    module_key VARCHAR(64) DEFAULT 'chat',
    source_system VARCHAR(64) DEFAULT 'web',
    question_text TEXT NOT NULL,
    question_hash VARCHAR(64) NOT NULL,
    answer_text TEXT NOT NULL,
    attachments JSON,
    tool_calls JSON,
    tool_call_id VARCHAR(64),
    messages_json JSON,
    model_name VARCHAR(64) NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_duration INTEGER,
    answer_source SMALLINT DEFAULT 0,
    similarity_score NUMERIC(4, 3),
    source_message_id VARCHAR(64),
    is_vectorized SMALLINT DEFAULT 0,
    vectorized_at TIMESTAMP,
    embedding_model VARCHAR(64),
    user_feedback SMALLINT,
    feedback_remark VARCHAR(512),
    status SMALLINT DEFAULT 1,
    sequence_num INTEGER NOT NULL,
    extra_metadata JSON,
    created_time TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP
);

-- 对话会话表
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL DEFAULT '新对话',
    is_favorite BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 向量元数据管理表
CREATE TABLE IF NOT EXISTS conversation_vector_metadata (
    id BIGSERIAL PRIMARY KEY,
    vector_id VARCHAR(128) NOT NULL,
    message_id VARCHAR(64) NOT NULL,
    question_hash VARCHAR(64) NOT NULL,
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    module_key VARCHAR(64) NOT NULL,
    embedding_model VARCHAR(64) NOT NULL,
    vector_dimension SMALLINT NOT NULL,
    collection_name VARCHAR(64) NOT NULL,
    quality_score NUMERIC(3, 2) DEFAULT 0.50,
    hit_count INTEGER DEFAULT 0,
    last_hit_time TIMESTAMP,
    status SMALLINT DEFAULT 1,
    expire_time TIMESTAMP,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 大模型配置表
-- ============================================================

CREATE TABLE IF NOT EXISTS embedding_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    api_key_encrypted TEXT,
    base_url VARCHAR(500),
    dimensions INTEGER DEFAULT 1024,
    max_tokens INTEGER DEFAULT 8192,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    is_api BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- ============================================================
-- 大模型配置表
-- ============================================================

CREATE TABLE IF NOT EXISTS llm_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    api_base VARCHAR(255),
    api_key VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- ============================================================
-- 公开对话相关表
-- ============================================================

-- 公开对话配置表
CREATE TABLE IF NOT EXISTS public_dialogs (
    id SERIAL PRIMARY KEY,
    dialog_code VARCHAR(32) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    welcome_message TEXT DEFAULT '您好！有什么可以帮助您的？',
    owner_id INTEGER,
    recommended_questions JSONB DEFAULT '[]',
    custom_prompt TEXT,
    knowledge_base_ids JSONB DEFAULT '[]',
    model_id INTEGER,
    language VARCHAR(10) DEFAULT 'zh',
    theme_config JSONB DEFAULT '{}',
    webhook_url VARCHAR(500),
    feedback_enabled BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    visit_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (model_id) REFERENCES llm_models(id) ON DELETE SET NULL
);

-- 公开对话消息记录表
CREATE TABLE IF NOT EXISTS public_dialog_messages (
    id SERIAL PRIMARY KEY,
    dialog_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dialog_id) REFERENCES public_dialogs(id) ON DELETE CASCADE
);

-- ============================================================
-- 索引创建
-- ============================================================

-- 用户索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 角色索引
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);

-- 菜单索引
CREATE INDEX IF NOT EXISTS idx_menus_parent_id ON menus(parent_id);

-- 用户角色关联索引
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_role_id ON user_roles(role_id);

-- 知识库索引
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_owner ON knowledge_bases(owner_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_kb_type ON knowledge_bases(kb_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_bases_embedding_model ON knowledge_bases(embedding_model_id);

-- 文档分块索引
CREATE INDEX IF NOT EXISTS idx_document_chunks_kb_id ON document_chunks(knowledge_base_id);

-- 审计日志索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- 对话会话索引
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated ON conversations(updated_at);

-- ============================================================
-- 初始化数据
-- ============================================================

-- 插入默认用户 (密码: test123)
INSERT INTO users (username, email, full_name, hashed_password, role) VALUES 
('test', 'test@example.com', '测试用户', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ePLF6.STUN0u', 'user')
ON CONFLICT (username) DO NOTHING;

-- 插入管理员用户 (密码: admin123)
INSERT INTO users (username, email, full_name, hashed_password, role) VALUES 
('admin', 'admin@example.com', '管理员', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'admin')
ON CONFLICT (username) DO NOTHING;

-- 插入角色
INSERT INTO roles (name, description) VALUES 
('admin', '管理员'),
('user', '普通用户'),
('guest', '访客')
ON CONFLICT (name) DO NOTHING;

-- 插入权限
INSERT INTO permissions (name, code, description) VALUES 
('查看仪表盘', 'dashboard:view', '查看仪表盘'),
('知识库管理', 'knowledge:manage', '管理知识库'),
('知识库查看', 'knowledge:view', '查看知识库'),
('智能对话', 'chat:use', '使用智能对话'),
('大模型管理', 'llm:manage', '管理大模型'),
('用户管理', 'user:manage', '管理用户'),
('权限管理', 'permission:manage', '管理权限')
ON CONFLICT (code) DO NOTHING;

-- 插入菜单
INSERT INTO menus (name, path, icon, parent_id, sort_order) VALUES 
('仪表盘', '/dashboard', 'HomeFilled', NULL, 1),
('知识库', '/knowledge', 'FolderOpened', NULL, 2),
('知识库管理', '/knowledge/manager', 'Document', 2, 1),
('知识库权限配置', '/knowledge/authority', 'Lock', 2, 2),
('智能问答', '/chat', 'ChatDotRound', NULL, 3),
('大模型管理', '/llm', 'Cpu', NULL, 4),
('权限管理', '/admin', 'Setting', NULL, 5),
('用户管理', '/admin/users', 'User', 5, 1),
('角色管理', '/admin/roles', 'UserFilled', 5, 2)
ON CONFLICT DO NOTHING;

-- 插入向量模型配置
INSERT INTO embedding_models (name, provider, model_name, base_url, dimensions, is_active, is_default, is_api) VALUES 
('text-embedding-v4', 'qwen', 'text-embedding-v4', 'https://dashscope.aliyuncs.com/compatible-mode/v1', 1024, TRUE, TRUE, TRUE),
('text-embedding-3-small', 'qwen', 'text-embedding-3-small', 'https://dashscope.aliyuncs.com/compatible-mode/v1', 1536, TRUE, FALSE, TRUE),
('embedding-2', 'zhipu', 'embedding-2', 'https://open.bigmodel.cn/api/paas/v4/', 1024, TRUE, FALSE, TRUE),
('text-embedding-ada-002', 'openai', 'text-embedding-ada-002', 'https://api.openai.com/v1', 1536, TRUE, FALSE, TRUE)
ON CONFLICT DO NOTHING;

-- 插入大模型配置
INSERT INTO llm_models (name, provider, model_type, api_base, api_key, is_active, is_default, config) VALUES 
('GPT-4', 'openai', 'gpt-4', 'https://api.openai.com/v1', '', TRUE, FALSE, '{"temperature": 0.7, "max_tokens": 2000}'),
('GPT-3.5 Turbo', 'openai', 'gpt-3.5-turbo', 'https://api.openai.com/v1', '', TRUE, TRUE, '{"temperature": 0.7, "max_tokens": 2000}')
ON CONFLICT DO NOTHING;

-- 插入知识库数据（示例）
INSERT INTO knowledge_bases (owner_id, name, description, kb_type) VALUES 
(1, '胜多负少', '测试知识库', 'file'),
(1, '数据库', '数据库知识库', 'db'),
(1, 'ceshi', '测试用', 'db')
ON CONFLICT DO NOTHING;

-- 更新序列（确保自增主键正确）
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('roles_id_seq', (SELECT MAX(id) FROM roles));
SELECT setval('permissions_id_seq', (SELECT MAX(id) FROM permissions));
SELECT setval('menus_id_seq', (SELECT MAX(id) FROM menus));
SELECT setval('knowledge_bases_id_seq', (SELECT MAX(id) FROM knowledge_bases));
SELECT setval('llm_models_id_seq', (SELECT MAX(id) FROM llm_models));
SELECT setval('embedding_models_id_seq', (SELECT MAX(id) FROM embedding_models));
SELECT setval('conversations_id_seq', (SELECT MAX(id) FROM conversations));
SELECT setval('database_connections_id_seq', (SELECT MAX(id) FROM database_connections));
SELECT setval('table_metadata_id_seq', (SELECT MAX(id) FROM table_metadata));
SELECT setval('public_dialogs_id_seq', (SELECT MAX(id) FROM public_dialogs));

-- 输出完成信息
DO $$
BEGIN
    RAISE NOTICE '数据库初始化完成！';
    RAISE NOTICE '默认账号: test / test123';
    RAISE NOTICE '管理员账号: admin / admin123';
END $$;
