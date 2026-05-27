from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(50), nullable=True)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(Integer, nullable=True)
    method = Column(String(10), nullable=True)
    path = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_body = Column(Text, nullable=True)
    response_status = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_created_at', 'created_at'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, user={self.username}, action={self.action})>"


class AuditAction:
    """审计操作类型常量"""
    # 认证相关
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    
    # 用户相关
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_PASSWORD_CHANGE = "user_password_change"
    
    # 知识库相关
    KB_CREATE = "kb_create"
    KB_UPDATE = "kb_update"
    KB_DELETE = "kb_delete"
    KB_ACCESS = "kb_access"
    
    # 文件相关
    FILE_UPLOAD = "file_upload"
    FILE_DELETE = "file_delete"
    FILE_DOWNLOAD = "file_download"
    
    # 对话相关
    CHAT_CREATE = "chat_create"
    CHAT_MESSAGE = "chat_message"
    
    # LLM 相关
    LLM_CREATE = "llm_create"
    LLM_UPDATE = "llm_update"
    LLM_DELETE = "llm_delete"
    
    # 权限相关
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    
    # 系统相关
    SYSTEM_ERROR = "system_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
