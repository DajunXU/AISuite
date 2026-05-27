from sqlalchemy import Column, Integer, String, Text, DateTime, SmallInteger, BigInteger, Numeric, JSON
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from ..core.database import Base


class ConversationMeta(Base):
    """会话元信息表（聚合统计）"""
    __tablename__ = "conversations_meta"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(String(64), unique=True, nullable=False)
    user_key = Column(String(128), nullable=False)
    module_key = Column(String(64), default="chat")
    source_system = Column(String(64), default="web")
    
    title = Column(String(255))
    session_type = Column(SmallInteger, default=0)
    status = Column(SmallInteger, default=1)
    
    message_count = Column(Integer, default=0)
    total_tokens = Column(BigInteger, default=0)
    first_message_at = Column(TIMESTAMP)
    last_message_time = Column(TIMESTAMP)
    
    model_name = Column(String(64))
    model_provider = Column(String(32))
    model_config = Column(String(2000))
    
    created_time = Column(TIMESTAMP, server_default=func.now())
    updated_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class ConversationMessage(Base):
    """对话消息明细表"""
    __tablename__ = "conversation_message"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    message_id = Column(String(64), unique=True, nullable=False)
    conversation_id = Column(String(64), nullable=False)
    
    user_key = Column(String(128), nullable=False)
    module_key = Column(String(64), default="chat")
    source_system = Column(String(64), default="web")
    
    question_text = Column(Text, nullable=False)
    question_hash = Column(String(64), nullable=False)
    answer_text = Column(Text, nullable=False)
    
    attachments = Column(JSON)
    tool_calls = Column(JSON)
    tool_call_id = Column(String(64))
    messages_json = Column(JSON)
    
    model_name = Column(String(64), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_duration = Column(Integer)
    
    answer_source = Column(SmallInteger, default=0)
    similarity_score = Column(Numeric(4, 3))
    source_message_id = Column(String(64))
    
    is_vectorized = Column(SmallInteger, default=0)
    vectorized_at = Column(TIMESTAMP)
    embedding_model = Column(String(64))
    
    user_feedback = Column(SmallInteger)
    feedback_remark = Column(String(512))
    
    status = Column(SmallInteger, default=1)
    sequence_num = Column(Integer, nullable=False)
    extra_metadata = Column(JSON)
    
    created_time = Column(TIMESTAMP(3), server_default=func.now())
    updated_time = Column(TIMESTAMP(3), server_default=func.now(), onupdate=func.now())


class ConversationVectorMetadata(Base):
    """向量元数据管理表"""
    __tablename__ = "conversation_vector_metadata"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    vector_id = Column(String(128), nullable=False)
    message_id = Column(String(64), nullable=False)
    
    question_hash = Column(String(64), nullable=False)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    module_key = Column(String(64), nullable=False)
    
    embedding_model = Column(String(64), nullable=False)
    vector_dimension = Column(SmallInteger, nullable=False)
    collection_name = Column(String(64), nullable=False)
    
    quality_score = Column(Numeric(3, 2), default=0.50)
    hit_count = Column(Integer, default=0)
    last_hit_time = Column(TIMESTAMP)
    
    status = Column(SmallInteger, default=1)
    expire_time = Column(TIMESTAMP)
    
    created_time = Column(TIMESTAMP, server_default=func.now())
    updated_time = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
