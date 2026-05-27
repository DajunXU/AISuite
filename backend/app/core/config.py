from pydantic_settings import BaseSettings
from typing import List
import os
import platform


class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "postgresql://postgres:123456@localhost:5432/test"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI配置
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    OPENAI_API_KEY: str = "your-openai-api-key"
    
    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    
    # 系统配置
    SYSTEM_PLATFORM: str = platform.system()
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: int = 100
    RATE_LIMIT_WINDOW: int = 60
    
    # 审计配置
    AUDIT_ENABLED: bool = False  # 是否启用审计日志功能
    
    # ==================== 存储配置 ====================
    # 文件存储类型: local(本地存储) / s3(AWS S3) / minio(MinIO对象存储)
    STORAGE_TYPE: str = "local"
    
    # --- S3 配置 (当 STORAGE_TYPE="s3" 时使用) ---
    # S3 存储桶名称
    S3_BUCKET: str = ""
    # S3 区域(如: us-east-1, cn-north-1)
    S3_REGION: str = "us-east-1"
    # S3 Access Key
    S3_ACCESS_KEY: str = ""
    # S3 Secret Key
    S3_SECRET_KEY: str = ""
    # S3 兼容服务的自定义端点(可选,AWS S3不需要设置)
    S3_ENDPOINT: str = ""
    
    # --- MinIO 配置 (当 STORAGE_TYPE="minio" 时使用) ---
    # MinIO 存储桶名称
    MINIO_BUCKET: str = ""
    # MinIO 服务地址(如: localhost:9000)
    MINIO_ENDPOINT: str = ""
    # MinIO Access Key
    MINIO_ACCESS_KEY: str = ""
    # MinIO Secret Key
    MINIO_SECRET_KEY: str = ""
    # MinIO 是否使用HTTPS
    MINIO_SECURE: bool = False
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]
    
    # 前端URL配置(用于生成公开对话链接)
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"


settings = Settings()