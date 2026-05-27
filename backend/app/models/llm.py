from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from ..core.database import Base
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os


class LLMModel(Base):
    """大语言模型配置"""
    __tablename__ = "llm_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # 模型名称
    provider = Column(String(50), nullable=False)  # 提供商：openai, azure, anthropic等
    model_name = Column(String(100), nullable=False)  # 实际模型名称
    api_key_encrypted = Column(Text, nullable=False)  # 加密的API密钥
    base_url = Column(String(500), nullable=True)  # API基础URL（用于自定义端点）
    is_active = Column(Boolean, default=True, nullable=False)  # 是否激活
    is_default = Column(Boolean, default=False, nullable=False)  # 是否默认模型
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    @property
    def fernet(self):
        return LLMKeyManager().fernet
    
    @property
    def encrypted_api_key(self):
        return self.api_key_encrypted
    
    def decrypt_api_key(self, encrypted_key: str = None) -> str:
        """解密API密钥"""
        key = encrypted_key or self.api_key_encrypted
        if not key:
            return ""
        return self.fernet.decrypt(key.encode()).decode()


class LLMKeyManager:
    """API密钥加密管理器"""
    
    def __init__(self, secret_key: str = None):
        # 使用环境变量或默认密钥
        self.secret_key = secret_key or os.getenv('LLM_SECRET_KEY', 'default-secret-key-change-in-production')
        self.fernet = self._create_fernet(self.secret_key)
    
    def _create_fernet(self, secret_key: str) -> Fernet:
        """创建Fernet加密器"""
        # 使用PBKDF2从密码生成密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'knowledge_base_salt',  # 固定salt，生产环境应该使用随机salt
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        return Fernet(key)
    
    def encrypt_api_key(self, api_key: str) -> str:
        """加密API密钥"""
        return self.fernet.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """解密API密钥"""
        return self.fernet.decrypt(encrypted_key.encode()).decode()
    
    @staticmethod
    def create_default_models(db):
        """创建默认的大模型配置"""
        from .llm import LLMModel
        
        # 检查是否已存在默认模型
        existing = db.query(LLMModel).filter(LLMModel.is_default == True).first()
        if existing:
            return
        
        key_manager = LLMKeyManager()
        
        default_model = LLMModel(
            name="GPT-3.5 Turbo",
            provider="openai",
            model_name="gpt-3.5-turbo",
            api_key_encrypted=key_manager.encrypt_api_key("sk-please-replace-with-your-api-key"),
            is_default=True
        )
        
        db.add(default_model)
        db.commit()