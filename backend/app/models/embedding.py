from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from ..core.database import Base
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os


class EmbeddingModel(Base):
    """向量模型配置"""
    __tablename__ = "embedding_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # 模型名称，如 "bge-small-zh-v1.5"
    provider = Column(String(50), nullable=False)  # 提供商：openai, zhipu, qwen, local 等
    model_name = Column(String(100), nullable=False)  # 实际模型名称，如 "text-embedding-v4"
    api_key_encrypted = Column(Text, nullable=True)  # 加密的API密钥（API调用时需要）
    base_url = Column(String(500), nullable=True)  # API基础URL（用于自定义端点或自部署API）
    dimensions = Column(Integer, default=1024)  # 向量维度，如 1024, 1536, 2560
    max_tokens = Column(Integer, default=8192)  # 最大输入 token 数
    is_active = Column(Boolean, default=True, nullable=False)  # 是否激活
    is_default = Column(Boolean, default=False, nullable=False)  # 是否默认模型
    is_api = Column(Boolean, default=True, nullable=False)  # 是否为API调用，False表示自部署
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    @property
    def fernet(self):
        return EmbeddingKeyManager().fernet
    
    @property
    def encrypted_api_key(self):
        return self.api_key_encrypted
    
    def decrypt_api_key(self, encrypted_key: str = None) -> str:
        """解密API密钥"""
        key = encrypted_key or self.api_key_encrypted
        if not key:
            return ""
        return self.fernet.decrypt(key.encode()).decode()


class EmbeddingKeyManager:
    """API密钥加密管理器"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.getenv('LLM_SECRET_KEY', 'default-secret-key-change-in-production')
        self.fernet = self._create_fernet(self.secret_key)
    
    def _create_fernet(self, secret_key: str) -> Fernet:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'embedding_model_salt',
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        return Fernet(key)
    
    def encrypt_api_key(self, api_key: str) -> str:
        """加密API密钥"""
        if not api_key:
            return ""
        return self.fernet.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """解密API密钥"""
        if not encrypted_key:
            return ""
        return self.fernet.decrypt(encrypted_key.encode()).decode()
