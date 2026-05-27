from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from pathlib import Path
from minio import Minio

from ..core.config import settings
import os


class StorageBackend(ABC):
    """存储后端抽象基类"""
    
    @abstractmethod
    async def save(self, file_data: BinaryIO, key: str, content_type: str = None) -> str:
        """保存文件，返回文件URL或路径"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除文件"""
        pass
    
    @abstractmethod
    async def get_url(self, key: str) -> str:
        """获取文件访问URL"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查文件是否存在"""
        pass


class LocalStorageBackend(StorageBackend):
    """本地文件系统存储"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    async def save(self, file_data: BinaryIO, key: str, content_type: str = None) -> str:
        file_path = self.base_dir / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'wb') as f:
            f.write(file_data.read())
        
        return str(file_path)
    
    async def delete(self, key: str) -> bool:
        file_path = self.base_dir / key
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    async def get_url(self, key: str) -> str:
        return f"/uploads/{key}"
    
    async def exists(self, key: str) -> bool:
        return (self.base_dir / key).exists()


class S3StorageBackend(StorageBackend):
    """AWS S3 存储"""
    
    def __init__(self, bucket: str, region: str, access_key: str, secret_key: str, endpoint: str = None):
        import boto3
        self.bucket = bucket
        self.s3 = boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint
        )
    
    async def save(self, file_data: BinaryIO, key: str, content_type: str = None) -> str:
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        self.s3.upload_fileobj(
            file_data,
            self.bucket,
            key,
            ExtraArgs=extra_args
        )
        return f"s3://{self.bucket}/{key}"
    
    async def delete(self, key: str) -> bool:
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False
    
    async def get_url(self, key: str) -> str:
        return self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=3600
        )
    
    async def exists(self, key: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False


class MinIOStorageBackend(StorageBackend):
    """MinIO 存储（兼容 S3 协议）"""
    
    def __init__(self, bucket: str, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        
        self.bucket = bucket
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)
    
    async def save(self, file_data: BinaryIO, key: str, content_type: str = None) -> str:
        file_data.seek(0)
        self.client.put_object(
            self.bucket,
            key,
            file_data,
            length=-1,
            part_size=5*1024*1024,
            content_type=content_type
        )
        return f"minio://{self.bucket}/{key}"
    
    async def delete(self, key: str) -> bool:
        try:
            self.client.remove_object(self.bucket, key)
            return True
        except Exception:
            return False
    
    async def get_url(self, key: str) -> str:
        return self.client.presigned_get_object(self.bucket, key, expires=3600)
    
    async def exists(self, key: str) -> bool:
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except Exception:
            return False


def create_storage_backend() -> StorageBackend:
    """根据配置创建存储后端"""
    
    storage_type = getattr(settings, 'STORAGE_TYPE', 'local')
    
    if storage_type == 's3':
        return S3StorageBackend(
            bucket=settings.S3_BUCKET,
            region=settings.S3_REGION,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            endpoint=getattr(settings, 'S3_ENDPOINT', None)
        )
    elif storage_type == 'minio':
        return MinIOStorageBackend(
            bucket=settings.MINIO_BUCKET,
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=getattr(settings, 'MINIO_SECURE', False)
        )
    else:
        return LocalStorageBackend(
            base_dir=settings.UPLOAD_DIR
        )


storage = create_storage_backend()
