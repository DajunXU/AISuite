from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .knowledge import router as knowledge_router
from .chat import router as chat_router
from .llm import router as llm_router
from .embedding import router as embedding_router
from .permission import router as permission_router
from .public_dialog import router as public_dialog_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(users_router, prefix="/users", tags=["用户"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["知识库"])
api_router.include_router(chat_router, prefix="/chat", tags=["智能问答"])
api_router.include_router(llm_router, prefix="/llm", tags=["大模型"])
api_router.include_router(embedding_router, prefix="/embedding", tags=["向量模型"])
api_router.include_router(permission_router, prefix="/permission", tags=["权限管理"])
api_router.include_router(public_dialog_router, prefix="/public-dialog", tags=["公开对话"])
