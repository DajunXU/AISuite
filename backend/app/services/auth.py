from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..core.config import settings
from ..core.security import create_access_token, verify_password, get_password_hash
from ..models.user import User


class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, username: str, password: str) -> User:
        """验证用户凭据"""
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
    
    def create_user(self, username: str, email: str, password: str, full_name: str = None) -> User:
        """创建新用户"""
        # 检查用户名是否已存在
        existing_user = self.db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError("用户名已存在")
        
        # 检查邮箱是否已存在
        existing_email = self.db.query(User).filter(User.email == email).first()
        if existing_email:
            raise ValueError("邮箱已存在")
        
        # 创建用户
        hashed_password = get_password_hash(password)
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def create_access_token(self, user: User) -> str:
        """为用户创建访问令牌"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return create_access_token(
            subject=user.username, expires_delta=access_token_expires
        )