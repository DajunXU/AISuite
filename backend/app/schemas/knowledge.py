from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class KnowledgeBaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False
    kb_type: str = "file"  # file: 文件向量化, db: 数据库连接
    config: Optional[dict] = None  # JSON格式的配置信息
    embedding_model_id: Optional[int] = None  # 向量模型ID


class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    kb_type: Optional[str] = None
    config: Optional[dict] = None
    embedding_model_id: Optional[int] = None


class KnowledgeBaseResponse(KnowledgeBaseBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserPermissionBase(BaseModel):
    user_id: int
    knowledge_base_id: int
    can_read: bool = True
    can_write: bool = False


class UserPermissionCreate(UserPermissionBase):
    pass


class UserPermissionResponse(UserPermissionBase):
    id: int
    granted_at: datetime
    
    class Config:
        from_attributes = True


# 文件上传相关Schemas
class UploadedFileBase(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    status: str = "uploaded"


class UploadedFileCreate(UploadedFileBase):
    knowledge_base_id: int


class UploadedFileResponse(UploadedFileBase):
    id: int
    knowledge_base_id: int
    vectorized_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# 数据库连接相关Schemas
class DatabaseConnectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    db_type: str
    host: str
    port: int
    database: str
    username: str
    password: str
    schema_name: Optional[str] = None
    connection_string: Optional[str] = None
    is_active: bool = True
    pool_size: int = 5
    timeout: int = 30
    max_rows: int = 1000


class TableMetadataBase(BaseModel):
    table_name: str
    table_name_cn: Optional[str] = None
    description: Optional[str] = None
    business_tags: Optional[str] = None
    is_selected: bool = True
    recommended_questions: Optional[str] = None


class ColumnMetadataBase(BaseModel):
    column_name: str
    column_type: Optional[str] = None
    column_comment: Optional[str] = None
    synonyms: Optional[str] = None
    is_selected: bool = True


class MetricDefinitionBase(BaseModel):
    metric_name: str
    metric_definition: str
    description: Optional[str] = None


class DatabaseConnectionCreate(DatabaseConnectionBase):
    knowledge_base_id: int


class DatabaseConnectionResponse(DatabaseConnectionBase):
    id: int
    knowledge_base_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TableMetadataResponse(TableMetadataBase):
    id: int
    connection_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ColumnMetadataResponse(ColumnMetadataBase):
    id: int
    table_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MetricDefinitionResponse(MetricDefinitionBase):
    id: int
    table_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DocumentChunkBase(BaseModel):
    content: str
    metadata: Optional[str] = None
    chunk_index: int


class DocumentChunkResponse(DocumentChunkBase):
    id: int
    knowledge_base_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True