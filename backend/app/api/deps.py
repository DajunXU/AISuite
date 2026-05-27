from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from ..core.database import get_db
from ..core.config import settings
from ..core.security import verify_token
from ..core.logger import get_logger
from ..models.user import User

logger = get_logger("deps")
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前认证用户"""
    logger.debug(f"[AUTH DEBUG] 收到认证请求")
    logger.debug(f"[AUTH DEBUG] credentials: {credentials}")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    logger.debug(f"[AUTH DEBUG] token: {token[:20]}..." if len(token) > 20 else f"[AUTH DEBUG] token: {token}")
    
    username = verify_token(token)
    logger.debug(f"[AUTH DEBUG] username from token: {username}")
    
    if username is None:
        logger.warning("[AUTH DEBUG] token验证失败")
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    logger.debug(f"[AUTH DEBUG] user: {user}")
    
    if user is None:
        logger.warning("[AUTH DEBUG] 用户不存在")
        raise credentials_exception
    if not user.is_active:
        logger.warning("[AUTH DEBUG] 用户已被禁用")
        raise HTTPException(status_code=400, detail="用户已被禁用")
    
    logger.info(f"[AUTH DEBUG] 认证成功, 用户: {user.username}, 角色: {user.role}")
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """获取管理员用户"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user