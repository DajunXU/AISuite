from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime


class EmbeddingModelBase(BaseModel):
    name: str
    provider: str
    model_name: str
    base_url: Optional[str] = None
    dimensions: int = 1024
    max_tokens: int = 8192
    is_active: bool = True
    is_default: bool = False
    is_api: bool = True


class EmbeddingModelCreate(EmbeddingModelBase):
    api_key: Optional[str] = None
    
    @validator('model_name')
    def validate_model_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('模型名称不能为空')
        return v.strip()


class EmbeddingModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    dimensions: Optional[int] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    is_api: Optional[bool] = None


class EmbeddingModelResponse(EmbeddingModelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EmbeddingModelWithKey(EmbeddingModelResponse):
    """包含API密钥的响应（仅管理员可见）"""
    api_key: str


class EmbeddingModelListResponse(BaseModel):
    models: List[EmbeddingModelResponse]
    total: int


class EmbeddingModelTestResponse(BaseModel):
    success: bool
    message: str
    response: Optional[str] = None
