from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ConversationBase(BaseModel):
    title: str = Field("新对话", description="对话标题")


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None


class ConversationInDB(BaseModel):
    id: Optional[int] = None
    user_id: Optional[int] = None
    title: str
    is_favorite: bool = False
    is_archived: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    message_id: str = Field(..., description="消息ID")
    feedback: int = Field(..., ge=0, le=1, description="反馈: 0踩 1赞")
    remark: Optional[str] = None


class Conversation(ConversationInDB):
    pass


class ConversationList(BaseModel):
    conversations: List[Conversation] = Field(default_factory=list, description="对话列表")


class ChatMessageBase(BaseModel):
    question: str
    text_kb_id: Optional[int] = None
    db_kb_id: Optional[int] = None
    model_id: Optional[int] = None


class ChatMessageCreate(ChatMessageBase):
    conversation_id: Optional[int] = None


class ChatMessageResponse(BaseModel):
    id: int
    message_id: str
    conversation_id: Optional[str]
    user_key: Optional[str]
    question_text: str
    answer_text: str
    model_name: Optional[str] = None
    total_duration: Optional[int] = None
    answer_source: Optional[int] = None
    user_feedback: Optional[int] = None
    created_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChatStreamResponse(BaseModel):
    content: str
    is_final: bool = False
    sources: Optional[List[str]] = None