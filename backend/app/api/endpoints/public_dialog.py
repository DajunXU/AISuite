from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import secrets
import string

from ...core.database import get_db
from ...core.logger import get_logger
from ...core.config import settings
from ...api.deps import get_current_user
from ...models.user import User
from ...models.knowledge import KnowledgeBase
from ...models.public_dialog import PublicDialog, PublicDialogMessage
from ...models.llm import LLMModel, LLMKeyManager
from ...services.rag import RAGService
from ...schemas.public_dialog import (
    PublicDialogCreate,
    PublicDialogUpdate,
    PublicDialogResponse,
    PublicDialogList,
    PublicDialogMessageCreate,
    PublicDialogChatResponse,
    PublicDialogMessageResponse
)

router = APIRouter()
logger = get_logger("public_dialog")


def generate_dialog_code(length: int = 12) -> str:
    """生成随机对话码"""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@router.post("/", response_model=PublicDialogResponse, status_code=status.HTTP_201_CREATED)
def create_public_dialog(
    dialog: PublicDialogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建公开对话"""
    dialog_code = generate_dialog_code()
    
    db_dialog = PublicDialog(
        dialog_code=dialog_code,
        name=dialog.name,
        description=dialog.description,
        welcome_message=dialog.welcome_message,
        recommended_questions=dialog.recommended_questions,
        custom_prompt=dialog.custom_prompt,
        knowledge_base_ids=dialog.knowledge_base_ids,
        owner_id=current_user.id,
        language=dialog.language,
        theme_config=dialog.theme_config,
        webhook_url=dialog.webhook_url,
        feedback_enabled=dialog.feedback_enabled,
        expires_at=dialog.expires_at
    )
    
    db.add(db_dialog)
    db.commit()
    db.refresh(db_dialog)
    
    return db_dialog


@router.get("/", response_model=PublicDialogList)
def get_public_dialogs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的公开对话列表"""
    logger.info(f"[PublicDialog] 获取列表，用户: {current_user.username}")
    try:
        query = db.query(PublicDialog).filter(PublicDialog.owner_id == current_user.id)
        total = query.count()
        dialogs = query.order_by(PublicDialog.created_at.desc()).offset(skip).limit(limit).all()
        logger.info(f"[PublicDialog] 找到 {total} 条记录")
        return PublicDialogList(dialogs=dialogs, total=total)
    except Exception as e:
        logger.error(f"[PublicDialog] 错误: {e}")
        import traceback
        traceback.print_exc()
        raise


@router.get("/{dialog_id}", response_model=PublicDialogResponse)
def get_public_dialog(
    dialog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取公开对话详情"""
    dialog = db.query(PublicDialog).filter(
        PublicDialog.id == dialog_id,
        PublicDialog.owner_id == current_user.id
    ).first()
    
    if not dialog:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return dialog


@router.put("/{dialog_id}", response_model=PublicDialogResponse)
def update_public_dialog(
    dialog_id: int,
    dialog: PublicDialogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新公开对话"""
    db_dialog = db.query(PublicDialog).filter(
        PublicDialog.id == dialog_id,
        PublicDialog.owner_id == current_user.id
    ).first()
    
    if not db_dialog:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    update_data = dialog.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_dialog, field, value)
    
    db.commit()
    db.refresh(db_dialog)
    
    return db_dialog


@router.delete("/{dialog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_public_dialog(
    dialog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除公开对话"""
    db_dialog = db.query(PublicDialog).filter(
        PublicDialog.id == dialog_id,
        PublicDialog.owner_id == current_user.id
    ).first()
    
    if not db_dialog:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    db.delete(db_dialog)
    db.commit()
    
    return None


@router.get("/by-code/{dialog_code}", response_model=PublicDialogResponse)
def get_public_dialog_by_code(
    dialog_code: str,
    db: Session = Depends(get_db)
):
    """通过对话码获取公开对话（无需登录）"""
    dialog = db.query(PublicDialog).filter(
        PublicDialog.dialog_code == dialog_code,
        PublicDialog.is_active == True
    ).first()
    
    if not dialog:
        raise HTTPException(status_code=404, detail="对话不存在或已停用")
    
    dialog.visit_count += 1
    db.commit()
    
    return dialog


@router.post("/by-code/{dialog_code}/chat", response_model=PublicDialogChatResponse)
async def chat_with_public_dialog(
    dialog_code: str,
    message: PublicDialogMessageCreate,
    db: Session = Depends(get_db)
):
    """公开对话聊天（无需登录）"""
    logger.info(f"[PublicDialog] chat请求, dialog_code: {dialog_code}")
    import datetime as dt
    
    try:
        dialog = db.query(PublicDialog).filter(
            PublicDialog.dialog_code == dialog_code,
            PublicDialog.is_active == True
        ).first()
        
        if not dialog:
            raise HTTPException(status_code=404, detail="对话不存在或已停用")
        
        logger.info(f"[PublicDialog] 找到对话框: {dialog.name}, model_id: {dialog.model_id}")
        
        if dialog.expires_at and dialog.expires_at < dt.datetime.now():
            logger.warning(f"[PublicDialog] 对话已过期: {dialog.expires_at}")
            raise HTTPException(status_code=410, detail="对话已过期")
        
        kb_ids = dialog.knowledge_base_ids or []
        text_kb_id = None
        db_kb_id = None
        
        for kb_id in kb_ids:
            kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
            if kb:
                if kb.kb_type == "file":
                    text_kb_id = kb_id
                elif kb.kb_type == "db":
                    db_kb_id = kb_id
        
        model_id_to_use = dialog.model_id
        if not model_id_to_use:
            default_model = db.query(LLMModel).filter(LLMModel.is_default == True).first()
            if default_model and default_model.is_active:
                model_id_to_use = default_model.id
        
        api_key = None
        base_url = None
        provider = None
        model_obj = None
        
        if model_id_to_use:
            model = db.query(LLMModel).filter(LLMModel.id == model_id_to_use).first()
            if model and model.is_active:
                key_manager = LLMKeyManager()
                api_key = key_manager.decrypt_api_key(model.api_key_encrypted)
                base_url = model.base_url
                provider = model.provider
                model_obj = model
                logger.info(f"[公开对话] 使用模型: {model.name} (ID: {model.id}), 提供商: {model.provider}")
        
        rag_service = RAGService(db)
        
        answer, sources = await rag_service.generate_answer(
            question=message.question,
            user_id=dialog.owner_id or 1,
            text_kb_id=text_kb_id,
            db_kb_id=db_kb_id,
            api_key=api_key,
            base_url=base_url,
            provider=provider,
            model=model_obj,
            system_prompt=dialog.custom_prompt
        )
        
        return PublicDialogChatResponse(
            answer=answer,
            sources=sources,
            message_id=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PublicDialog] 聊天错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dialog_id}/messages", response_model=List[PublicDialogMessageResponse])
def get_dialog_messages(
    dialog_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取对话的消息历史"""
    dialog = db.query(PublicDialog).filter(
        PublicDialog.id == dialog_id,
        PublicDialog.owner_id == current_user.id
    ).first()
    
    if not dialog:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    messages = db.query(PublicDialogMessage).filter(
        PublicDialogMessage.dialog_id == dialog_id
    ).order_by(PublicDialogMessage.created_at.desc()).offset(skip).limit(limit).all()
    
    return messages


@router.get("/by-code/{dialog_code}/messages", response_model=List[PublicDialogMessageResponse])
def get_public_dialog_messages(
    dialog_code: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """通过对话码获取公开对话的消息历史（无需登录）"""
    dialog = db.query(PublicDialog).filter(
        PublicDialog.dialog_code == dialog_code,
        PublicDialog.is_active == True
    ).first()
    
    if not dialog:
        raise HTTPException(status_code=404, detail="对话不存在或已停用")
    
    messages = db.query(PublicDialogMessage).filter(
        PublicDialogMessage.dialog_id == dialog.id
    ).order_by(PublicDialogMessage.created_at.desc()).offset(skip).limit(limit).all()
    
    return messages


@router.get("/{dialog_id}/access-url")
def get_dialog_access_url(
    dialog_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取对话的访问URL"""
    dialog = db.query(PublicDialog).filter(
        PublicDialog.id == dialog_id,
        PublicDialog.owner_id == current_user.id
    ).first()
    
    if not dialog:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    return {
        "dialog_code": dialog.dialog_code,
        "access_url": f"/dialog/{dialog.dialog_code}",
        "full_url": f"{settings.FRONTEND_URL}/dialog/{dialog.dialog_code}"
    }
