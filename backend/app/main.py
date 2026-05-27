from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import threading

from .core.config import settings
from .core.database import engine, Base
from .core.logger import get_logger
from .core.errors import APIException
from .core.rate_limit import RateLimitMiddleware
from .core.audit_middleware import AuditMiddleware
from .api.endpoints import auth, users, knowledge, chat, permission
from .api.endpoints import api_router
from .api.endpoints.audit import router as audit_router
from .api.endpoints.kb_stats import router as kb_stats_router

logger = get_logger("main")

# 创建FastAPI应用（启用调试模式）
app = FastAPI(
    title="AI知识库智能对话系统",
    description="基于FastAPI+Vue3的企业级知识库问答系统",
    version="1.0.0",
    debug=True
)

# 配置限流中间件
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        default_limit=settings.RATE_LIMIT_DEFAULT,
        default_window=settings.RATE_LIMIT_WINDOW
    )

# 配置审计中间件
app.add_middleware(AuditMiddleware)

# 配置CORS - 简化配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识库管理"])
app.include_router(audit_router, prefix="/api/audit", tags=["审计日志"])
app.include_router(kb_stats_router, prefix="/api/knowledge", tags=["知识库统计"])
# chat.router 已在 api_router 中注册
app.include_router(api_router, prefix="/api")

# 包含大模型管理路由
try:
    from .api.endpoints import llm
    app.include_router(llm.router, prefix="/api/llm", tags=["大模型管理"])
except ImportError as e:
    logger.warning(f"无法导入大模型管理路由: {e}")

# 创建上传目录
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# 挂载静态文件
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# 全局异常处理器
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """处理自定义 API 异常"""
    logger.warning(f"API异常: {exc.message} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "detail": exc.detail
            }
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """处理全局未捕获异常"""
    logger.error(f"全局异常: {type(exc).__name__}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 1000,
                "message": "服务器内部错误",
                "detail": str(exc) if settings.LOG_LEVEL == "DEBUG" else "请联系管理员"
            }
        }
    )


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    
    # 启动消息向量化调度器（后台线程）
    from .services.vectorization_task import start_vectorization_scheduler
    vectorization_thread = threading.Thread(
        target=start_vectorization_scheduler,
        args=(30,),
        daemon=True
    )
    vectorization_thread.start()
    logger.info("消息向量化调度器已启动")


@app.get("/")
async def root():
    """根路径"""
    return {"message": "AI知识库智能对话系统 API"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
