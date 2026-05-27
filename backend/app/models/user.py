from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default="user", nullable=False)  # 保留作为兼容字段
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())  # 移除timezone
    updated_at = Column(DateTime, onupdate=func.now())  # 移除timezone
    
    # 关系
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    # owned_knowledge_bases = relationship("KnowledgeBase", back_populates="owner")
    # knowledge_permissions = relationship("UserKnowledgePermission", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"
