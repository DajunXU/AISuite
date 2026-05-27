from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime


class LLMModelBase(BaseModel):
    name: str
    provider: str
    model_name: str
    base_url: Optional[str] = None
    is_active: bool = True
    is_default: bool = False


class LLMModelCreate(LLMModelBase):
    api_key: str
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('API密钥不能为空')
        return v.strip()


class LLMModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class LLMModelResponse(LLMModelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class LLMModelWithKey(LLMModelResponse):
    """包含API密钥的响应（仅管理员可见）"""
    api_key: str


class LLMModelListResponse(BaseModel):
    models: List[LLMModelResponse]
    total: int


class LLMTestResponse(BaseModel):
    success: bool
    message: str
    response: Optional[str] = None