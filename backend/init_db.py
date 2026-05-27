#!/usr/bin/env python3
"""初始化数据库和创建测试用户"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash

# 创建数据库引擎
if "sqlite" in settings.DATABASE_URL:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300
    )

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """初始化数据库"""
    try:
        # 导入模型
        from app.models.user import User
        from app.models.knowledge import KnowledgeBase, UserKnowledgePermission, DocumentChunk
        from app.models.chat import Conversation
        from app.models.cache import ConversationMeta, ConversationMessage, ConversationVectorMetadata
        from app.models.embedding import EmbeddingModel
        from app.models.audit import AuditLog
        from app.models.permission import Role, Menu, Permission, UserRole, RolePermission
        from app.models.public_dialog import PublicDialog, PublicDialogMessage
        
        # 创建所有表
        from app.core.database import Base
        Base.metadata.create_all(bind=engine)
        print("数据库表创建成功！")
        
        # 创建会话
        db = SessionLocal()
        
        # 检查是否已有测试用户
        test_user = db.query(User).filter(User.username == "test").first()
        if not test_user:
            # 创建测试用户
            test_user = User(
                username="test",
                email="test@example.com",
                full_name="测试用户",
                hashed_password=get_password_hash("test123")
            )
            db.add(test_user)
            db.commit()
            print("测试用户创建成功！")
            print(f"用户名: test")
            print(f"密码: test123")
        else:
            print("测试用户已存在")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    init_database()