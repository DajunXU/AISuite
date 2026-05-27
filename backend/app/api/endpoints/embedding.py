from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
from openai import OpenAI

from ...core.database import get_db
from ...core.config import settings
from ...api.deps import get_current_user, get_current_admin_user
from ...models.embedding import EmbeddingModel, EmbeddingKeyManager
from ...models.knowledge import KnowledgeBase
from ...models.user import User
from ...services.rag import RAGService
from ...schemas.embedding import (
    EmbeddingModelCreate, EmbeddingModelResponse, EmbeddingModelUpdate,
    EmbeddingModelWithKey, EmbeddingModelListResponse
)

router = APIRouter()


@router.get("/", response_model=EmbeddingModelListResponse)
def get_embedding_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取向量模型列表"""
    models = db.query(EmbeddingModel).offset(skip).limit(limit).all()
    
    if current_user.role != "admin":
        return {
            "models": [
                {
                    "id": model.id,
                    "name": model.name,
                    "provider": model.provider,
                    "model_name": model.model_name,
                    "base_url": model.base_url,
                    "dimensions": model.dimensions,
                    "max_tokens": model.max_tokens,
                    "is_active": model.is_active,
                    "is_default": model.is_default,
                    "is_api": model.is_api,
                    "created_at": model.created_at,
                    "updated_at": model.updated_at
                }
                for model in models
            ],
            "total": len(models)
        }
    
    return {
        "models": [
            {
                "id": model.id,
                "name": model.name,
                "provider": model.provider,
                "model_name": model.model_name,
                "base_url": model.base_url,
                "dimensions": model.dimensions,
                "max_tokens": model.max_tokens,
                "is_active": model.is_active,
                "is_default": model.is_default,
                "is_api": model.is_api,
                "created_at": model.created_at,
                "updated_at": model.updated_at
            }
            for model in models
        ],
        "total": len(models)
    }


@router.get("/active", response_model=List[EmbeddingModelResponse])
def get_active_embedding_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取激活的向量模型列表"""
    models = db.query(EmbeddingModel).filter(EmbeddingModel.is_active == True).all()
    return models


@router.get("/{model_id}", response_model=EmbeddingModelResponse)
def get_embedding_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取向量模型详情"""
    model = db.query(EmbeddingModel).filter(EmbeddingModel.id == model_id).first()
    if model is None:
        raise HTTPException(status_code=404, detail="向量模型不存在")
    return model


@router.post("/", response_model=EmbeddingModelResponse)
def create_embedding_model(
    model: EmbeddingModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建向量模型配置（需要管理员权限）"""
    try:
        existing = db.query(EmbeddingModel).filter(EmbeddingModel.name == model.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="模型名称已存在")
        
        key_manager = EmbeddingKeyManager()
        encrypted_key = ""
        if model.api_key:
            encrypted_key = key_manager.encrypt_api_key(model.api_key)
        
        if model.is_default:
            db.query(EmbeddingModel).update({EmbeddingModel.is_default: False})
        
        db_model = EmbeddingModel(
            name=model.name,
            provider=model.provider,
            model_name=model.model_name,
            api_key_encrypted=encrypted_key,
            base_url=model.base_url,
            dimensions=model.dimensions,
            max_tokens=model.max_tokens,
            is_active=model.is_active,
            is_default=model.is_default,
            is_api=model.is_api
        )
        
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        
        return db_model
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{model_id}", response_model=EmbeddingModelResponse)
def update_embedding_model(
    model_id: int,
    model_update: EmbeddingModelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新向量模型配置（需要管理员权限）"""
    db_model = db.query(EmbeddingModel).filter(EmbeddingModel.id == model_id).first()
    if db_model is None:
        raise HTTPException(status_code=404, detail="向量模型不存在")
    
    if model_update.name and model_update.name != db_model.name:
        existing = db.query(EmbeddingModel).filter(
            EmbeddingModel.name == model_update.name,
            EmbeddingModel.id != model_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="模型名称已存在")
    
    if model_update.is_default:
        db.query(EmbeddingModel).filter(EmbeddingModel.id != model_id).update({EmbeddingModel.is_default: False})
    
    update_data = model_update.dict(exclude_unset=True)
    
    if 'api_key' in update_data and update_data['api_key']:
        key_manager = EmbeddingKeyManager()
        update_data['api_key_encrypted'] = key_manager.encrypt_api_key(update_data['api_key'])
        del update_data['api_key']
    
    for field, value in update_data.items():
        setattr(db_model, field, value)
    
    db.commit()
    db.refresh(db_model)
    
    return db_model


@router.delete("/{model_id}")
def delete_embedding_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除向量模型配置（需要管理员权限）"""
    db_model = db.query(EmbeddingModel).filter(EmbeddingModel.id == model_id).first()
    if db_model is None:
        raise HTTPException(status_code=404, detail="向量模型不存在")
    
    if db_model.is_default:
        raise HTTPException(status_code=400, detail="不能删除默认模型")
    
    kb_count = db.query(KnowledgeBase).filter(KnowledgeBase.embedding_model_id == model_id).count()
    if kb_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"该向量模型正在被 {kb_count} 个知识库使用，无法删除。请先修改这些知识库的向量模型配置。"
        )
    
    db.delete(db_model)
    db.commit()
    
    return {"message": "向量模型删除成功"}


@router.get("/{model_id}/test")
def test_embedding_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """测试向量模型连接（需要管理员权限）"""
    
    model = db.query(EmbeddingModel).filter(EmbeddingModel.id == model_id).first()
    if model is None:
        raise HTTPException(status_code=404, detail="向量模型不存在")
    
    try:
        key_manager = EmbeddingKeyManager()
        api_key = ""
        
        # 优先使用模型配置的API密钥
        if model.api_key_encrypted:
            api_key = key_manager.decrypt_api_key(model.api_key_encrypted)
        
        # 如果模型没有配置密钥，使用环境变量中的密钥
        if not api_key:
            if model.provider == "qwen" or "qwen" in (model.base_url or ""):
                api_key = os.environ.get("DASHSCOPE_API_KEY", "")
            elif model.provider == "zhipu":
                api_key = os.environ.get("ZHIPU_API_KEY", "")
            elif model.provider == "openai":
                api_key = settings.OPENAI_API_KEY
        
        if not api_key or api_key == "your-openai-api-key":
            return {
                "success": False,
                "message": "未配置API密钥，请先在向量模型配置中填写API密钥，或设置环境变量 DASHSCOPE_API_KEY/ZHIPU_API_KEY",
                "response": None
            }
        
        base_url = model.base_url or "https://api.openai.com/v1"
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.embeddings.create(
            model=model.model_name,
            input="测试文本"
        )
        
        return {
            "success": True,
            "message": "向量模型连接成功",
            "response": f"向量维度: {len(response.data[0].embedding)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接失败: {str(e)}",
            "response": None
        }
