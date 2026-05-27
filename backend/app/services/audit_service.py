from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.audit import AuditLog, AuditAction
from ..core.logger import get_logger

logger = get_logger("audit")


class AuditService:
    """审计日志服务"""
    
    def __init__(self, db: Session = None):
        self.db = db
    
    def log(
        self,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_body: Optional[str] = None,
        response_status: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """记录审计日志"""
        try:
            audit = AuditLog(
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                method=method,
                path=path,
                ip_address=ip_address,
                user_agent=user_agent,
                request_body=request_body,
                response_status=response_status,
                error_message=error_message
            )
            self.db.add(audit)
            self.db.commit()
            logger.debug(f"审计日志记录成功: {action} - {username}")
        except Exception as e:
            logger.error(f"审计日志记录失败: {e}")
            self.db.rollback()
    
    def log_login(self, user_id: int, username: str, ip_address: str = None, success: bool = True):
        """记录登录操作"""
        action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
        self.log(
            action=action,
            user_id=user_id if success else None,
            username=username if success else username,
            ip_address=ip_address,
            response_status=200 if success else 401
        )
    
    def log_logout(self, user_id: int, username: str, ip_address: str = None):
        """记录登出操作"""
        self.log(
            action=AuditAction.LOGOUT,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            response_status=200
        )
    
    def log_kb_access(self, user_id: int, username: str, kb_id: int, action_type: str, ip_address: str = None):
        """记录知识库访问操作"""
        action_map = {
            "create": AuditAction.KB_CREATE,
            "update": AuditAction.KB_UPDATE,
            "delete": AuditAction.KB_DELETE,
            "access": AuditAction.KB_ACCESS
        }
        self.log(
            action=action_map.get(action_type, AuditAction.KB_ACCESS),
            user_id=user_id,
            username=username,
            resource_type="knowledge_base",
            resource_id=kb_id,
            ip_address=ip_address,
            response_status=200
        )
    
    def log_file_operation(
        self, 
        user_id: int, 
        username: str, 
        file_id: int, 
        operation: str,
        ip_address: str = None,
        success: bool = True
    ):
        """记录文件操作"""
        action = AuditAction.FILE_UPLOAD if operation == "upload" else AuditAction.FILE_DELETE
        self.log(
            action=action,
            user_id=user_id,
            username=username,
            resource_type="file",
            resource_id=file_id,
            ip_address=ip_address,
            response_status=200 if success else 500
        )
    
    def log_chat(
        self, 
        user_id: int, 
        username: str, 
        conversation_id: int = None,
        message: str = None,
        ip_address: str = None
    ):
        """记录对话操作"""
        self.log(
            action=AuditAction.CHAT_MESSAGE,
            user_id=user_id,
            username=username,
            resource_type="conversation",
            resource_id=conversation_id,
            request_body=message[:500] if message else None,
            ip_address=ip_address,
            response_status=200
        )
    
    def log_error(
        self,
        error_action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        error_message: str = None,
        path: str = None,
        method: str = None
    ):
        """记录错误操作"""
        self.log(
            action=AuditAction.SYSTEM_ERROR,
            user_id=user_id,
            username=username,
            path=path,
            method=method,
            error_message=error_message,
            response_status=500
        )


audit_service = AuditService()
