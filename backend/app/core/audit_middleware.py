from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import get_logger
from .security import verify_token
from .database import SessionLocal
from .config import settings
from ..models.audit import AuditLog
from ..models.user import User

logger = get_logger("audit_middleware")

logger.info("[AUDIT] 审计中间件已加载")


def _get_user_from_token(request: Request):
    """从请求头获取JWT token并解析出用户信息"""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, None
    
    token = auth_header.replace("Bearer ", "")
    username = verify_token(token)
    if not username:
        return None, None
    
    try:
        db = SessionLocal()
        user = db.query(User).filter(User.username == username).first()
        db.close()
        if user:
            return user.id, user.username
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
    
    return None, None


class AuditMiddleware(BaseHTTPMiddleware):
    """审计日志中间件 - 自动记录 API 请求"""
    
    SKIP_PATHS = ["/", "/health", "/docs", "/openapi.json", "/redoc"]
    SKIP_PREFIXES = ["/docs", "/openapi", "/redoc"]
    
    def _should_skip(self, path: str) -> bool:
        if path in self.SKIP_PATHS:
            return True
        for prefix in self.SKIP_PREFIXES:
            if path.startswith(prefix):
                return True
        return False
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        
        if not settings.AUDIT_ENABLED:
            return await call_next(request)
        
        logger.info(f"[AUDIT] 收到请求: {request.method} {request.url.path}")
        
        if self._should_skip(request.url.path):
            logger.info(f"[AUDIT] 跳过: {request.url.path}")
            return await call_next(request)
        
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)
        
        if not user_id or not username:
            user_id, username = _get_user_from_token(request)
        
        logger.info(f"审计: {method} {path} - user: {username or 'anonymous'}")
        
        response = await call_next(request)
        status_code = response.status_code
        
        action = self._get_action(method, path)
        
        try:
            db = SessionLocal()
            try:
                audit = AuditLog(
                    user_id=user_id,
                    username=username,
                    action=action,
                    method=method,
                    path=path,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    response_status=status_code
                )
                db.add(audit)
                db.commit()
                logger.info(f"审计日志已记录: {action} - {path}")
            except Exception as e:
                logger.error(f"审计日志记录失败: {e}")
                db.rollback()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"审计中间件错误: {e}")
        
        return response
    
    def _get_action(self, method: str, path: str) -> str:
        action_map = {
            ("GET", "/api/knowledge"): "kb_list",
            ("POST", "/api/knowledge"): "kb_create",
            ("PUT", "/api/knowledge"): "kb_update",
            ("DELETE", "/api/knowledge"): "kb_delete",
            ("POST", "/api/chat"): "chat",
            ("GET", "/api/users"): "user_list",
            ("POST", "/api/users"): "user_create",
            ("PUT", "/api/users"): "user_update",
            ("DELETE", "/api/users"): "user_delete",
            ("GET", "/api/llm"): "llm_list",
            ("POST", "/api/llm"): "llm_create",
            ("PUT", "/api/llm"): "llm_update",
            ("DELETE", "/api/llm"): "llm_delete",
            ("GET", "/api/audit"): "audit_view",
        }
        return action_map.get((method, path), f"{method.lower()}_{path.replace('/', '_')}")
