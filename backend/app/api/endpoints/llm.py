from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List
import openai

from ...core.database import get_db
from ...api.deps import get_current_user, get_current_admin_user
from ...models.llm import LLMModel, LLMKeyManager
from ...models.user import User
from ...services.rag import RAGService
from ...schemas.llm import (
    LLMModelCreate, LLMModelResponse, LLMModelUpdate,
    LLMModelWithKey, LLMModelListResponse
)

router = APIRouter()


@router.get("/models", response_model=List[dict])
def get_all_llm_models(
    db: Session = Depends(get_db)
):
    """获取所有大模型列表（无需登录，用于公开对话选择模型）"""
    models = db.query(LLMModel).filter(LLMModel.is_active == True).all()
    return [
        {
            "id": model.id,
            "name": model.name,
            "provider": model.provider,
            "model_name": model.model_name,
            "is_active": model.is_active,
            "is_default": model.is_default
        }
        for model in models
    ]


@router.get("/", response_model=LLMModelListResponse)
def get_llm_models(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取大模型列表（管理员权限）"""
    models = db.query(LLMModel).offset(skip).limit(limit).all()
    
    # 对普通用户隐藏API密钥
    if current_user.role != "admin":
        return {
            "models": [
                {
                    "id": model.id,
                    "name": model.name,
                    "provider": model.provider,
                    "model_name": model.model_name,
                    "base_url": model.base_url,
                    "is_active": model.is_active,
                    "is_default": model.is_default,
                    "created_at": model.created_at,
                    "updated_at": model.updated_at
                }
                for model in models
            ],
            "total": len(models)
        }
    
    # 管理员可以看到模型信息但看不到具体密钥
    return {
        "models": [
            {
                "id": model.id,
                "name": model.name,
                "provider": model.provider,
                "model_name": model.model_name,
                "base_url": model.base_url,
                "is_active": model.is_active,
                "is_default": model.is_default,
                "created_at": model.created_at,
                "updated_at": model.updated_at
            }
            for model in models
        ],
        "total": len(models)
    }


@router.get("/active", response_model=List[LLMModelResponse])
def get_active_llm_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取激活的大模型列表"""
    models = db.query(LLMModel).filter(LLMModel.is_active == True).all()
    return models


@router.get("/{model_id}", response_model=LLMModelResponse)
def get_llm_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取大模型详情"""
    model = db.query(LLMModel).filter(LLMModel.id == model_id).first()
    if model is None:
        raise HTTPException(status_code=404, detail="大模型不存在")
    return model


@router.post("/", response_model=LLMModelResponse)
def create_llm_model(
    model: LLMModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """创建大模型配置（需要管理员权限）"""
    try:
        # 检查名称是否已存在
        existing = db.query(LLMModel).filter(LLMModel.name == model.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="模型名称已存在")
        
        # 加密API密钥
        key_manager = LLMKeyManager()
        encrypted_key = key_manager.encrypt_api_key(model.api_key)
        
        # 如果设置为默认模型，取消其他模型的默认状态
        if model.is_default:
            db.query(LLMModel).update({LLMModel.is_default: False})
        
        # 创建新模型
        db_model = LLMModel(
            name=model.name,
            provider=model.provider,
            model_name=model.model_name,
            api_key_encrypted=encrypted_key,
            base_url=model.base_url,
            is_active=model.is_active,
            is_default=model.is_default
        )
        
        db.add(db_model)
        db.commit()
        db.refresh(db_model)
        
        return db_model
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise


@router.put("/{model_id}", response_model=LLMModelResponse)
def update_llm_model(
    model_id: int,
    model_update: LLMModelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """更新大模型配置（需要管理员权限）"""
    db_model = db.query(LLMModel).filter(LLMModel.id == model_id).first()
    if db_model is None:
        raise HTTPException(status_code=404, detail="大模型不存在")
    
    # 检查名称是否已存在（排除自身）
    if model_update.name and model_update.name != db_model.name:
        existing = db.query(LLMModel).filter(
            LLMModel.name == model_update.name,
            LLMModel.id != model_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="模型名称已存在")
    
    # 如果设置为默认模型，取消其他模型的默认状态
    if model_update.is_default:
        db.query(LLMModel).filter(LLMModel.id != model_id).update({LLMModel.is_default: False})
    
    # 更新字段
    update_data = model_update.dict(exclude_unset=True)
    
    # 如果提供了新的API密钥，需要加密
    if 'api_key' in update_data and update_data['api_key']:
        key_manager = LLMKeyManager()
        update_data['api_key_encrypted'] = key_manager.encrypt_api_key(update_data['api_key'])
        del update_data['api_key']
    
    for field, value in update_data.items():
        setattr(db_model, field, value)
    
    db.commit()
    db.refresh(db_model)
    
    return db_model


@router.delete("/{model_id}")
def delete_llm_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """删除大模型配置（需要管理员权限）"""
    db_model = db.query(LLMModel).filter(LLMModel.id == model_id).first()
    if db_model is None:
        raise HTTPException(status_code=404, detail="大模型不存在")
    
    # 不能删除默认模型
    if db_model.is_default:
        raise HTTPException(status_code=400, detail="不能删除默认模型")
    
    db.delete(db_model)
    db.commit()
    
    return {"message": "大模型删除成功"}


@router.get("/{model_id}/test")
def test_llm_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """测试大模型连接（需要管理员权限）"""
    model = db.query(LLMModel).filter(LLMModel.id == model_id).first()
    if model is None:
        raise HTTPException(status_code=404, detail="大模型不存在")
    
    # 解密API密钥
    key_manager = LLMKeyManager()
    try:
        api_key = key_manager.decrypt_api_key(model.api_key_encrypted)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"API密钥解密失败: {e}")
    
    # 测试模型连接
    try:
        rag_service = RAGService()
        
        # 使用测试问题验证连接
        test_question = "你好，请回复'连接成功'"
        
        # 临时设置API密钥
        original_key = openai.api_key
        openai.api_key = api_key
        
        try:
            response = openai.chat.completions.create(
                model=model.model_name,
                messages=[{"role": "user", "content": test_question}],
                max_tokens=50
            )
            
            result = response.choices[0].message.content
            return {
                "success": True,
                "message": "模型连接测试成功",
                "response": result
            }
        finally:
            openai.api_key = original_key
            
    except Exception as e:
        return {
            "success": False,
            "message": f"模型连接测试失败: {str(e)}"
        }