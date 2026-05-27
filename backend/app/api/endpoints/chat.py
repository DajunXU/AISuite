from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Optional
import json
import hashlib
import uuid

from ...core.database import get_db
from ...core.logger import get_logger
from ...api.deps import get_current_user
from ...models.chat import Conversation as ConversationModel
from ...models.knowledge import KnowledgeBase
from ...models.user import User as UserModel
from ...models.llm import LLMModel, LLMKeyManager
from ...models.knowledge import UploadedFile
from ...models.knowledge import UserKnowledgePermission
from ...schemas.chat import (
    ChatMessageCreate, ChatMessageResponse, ChatStreamResponse,
    Conversation, ConversationCreate, ConversationUpdate, ConversationList,
    FeedbackCreate
)
from ...services.cache import CacheService
from ...models.cache import ConversationMessage
from ...services.rag import RAGService

router = APIRouter()
logger = get_logger("chat")


# 测试端点 - 不需要认证
@router.get("/test")
def test_endpoint():
    """测试端点"""
    logger.info("[TEST] 测试端点被调用")
    return {"message": "test ok"}


# 对话管理接口

@router.get("/conversations", response_model=ConversationList)
def get_conversations(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """获取用户的对话列表"""
    logger.info(f"[GET CONVERSATIONS] user_id: {current_user.id}")
    query = db.query(ConversationModel).filter(ConversationModel.user_id == current_user.id)
    
    if not include_archived:
        query = query.filter(ConversationModel.is_archived == False)
    
    conversations = query.order_by(ConversationModel.updated_at.desc()).all()
    return ConversationList(conversations=conversations)


@router.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """创建新对话"""
    logger.info(f"[DEBUG] 创建对话 - user_id: {current_user.id}, title: {conversation.title}")
    try:
        db_conversation = ConversationModel(
            user_id=current_user.id,
            title=conversation.title
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        logger.info(f"[DEBUG] 对话创建成功 - id: {db_conversation.id}")
        return db_conversation
    except Exception as e:
        logger.error(f"[DEBUG] 创建对话失败: {e}", exc_info=True)
        raise


@router.put("/conversations/{conversation_id}", response_model=Conversation)
def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """更新对话（标题、收藏、归档）"""
    conversation = db.query(ConversationModel).filter(
        ConversationModel.id == conversation_id,
        ConversationModel.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    if conversation_update.title is not None:
        conversation.title = conversation_update.title
    if conversation_update.is_favorite is not None:
        conversation.is_favorite = conversation_update.is_favorite
    if conversation_update.is_archived is not None:
        conversation.is_archived = conversation_update.is_archived
    
    db.commit()
    db.refresh(conversation)
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """删除对话"""
    conversation = db.query(ConversationModel).filter(
        ConversationModel.id == conversation_id,
        ConversationModel.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 删除对话及其所有消息
    db.query(ConversationMessage).filter(ConversationMessage.conversation_id == str(conversation_id)).delete()
    db.delete(conversation)
    db.commit()
    return None


@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessageResponse])
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """获取对话的所有消息"""
    conversation = db.query(ConversationModel).filter(
        ConversationModel.id == conversation_id,
        ConversationModel.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 使用 ConversationMessage 获取消息
    messages = db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == str(conversation_id),
        ConversationMessage.user_key == str(current_user.id)
    ).order_by(ConversationMessage.created_time).all()
    
    return messages


@router.post("/", response_model=ChatMessageResponse)
async def chat(
    message: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """发送聊天消息（异步）"""
    # 检查文本知识库权限
    text_kb_id = message.text_kb_id
    db_kb_id = message.db_kb_id
    
    if text_kb_id:
        knowledge_base = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == text_kb_id
        ).first()
        
        if knowledge_base is None:
            raise HTTPException(status_code=404, detail="文本知识库不存在")
        
        # 检查权限
        if not _has_kb_access(current_user, knowledge_base, db):
            raise HTTPException(status_code=403, detail="没有文本知识库访问权限")
    
    # 检查数据库知识库权限
    if db_kb_id:
        db_knowledge_base = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == db_kb_id
        ).first()
        
        if db_knowledge_base is None:
            raise HTTPException(status_code=404, detail="数据库知识库不存在")
        
        # 检查权限
        if not _has_kb_access(current_user, db_knowledge_base, db):
            raise HTTPException(status_code=403, detail="没有数据库知识库访问权限")
    
    # 使用RAG服务生成回答
    rag_service = RAGService(db)
    
    # 优先使用指定模型的API密钥，如果没有指定则使用默认模型
    model_id_to_use = message.model_id
    
    # 如果没有指定模型ID，查找默认模型
    if not model_id_to_use:
        default_model = db.query(LLMModel).filter(LLMModel.is_default == True).first()
        if default_model and default_model.is_active:
            model_id_to_use = default_model.id
    
    # 使用对应的API密钥
    if model_id_to_use:
        # 获取模型配置
        model = db.query(LLMModel).filter(LLMModel.id == model_id_to_use).first()
        if model and model.is_active:
            # 解密API密钥
            key_manager = LLMKeyManager()
            try:
                api_key = key_manager.decrypt_api_key(model.api_key_encrypted)
                rag_service._init_llm(
                    api_key=api_key,
                    base_url=model.base_url,
                    provider=model.provider,
                    model=model
                )
                logger.info(f"使用模型: {model.name} (ID: {model.id}), 提供商: {model.provider}")
            except Exception as e:
                logger.error(f"API密钥解密失败: {e}")
    else:
        logger.warning("没有找到有效的模型配置，使用环境默认密钥")
    
    try:
        logger.info(f"开始处理问题: {message.question}")
        logger.info(f"用户ID: {current_user.id}, 文本知识库ID: {text_kb_id}, 数据库知识库ID: {db_kb_id}")
        answer, sources = await rag_service.generate_answer(
            question=message.question,
            user_id=current_user.id,
            text_kb_id=text_kb_id,
            db_kb_id=db_kb_id
        )
        logger.info(f"问题处理完成，回答长度: {len(answer) if answer else 0}")
    except Exception as e:
        logger.error(f"RAG服务处理错误: {e}", exc_info=True)
        answer = "抱歉，我暂时无法回答您的问题。请稍后再试。"
        sources = None
    
    # 保存对话历史到 ConversationMessage
    message_id = str(uuid.uuid4())
    question_hash = hashlib.md5(message.question.encode('utf-8')).hexdigest()
    conversation_id_str = str(message.conversation_id) if message.conversation_id else str(uuid.uuid4())
    
    chat_message = ConversationMessage(
        message_id=message_id,
        conversation_id=conversation_id_str,
        user_key=str(current_user.id),
        module_key="chat",
        question_text=message.question,
        question_hash=question_hash,
        answer_text=answer,
        model_name=model.name if model else "unknown",
        total_duration=0,
        answer_source=0,
        sequence_num=1
    )
    
    db.add(chat_message)
    db.commit()
    db.refresh(chat_message)
    
    # 如果有对话ID，更新对话的更新时间
    if message.conversation_id:
        conversation = db.query(ConversationModel).filter(ConversationModel.id == message.conversation_id).first()
        if conversation:
            if conversation.title == "新对话" and message.question:
                conversation.title = message.question[:20] + ("..." if len(message.question) > 20 else "")
            conversation.updated_at = func.now()
            db.commit()
    
    return chat_message


@router.post("/stream")
async def chat_stream(
    message: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """发送聊天消息（流式）"""
    # 检查文本知识库权限
    text_kb_id = message.text_kb_id
    db_kb_id = message.db_kb_id
    
    if text_kb_id:
        knowledge_base = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == text_kb_id
        ).first()
        
        if knowledge_base is None:
            raise HTTPException(status_code=404, detail="文本知识库不存在")
        
        # 检查权限
        if not _has_kb_access(current_user, knowledge_base, db):
            raise HTTPException(status_code=403, detail="没有文本知识库访问权限")
    
    if db_kb_id:
        db_knowledge_base = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == db_kb_id
        ).first()
        
        if db_knowledge_base is None:
            raise HTTPException(status_code=404, detail="数据库知识库不存在")
        
        # 检查权限
        if not _has_kb_access(current_user, db_knowledge_base, db):
            raise HTTPException(status_code=403, detail="没有数据库知识库访问权限")
    
    # 创建流式响应
    async def generate():
        rag_service = RAGService(db)
        
        # 优先使用指定模型的API密钥，如果没有指定则使用默认模型
        model_id_to_use = message.model_id
        
        # 如果没有指定模型ID，查找默认模型
        if not model_id_to_use:
            default_model = db.query(LLMModel).filter(LLMModel.is_default == True).first()
            if default_model and default_model.is_active:
                model_id_to_use = default_model.id
        
        # 使用对应的API密钥
        if model_id_to_use:
            # 获取模型配置
            model = db.query(LLMModel).filter(LLMModel.id == model_id_to_use).first()
            if model and model.is_active:
                # 解密API密钥
                key_manager = LLMKeyManager()
                try:
                    api_key = key_manager.decrypt_api_key(model.api_key_encrypted)
                    rag_service._init_llm(
                        api_key=api_key,
                        base_url=model.base_url,
                        provider=model.provider,
                        model=model
                    )
                    logger.info(f"使用模型: {model.name} (ID: {model.id}), 提供商: {model.provider}")
                except Exception as e:
                    logger.error(f"API密钥解密失败: {e}")
        else:
            logger.warning("没有找到有效的模型配置，使用环境默认密钥")
        
        # 流式生成回答
        async for chunk in rag_service.stream_answer(
            question=message.question,
            user_id=current_user.id,
            text_kb_id=text_kb_id,
            db_kb_id=db_kb_id
        ):
            yield f"data: {json.dumps(chunk.dict())}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/feedback")
def submit_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """提交用户反馈"""
    cache_service = CacheService(db)
    message_id = feedback_data.message_id

    logger.info(f"[FEEDBACK] 收到反馈请求: message_id={message_id}, feedback={feedback_data.feedback}")

    msg = db.query(ConversationMessage).filter(
        (ConversationMessage.message_id == message_id) |
        (ConversationMessage.id == int(message_id) if message_id.isdigit() else False)
    ).first()

    logger.info(f"[FEEDBACK] 查询结果: {msg}")

    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在或已反馈")

    if msg.user_feedback is not None:
        raise HTTPException(status_code=400, detail="消息不存在或已反馈")

    msg.user_feedback = feedback_data.feedback
    msg.feedback_remark = feedback_data.remark
    cache_service._update_quality_score(msg.message_id, feedback_data.feedback)

    db.commit()

    return {"message": "反馈提交成功"}


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # 统计用户自己的知识库数量
    knowledge_bases = db.query(KnowledgeBase).filter(
        KnowledgeBase.owner_id == current_user.id
    ).count()
    
    chat_messages = db.query(ConversationMessage).filter(
        ConversationMessage.user_key == str(current_user.id)
    ).count()
    
    active_users = db.query(UserModel).filter(
        UserModel.is_active == True
    ).count()
    
    documents = db.query(UploadedFile).join(KnowledgeBase).filter(
        KnowledgeBase.owner_id == current_user.id
    ).count()
    
    recent_activities = db.query(ConversationMessage).filter(
        ConversationMessage.user_key == str(current_user.id)
    ).order_by(ConversationMessage.created_time.desc()).limit(5).all()
    
    activities = []
    for chat in recent_activities:
        activities.append({
            "id": chat.id,
            "time": chat.created_time.strftime("%Y-%m-%d %H:%M") if chat.created_time else "",
            "content": f"进行了智能对话: {chat.question_text[:30]}..." if chat.question_text else "进行了智能对话"
        })
    
    return {
        "stats": {
            "knowledgeBases": knowledge_bases,
            "chatMessages": chat_messages,
            "activeUsers": active_users,
            "documents": documents
        },
        "recentActivities": activities
    }


@router.get("/history", response_model=List[ChatMessageResponse])
def get_chat_history(
    knowledge_base_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """获取对话历史"""
    query = db.query(ConversationMessage).filter(ConversationMessage.user_key == str(current_user.id))
    
    chat_history = query.order_by(ConversationMessage.created_time.desc()).offset(skip).limit(limit).all()
    return chat_history


@router.get("/history/{chat_id}", response_model=ChatMessageResponse)
def get_chat_detail(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """获取单条对话详情"""
    chat_history = db.query(ConversationMessage).filter(
        ConversationMessage.id == chat_id,
        ConversationMessage.user_key == str(current_user.id)
    ).first()
    
    if chat_history is None:
        raise HTTPException(status_code=404, detail="对话记录不存在")
    
    return chat_history


@router.delete("/history/{chat_id}")
def delete_chat_history(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """删除对话记录"""
    chat_history = db.query(ConversationMessage).filter(
        ConversationMessage.id == chat_id,
        ConversationMessage.user_key == str(current_user.id)
    ).first()
    
    if chat_history is None:
        raise HTTPException(status_code=404, detail="对话记录不存在")
    
    db.delete(chat_history)
    db.commit()
    return {"message": "对话记录删除成功"}


def _has_kb_access(user: UserModel, knowledge_base: KnowledgeBase, db: Session) -> bool:
    """检查用户是否有知识库访问权限"""
    if user.role == "admin":
        return True
    
    if knowledge_base.owner_id == user.id:
        return True
    
    if knowledge_base.is_public:
        return True
    
    permission = db.query(UserKnowledgePermission).filter(
        UserKnowledgePermission.user_id == user.id,
        UserKnowledgePermission.knowledge_base_id == knowledge_base.id,
        UserKnowledgePermission.can_read == True
    ).first()
    
    return permission is not None


@router.post("/smart", response_model=ChatMessageResponse)
async def smart_chat(
    message: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """智能聊天 - 根据知识库类型自动选择处理方式"""
    # 检查知识库权限
    if not message.knowledge_base_id:
        raise HTTPException(status_code=400, detail="需要指定知识库")
    
    knowledge_base = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == message.knowledge_base_id
    ).first()
    
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限
    if not _has_kb_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有知识库访问权限")
    
    try:
        # 使用智能问答服务
        rag_service = RAGService(db)
        answer, sources, metadata = await rag_service.smart_answer(
            question=message.question,
            knowledge_base=knowledge_base
        )
        
        # 获取模型名称
        model_name = "unknown"
        if message.model_id:
            model = db.query(LLMModel).filter(LLMModel.id == message.model_id).first()
            if model:
                model_name = model.name
        
        # 保存对话历史到 ConversationMessage
        message_id = str(uuid.uuid4())
        question_hash = hashlib.md5(message.question.encode('utf-8')).hexdigest()
        conversation_id_str = str(message.conversation_id) if message.conversation_id else str(uuid.uuid4())
        
        chat_message = ConversationMessage(
            message_id=message_id,
            conversation_id=conversation_id_str,
            user_key=str(current_user.id),
            module_key="chat",
            question_text=message.question,
            question_hash=question_hash,
            answer_text=answer,
            model_name=model_name,
            total_duration=0,
            answer_source=0,
            sequence_num=1
        )
        
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        
        return chat_message
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能问答失败: {str(e)}")


@router.post("/smart/stream")
async def smart_chat_stream(
    message: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """智能聊天 - 流式响应"""
    # 检查知识库权限
    if not message.knowledge_base_id:
        raise HTTPException(status_code=400, detail="需要指定知识库")
    
    knowledge_base = db.query(KnowledgeBase).filter(
        KnowledgeBase.id == message.knowledge_base_id
    ).first()
    
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限
    if not _has_kb_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有知识库访问权限")
    
    # 创建流式响应
    async def generate():
        try:
            # 使用智能问答服务
            rag_service = RAGService(db)
            answer, sources, metadata = await rag_service.smart_answer(
                question=message.question,
                knowledge_base=knowledge_base
            )
            
            # 模拟流式输出
            words = answer.split()
            for i, word in enumerate(words):
                is_final = i == len(words) - 1
                chunk = ChatStreamResponse(
                    content=word + " ",
                    is_final=is_final,
                    sources=sources if is_final else None,
                    metadata=metadata if is_final else None
                )
                yield f"data: {json.dumps(chunk.dict())}\n\n"
                
                # 添加延迟以模拟流式效果
                import asyncio
                await asyncio.sleep(0.05)
                
        except Exception as e:
            error_chunk = ChatStreamResponse(
                content=f"智能问答失败: {str(e)}",
                is_final=True
            )
            yield f"data: {json.dumps(error_chunk.dict())}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )