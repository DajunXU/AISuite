from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class PublicDialog(Base):
    """公开对话配置表"""
    __tablename__ = "public_dialogs"

    id = Column(Integer, primary_key=True, index=True)
    dialog_code = Column(String(32), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    welcome_message = Column(Text, default="您好！有什么可以帮助您的？")
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    recommended_questions = Column(JSONB, default=list)
    custom_prompt = Column(Text)
    
    knowledge_base_ids = Column(JSONB, default=list)
    model_id = Column(Integer, ForeignKey("llm_models.id"), nullable=True)
    
    language = Column(String(10), default="zh")
    theme_config = Column(JSONB, default={})
    webhook_url = Column(String(500), nullable=True)
    feedback_enabled = Column(Boolean, default=False)
    
    is_active = Column(Boolean, default=True)
    visit_count = Column(Integer, default=0)
    
    expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    owner = relationship("User")
    model = relationship("LLMModel")
    messages = relationship("PublicDialogMessage", back_populates="dialog", cascade="all, delete-orphan")


class PublicDialogMessage(Base):
    """公开对话消息记录"""
    __tablename__ = "public_dialog_messages"

    id = Column(Integer, primary_key=True, index=True)
    dialog_id = Column(Integer, ForeignKey("public_dialogs.id"), nullable=False)
    
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())

    dialog = relationship("PublicDialog", back_populates="messages")
