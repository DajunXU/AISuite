from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
from .logger import get_logger

logger = get_logger("database")

# 创建数据库引擎（支持SQLite和PostgreSQL）
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

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 启用pgvector扩展（如果使用PostgreSQL）
def enable_pgvector():
    """启用pgvector扩展"""
    if settings.DATABASE_URL.startswith("postgresql"):
        try:
            with engine.connect() as conn:
                # 启用pgvector扩展
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("pgvector扩展已启用")
        except Exception as e:
            logger.error(f"启用pgvector扩展失败: {e}")

try:
    enable_pgvector()
except Exception as e:
    logger.error(f"初始化pgvector失败: {e}")


def get_db():
    """数据库依赖注入"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()