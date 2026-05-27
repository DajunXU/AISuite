from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
import hashlib
from .config import settings

# 简单的密码哈希函数（用于开发环境）
def simple_hash_password(password: str) -> str:
    """简单的密码哈希函数"""
    return hashlib.sha256(password.encode()).hexdigest()

def simple_verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return simple_hash_password(plain_password) == hashed_password


def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """创建JWT访问令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return simple_verify_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return simple_hash_password(password)


def verify_token(token: str) -> Union[str, None]:
    """验证JWT令牌"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except jwt.JWTError:
        return None