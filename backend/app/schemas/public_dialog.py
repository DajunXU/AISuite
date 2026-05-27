from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class PublicDialogBase(BaseModel):
    name: str = Field(..., description="对话框名称")
    description: Optional[str] = Field(None, description="对话框描述")
    welcome_message: Optional[str] = Field("您好！有什么可以帮助您的？", description="欢迎语")
    recommended_questions: List[str] = Field(default_factory=list, description="推荐问题列表")
    custom_prompt: Optional[str] = Field(None, description="自定义提示词")
    knowledge_base_ids: List[int] = Field(default_factory=list, description="关联的知识库ID列表")
    model_id: Optional[int] = Field(None, description="关联的模型ID")
    language: str = Field("zh", description="语言")
    theme_config: Dict[str, Any] = Field(default_factory=dict, description="主题配置")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    feedback_enabled: bool = Field(False, description="是否启用反馈")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class PublicDialogCreate(PublicDialogBase):
    pass


class PublicDialogUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    welcome_message: Optional[str] = None
    recommended_questions: Optional[List[str]] = None
    custom_prompt: Optional[str] = None
    knowledge_base_ids: Optional[List[int]] = None
    model_id: Optional[int] = None
    language: Optional[str] = None
    theme_config: Optional[Dict[str, Any]] = None
    webhook_url: Optional[str] = None
    feedback_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class PublicDialogResponse(PublicDialogBase):
    id: int
    dialog_code: str
    owner_id: Optional[int]
    model_id: Optional[int]
    is_active: bool
    visit_count: int
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class PublicDialogList(BaseModel):
    dialogs: List[PublicDialogResponse]
    total: int


class PublicDialogMessageCreate(BaseModel):
    question: str = Field(..., description="问题")


class PublicDialogMessageResponse(BaseModel):
    id: int
    question: str
    answer: str
    sources: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PublicDialogChatResponse(BaseModel):
    answer: str
    sources: List[str]
    message_id: int
