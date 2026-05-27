from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
from .embedding import EmbeddingModel

# 导入pgvector支持
try:
    from pgvector.sqlalchemy import Vector
    PG_VECTOR_AVAILABLE = True
except ImportError:
    PG_VECTOR_AVAILABLE = False
    # 如果没有pgvector，使用Text类型作为备选
    Vector = Text


class KnowledgeBaseRole(Base):
    """知识库角色关联 - 控制哪些角色可以访问哪些知识库"""
    __tablename__ = "knowledge_base_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False, comment="知识库ID")
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, comment="角色ID")
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<KnowledgeBaseRole(kb_id={self.knowledge_base_id}, role_id={self.role_id})>"


class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    
    # 向量模型关联（新增）
    embedding_model_id = Column(Integer, ForeignKey("embedding_models.id"), nullable=True, comment="向量模型ID")
    
    # 新增字段：知识库类型和配置
    kb_type = Column(String(20), default="file", nullable=False)  # file: 文件向量化, db: 数据库连接
    config = Column(Text, nullable=True)  # JSON格式的配置信息
    
    created_at = Column(DateTime, server_default=func.now())  # 移除timezone
    updated_at = Column(DateTime, onupdate=func.now())  # 移除timezone
    
    # 关系（简化关系定义）
    owner = relationship("User")
    embedding_model = relationship("EmbeddingModel")
    user_permissions = relationship("UserKnowledgePermission", back_populates="knowledge_base")
    document_chunks = relationship("DocumentChunk", back_populates="knowledge_base")
    uploaded_files = relationship("UploadedFile", back_populates="knowledge_base")
    db_connections = relationship("DatabaseConnection", back_populates="knowledge_base")


class UserKnowledgePermission(Base):
    __tablename__ = "user_kb_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    can_read = Column(Boolean, default=True, nullable=False)
    can_write = Column(Boolean, default=False, nullable=False)
    granted_at = Column(DateTime, server_default=func.now())  # 移除timezone
    
    # 关系（简化关系定义）
    user = relationship("User")
    knowledge_base = relationship("KnowledgeBase")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))  # pgvector向量类型
    chunk_metadata = Column(Text)  # JSON格式的元数据（避免与SQLAlchemy metadata冲突）
    chunk_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())  # 移除timezone
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="document_chunks")


class UploadedFile(Base):
    """上传文件模型"""
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(100), nullable=False)
    status = Column(String(20), default="uploaded", nullable=False)  # uploaded, processing, processed, error
    vectorized_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="uploaded_files")


class DatabaseConnection(Base):
    """数据库连接配置模型"""
    __tablename__ = "database_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"), nullable=False)
    name = Column(String(100), nullable=False)  # 数据源名称
    description = Column(Text, nullable=True)  # 数据源描述
    db_type = Column(String(20), nullable=False)  # mysql, postgresql, sqlserver, etc.
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    database = Column(String(100), nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(500), nullable=False)  # 加密存储
    schema_name = Column(String(100), nullable=True)
    connection_string = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 连接池配置
    pool_size = Column(Integer, default=5)
    timeout = Column(Integer, default=30)
    max_rows = Column(Integer, default=1000)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="db_connections")
    tables = relationship("TableMetadata", back_populates="connection", cascade="all, delete-orphan")


class TableMetadata(Base):
    """数据库表元数据"""
    __tablename__ = "table_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("database_connections.id"), nullable=False)
    table_name = Column(String(100), nullable=False)
    table_name_cn = Column(String(100), nullable=True)  # 表中文名
    description = Column(Text, nullable=True)  # 表描述
    business_tags = Column(Text, nullable=True)  # 业务标签，逗号分隔
    is_selected = Column(Boolean, default=True)  # 是否被选中接入
    recommended_questions = Column(Text, nullable=True)  # 推荐问题，JSON数组
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    connection = relationship("DatabaseConnection", back_populates="tables")
    columns = relationship("ColumnMetadata", back_populates="table", cascade="all, delete-orphan")
    metrics = relationship("MetricDefinition", back_populates="table", cascade="all, delete-orphan")


class ColumnMetadata(Base):
    """数据库字段元数据"""
    __tablename__ = "column_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("table_metadata.id"), nullable=False)
    column_name = Column(String(100), nullable=False)
    column_type = Column(String(50), nullable=True)
    column_comment = Column(String(500), nullable=True)  # 字段注释
    synonyms = Column(String(500), nullable=True)  # 同义词，逗号分隔
    is_selected = Column(Boolean, default=True)  # 是否被选中
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    table = relationship("TableMetadata", back_populates="columns")


class MetricDefinition(Base):
    """指标口径定义"""
    __tablename__ = "metric_definitions"
    
    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("table_metadata.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)  # 指标名称
    metric_definition = Column(Text, nullable=False)  # 口径定义（SQL片段）
    description = Column(Text, nullable=True)  # 指标描述
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关系
    table = relationship("TableMetadata", back_populates="metrics")