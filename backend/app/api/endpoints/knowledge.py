from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import asyncio

from ...core.database import get_db, SessionLocal
from ...core.logger import get_logger
from ...api.deps import get_current_user, get_current_admin_user
from ...models.knowledge import KnowledgeBase, UserKnowledgePermission, DocumentChunk, UploadedFile, DatabaseConnection, TableMetadata, ColumnMetadata, MetricDefinition, KnowledgeBaseRole
from ...models.user import User
from ...services.file_processor import FileProcessor, file_processor
from ...services.database_service import database_service
from ...schemas.knowledge import (
    KnowledgeBaseCreate, KnowledgeBaseResponse, 
    KnowledgeBaseUpdate, UserPermissionCreate, UserPermissionResponse,
    UploadedFileResponse, DatabaseConnectionCreate, DatabaseConnectionResponse
)

router = APIRouter()
logger = get_logger("knowledge")


@router.post("/", response_model=KnowledgeBaseResponse)
def create_knowledge_base(
    knowledge_base: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建知识库"""
    # 检查知识库名称是否已存在
    db_kb = db.query(KnowledgeBase).filter(
        KnowledgeBase.name == knowledge_base.name,
        KnowledgeBase.owner_id == current_user.id
    ).first()
    
    if db_kb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="知识库名称已存在"
        )
    
    db_kb = KnowledgeBase(
        **knowledge_base.dict(),
        owner_id=current_user.id
    )
    
    db.add(db_kb)
    db.commit()
    db.refresh(db_kb)
    
    # 自动为创建者添加读写权限
    permission = UserKnowledgePermission(
        user_id=current_user.id,
        knowledge_base_id=db_kb.id,
        can_read=True,
        can_write=True
    )
    db.add(permission)
    db.commit()
    
    return db_kb


@router.get("/", response_model=List[KnowledgeBaseResponse])
def read_knowledge_bases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户可访问的知识库列表"""
    if current_user.role == "admin":
        # 管理员可以查看所有知识库
        knowledge_bases = db.query(KnowledgeBase).offset(skip).limit(limit).all()
    else:
        # 普通用户只能查看自己创建的和被授权的知识库
        knowledge_bases = db.query(KnowledgeBase).filter(
            (KnowledgeBase.owner_id == current_user.id) |
            (KnowledgeBase.id.in_(
                db.query(UserKnowledgePermission.knowledge_base_id).filter(
                    UserKnowledgePermission.user_id == current_user.id,
                    UserKnowledgePermission.can_read == True
                )
            )) |
            (KnowledgeBase.is_public == True)
        ).offset(skip).limit(limit).all()
    
    return knowledge_bases


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
def read_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库详情"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限
    if not _has_kb_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有访问权限")
    
    return knowledge_base


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
def update_knowledge_base(
    kb_id: int,
    knowledge_base: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新知识库信息"""
    db_kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if db_kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限（只有所有者或具有写权限的用户可以修改）
    if db_kb.owner_id != current_user.id and not _has_kb_write_access(current_user, db_kb, db):
        raise HTTPException(status_code=403, detail="没有修改权限")
    
    update_data = knowledge_base.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_kb, field, value)
    
    db.commit()
    db.refresh(db_kb)
    return db_kb


@router.delete("/{kb_id}")
def delete_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除知识库（仅所有者）"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if knowledge_base.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有所有者可以删除知识库")
    
    # 先删除关联的数据
    # 1. 删除文档片段
    db.query(DocumentChunk).filter(DocumentChunk.knowledge_base_id == kb_id).delete()
    
    # 2. 删除上传的文件记录
    db.query(UploadedFile).filter(UploadedFile.knowledge_base_id == kb_id).delete()
    
    # 3. 删除数据库连接配置
    db.query(DatabaseConnection).filter(DatabaseConnection.knowledge_base_id == kb_id).delete()
    
    # 4. 删除用户权限
    db.query(UserKnowledgePermission).filter(UserKnowledgePermission.knowledge_base_id == kb_id).delete()
    
    # 5. 删除知识库角色权限
    db.query(KnowledgeBaseRole).filter(KnowledgeBaseRole.knowledge_base_id == kb_id).delete()
    
    db.commit()
    
    # 最后删除知识库
    db.delete(knowledge_base)
    db.commit()
    return {"message": "知识库删除成功"}


class BatchDeleteRequest(BaseModel):
    kb_ids: List[int]

@router.post("/batch-delete")
def batch_delete_knowledge_bases(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量删除知识库"""
    if not request.kb_ids:
        raise HTTPException(status_code=400, detail="请选择要删除的知识库")
    
    deleted_count = 0
    failed_items = []
    
    for kb_id in request.kb_ids:
        knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if knowledge_base is None:
            failed_items.append({"id": kb_id, "error": "知识库不存在"})
            continue
        
        if knowledge_base.owner_id != current_user.id and current_user.role != "admin":
            failed_items.append({"id": kb_id, "error": "没有删除权限"})
            continue
        
        try:
            db.query(DocumentChunk).filter(DocumentChunk.knowledge_base_id == kb_id).delete()
            db.query(UploadedFile).filter(UploadedFile.knowledge_base_id == kb_id).delete()
            db.query(DatabaseConnection).filter(DatabaseConnection.knowledge_base_id == kb_id).delete()
            db.query(UserKnowledgePermission).filter(UserKnowledgePermission.knowledge_base_id == kb_id).delete()
            db.delete(knowledge_base)
            db.commit()
            deleted_count += 1
        except Exception as e:
            db.rollback()
            failed_items.append({"id": kb_id, "error": str(e)})
    
    if failed_items:
        return {"message": f"成功删除 {deleted_count} 个知识库", "failed": failed_items}
    
    return {"message": f"成功删除 {deleted_count} 个知识库"}


@router.post("/{kb_id}/upload")
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文档到知识库"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限
    if not _has_kb_write_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有上传权限")
    
    # 检查文件类型
    allowed_extensions = {'.pdf', '.docx', '.txt', '.md', '.csv', '.xlsx', '.xls'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型，支持的类型：{', '.join(allowed_extensions)}"
        )
    
    # 使用文件处理器保存文件
    file_processor = FileProcessor()
    
    try:
        logger.info(f"[UPLOAD] 开始上传文件到知识库 {kb_id}")
        
        # 保存文件到磁盘和数据库
        uploaded_file = await file_processor.save_uploaded_file(file, kb_id)
        logger.info(f"[UPLOAD] 文件已保存: {uploaded_file.id}, status: {uploaded_file.status}")
        
        # 保存到数据库
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)
        logger.info(f"[UPLOAD] 数据库记录已创建, file_id: {uploaded_file.id}")
        
        # 同步处理文件（解析和向量化）- 直接在当前线程执行，确保完成
        logger.info(f"[UPLOAD] 开始同步处理文件 {uploaded_file.id}")
        
        def run_async_process():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_process_file_async(uploaded_file.id))
            finally:
                loop.close()
        
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(run_async_process)
        future.result()  # 等待完成
        logger.info("[UPLOAD] 文件处理完成")
        
        return {
            "message": f"文件 {file.filename} 上传成功",
            "file_id": uploaded_file.id,
            "filename": uploaded_file.original_filename,
            "status": uploaded_file.status
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"文件上传失败：{str(e)}")


async def _process_file_async(file_id: int):
    """异步处理文件（解析和向量化）"""
    
    logger.info(f"[ASYNC] _process_file_async 被调用, file_id: {file_id}")
    
    # 创建新的数据库会话
    db = SessionLocal()
    try:
        file_processor = FileProcessor()
        
        # 获取文件记录
        uploaded_file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not uploaded_file:
            logger.warning(f"[ASYNC] 文件不存在: {file_id}")
            return
        
        logger.info(f"[ASYNC] 开始处理文件: {uploaded_file.original_filename}, status: {uploaded_file.status}")
        
        # 处理文件
        success = await file_processor.process_file(uploaded_file, db)
        
        # 刷新获取最新状态
        db.refresh(uploaded_file)
        logger.info(f"[ASYNC] 处理完成, success: {success}, final status: {uploaded_file.status}")
        
        if success:
            logger.info(f"[ASYNC] 文件处理成功: {uploaded_file.original_filename}")
        else:
            logger.warning(f"[ASYNC] 文件处理失败: {uploaded_file.original_filename}")
    except Exception as e:
        logger.error(f"[ASYNC] 文件处理异常: {e}", exc_info=True)
    finally:
        db.close()


@router.post("/{kb_id}/permissions", response_model=UserPermissionResponse)
def grant_permission(
    kb_id: int,
    permission: UserPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """授予用户知识库权限（仅所有者或管理员）"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限
    if knowledge_base.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="没有权限管理此知识库")
    
    # 检查用户是否存在
    target_user = db.query(User).filter(User.id == permission.user_id).first()
    if target_user is None:
        raise HTTPException(status_code=404, detail="目标用户不存在")
    
    # 检查权限是否已存在
    existing_permission = db.query(UserKnowledgePermission).filter(
        UserKnowledgePermission.user_id == permission.user_id,
        UserKnowledgePermission.knowledge_base_id == kb_id
    ).first()
    
    if existing_permission:
        raise HTTPException(status_code=400, detail="权限已存在")
    
    db_permission = UserKnowledgePermission(
        user_id=permission.user_id,
        knowledge_base_id=kb_id,
        can_read=permission.can_read,
        can_write=permission.can_write
    )
    
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    
    return db_permission


def _has_kb_access(user: User, knowledge_base: KnowledgeBase, db: Session) -> bool:
    """检查用户是否有知识库访问权限"""
    logger.info(f"[PERMISSION CHECK] 用户: {user.id}, 角色: {user.role}, 知识库: {knowledge_base.id}, 所有者: {knowledge_base.owner_id}")
    
    if user.role == "admin":
        logger.info("[PERMISSION CHECK] 管理员权限，直接返回True")
        return True
    
    if knowledge_base.owner_id == user.id:
        logger.info("[PERMISSION CHECK] 用户是所有者，返回True")
        return True
    
    if knowledge_base.is_public:
        logger.info("[PERMISSION CHECK] 知识库是公开的，返回True")
        return True
    
    permission = db.query(UserKnowledgePermission).filter(
        UserKnowledgePermission.user_id == user.id,
        UserKnowledgePermission.knowledge_base_id == knowledge_base.id,
        UserKnowledgePermission.can_read == True
    ).first()
    
    logger.info(f"[PERMISSION CHECK] 权限记录: {permission}")
    return permission is not None


def _has_kb_write_access(user: User, knowledge_base: KnowledgeBase, db: Session) -> bool:
    """检查用户是否有知识库写权限"""
    if user.role == "admin":
        return True
    
    if knowledge_base.owner_id == user.id:
        return True
    
    permission = db.query(UserKnowledgePermission).filter(
        UserKnowledgePermission.user_id == user.id,
        UserKnowledgePermission.knowledge_base_id == knowledge_base.id,
        UserKnowledgePermission.can_write == True
    ).first()
    
    return permission is not None


# 新增的文件上传和数据库连接相关端点

@router.post("/{kb_id}/files/upload")
async def upload_file_to_knowledge_base(
    kb_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文件到知识库（支持多种格式）"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限
    if not _has_kb_write_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有上传权限")
    
    # 检查知识库类型
    if knowledge_base.kb_type != "file":
        raise HTTPException(status_code=400, detail="此知识库类型不支持文件上传")
    
    # 检查文件类型
    allowed_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.csv', '.xlsx', '.xls'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型，支持的类型：{', '.join(allowed_extensions)}"
        )
    
    # 检查文件大小（限制为50MB）
    max_size = 50 * 1024 * 1024  # 50MB
    file.file.seek(0, 2)  # 移动到文件末尾
    file_size = file.file.tell()
    file.file.seek(0)  # 重置文件指针
    
    if file_size > max_size:
        raise HTTPException(status_code=400, detail="文件大小超过50MB限制")
    
    try:
        # 使用文件处理器保存文件
        
        uploaded_file = await file_processor.save_uploaded_file(file, kb_id)
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)
        
        # 同步处理文件（向量化）- 确保完成
        logger.info(f"[FILES UPLOAD] 开始同步处理文件 {uploaded_file.id}")
        
        def run_async_process():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(file_processor.process_file(uploaded_file, db))
                logger.info("[FILES UPLOAD] process_file 完成")
            except Exception as e:
                logger.error(f"[FILES UPLOAD] process_file 异常: {e}")
                import traceback
                traceback.print_exc()
            finally:
                loop.close()
        
        import concurrent.futures
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(run_async_process)
        
        try:
            future.result()  # 等待完成
            db.expire_all()  # 刷新session
            db.refresh(uploaded_file)
            logger.info(f"[FILES UPLOAD] 文件处理完成, status: {uploaded_file.status}")
        except Exception as e:
            logger.error(f"[FILES UPLOAD] 刷新文件状态异常: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
        
        return {
            "message": f"文件 {file.filename} 上传成功",
            "file_id": uploaded_file.id,
            "status": uploaded_file.status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/{kb_id}/files", response_model=List[UploadedFileResponse])
def get_knowledge_base_files(
    kb_id: int,
    db: Session = Depends(get_db)
):
    """获取知识库的文件列表（无需认证）"""
    logger.debug("[FILES LIST DEBUG] ====== 新请求 ======")
    logger.debug(f"[FILES LIST DEBUG] kb_id={kb_id}")
    
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        logger.warning(f"[FILES LIST DEBUG] 知识库 {kb_id} 不存在")
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 临时移除认证检查
    logger.debug("[FILES LIST DEBUG] 跳过权限检查（临时）")
    
    files = db.query(UploadedFile).filter(UploadedFile.knowledge_base_id == kb_id).all()
    logger.debug(f"[FILES LIST DEBUG] 返回 {len(files)} 个文件")
    return files


@router.delete("/{kb_id}/files/{file_id}")
def delete_knowledge_base_file(
    kb_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除知识库中的文件"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限
    if not _has_kb_write_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有删除权限")
    
    file = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.knowledge_base_id == kb_id
    ).first()
    
    if file is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 删除物理文件
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception as e:
        logger.error(f"删除物理文件失败: {e}")
    
    # 删除数据库记录
    db.delete(file)
    db.commit()
    
    return {"message": "文件删除成功"}


@router.post("/{kb_id}/database/connections", response_model=DatabaseConnectionResponse)
def create_database_connection(
    kb_id: int,
    db_connection: DatabaseConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为知识库创建数据库连接配置"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限
    if not _has_kb_write_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有配置权限")
    
    # 检查知识库类型
    if knowledge_base.kb_type != "db":
        raise HTTPException(status_code=400, detail="此知识库类型不支持数据库连接")
    
    # 检查是否已存在连接配置，数据库知识库只能添加一个数据源
    existing_connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.knowledge_base_id == kb_id
    ).first()
    
    if existing_connection:
        raise HTTPException(
            status_code=400, 
            detail="数据库知识库只能添加一个数据源，如需更换请先删除现有数据源"
        )
    
    try:
        # 测试数据库连接
        
        # 创建临时连接进行测试
        temp_connection = DatabaseConnection(
            **db_connection.dict(exclude={'knowledge_base_id'})
        )
        engine = database_service.create_connection(temp_connection)
        
        # 测试连接成功，创建正式记录
        db_connection_record = DatabaseConnection(
            **db_connection.dict()
        )
        
        db.add(db_connection_record)
        db.commit()
        db.refresh(db_connection_record)
        
        return db_connection_record
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"数据库连接测试失败: {str(e)}")


@router.get("/{kb_id}/database/connections", response_model=List[DatabaseConnectionResponse])
def get_database_connections(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库的数据库连接配置"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限
    if not _has_kb_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有访问权限")
    
    connections = db.query(DatabaseConnection).filter(
        DatabaseConnection.knowledge_base_id == kb_id
    ).all()
    
    return connections


@router.put("/{kb_id}/database/connections/{conn_id}", response_model=DatabaseConnectionResponse)
def update_database_connection(
    kb_id: int,
    conn_id: int,
    db_connection: DatabaseConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新数据库连接配置"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限
    if not _has_kb_write_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有配置权限")
    
    # 检查知识库类型
    if knowledge_base.kb_type != "db":
        raise HTTPException(status_code=400, detail="此知识库类型不支持数据库连接")
    
    # 查找现有连接
    db_conn = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == conn_id,
        DatabaseConnection.knowledge_base_id == kb_id
    ).first()
    
    if db_conn is None:
        raise HTTPException(status_code=404, detail="数据库连接不存在")
    
    try:
        # 测试新连接（如果提供了新密码）
        if db_connection.password:
            
            temp_connection = DatabaseConnection(
                **db_connection.dict(exclude={'knowledge_base_id'})
            )
            engine = database_service.create_connection(temp_connection)
        
        # 更新连接配置
        db_conn.name = db_connection.name
        db_conn.description = db_connection.description
        db_conn.db_type = db_connection.db_type
        db_conn.host = db_connection.host
        db_conn.port = db_connection.port
        db_conn.database = db_connection.database
        db_conn.username = db_connection.username
        if db_connection.password:
            db_conn.password = db_connection.password
        db_conn.schema_name = db_connection.schema_name
        db_conn.is_active = db_connection.is_active
        db_conn.pool_size = db_connection.pool_size
        db_conn.timeout = db_connection.timeout
        db_conn.max_rows = db_connection.max_rows
        
        db.commit()
        db.refresh(db_conn)
        
        return db_conn
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"更新失败: {str(e)}")


@router.delete("/{kb_id}/database/connections/{conn_id}")
def delete_database_connection(
    kb_id: int,
    conn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除数据库连接配置"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限
    if not _has_kb_write_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有删除权限")
    
    # 查找连接
    db_conn = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == conn_id,
        DatabaseConnection.knowledge_base_id == kb_id
    ).first()
    
    if db_conn is None:
        raise HTTPException(status_code=404, detail="数据库连接不存在")
    
    # 删除关联的表元数据
    db.query(ColumnMetadata).filter(
        ColumnMetadata.table_id.in_(
            db.query(TableMetadata.id).filter(TableMetadata.connection_id == conn_id)
        )
    ).delete(synchronize_session=False)
    db.query(TableMetadata).filter(TableMetadata.connection_id == conn_id).delete()
    
    # 删除连接
    db.delete(db_conn)
    db.commit()
    
    return {"message": "数据源删除成功"}


@router.get("/{kb_id}/database/sample")
def get_database_sample_data(
    kb_id: int,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据库表的样例数据"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    # 检查权限
    if not _has_kb_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有访问权限")
    
    # 获取数据库连接配置
    db_connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.knowledge_base_id == kb_id
    ).first()
    
    if db_connection is None:
        raise HTTPException(status_code=404, detail="数据库连接配置不存在")
    
    try:
        # 创建数据库连接
        engine = database_service.create_connection(db_connection)
        
        # 获取样例数据
        sample_data = database_service.get_sample_data(
            engine, 
            db_connection.table_name, 
            db_connection.schema_name, 
            limit
        )
        
        return {
            "table_name": db_connection.table_name,
            "schema_name": db_connection.schema_name,
            "sample_data": sample_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取样例数据失败: {str(e)}")


@router.get("/{kb_id}/database/connections/{conn_id}/tables")
def get_connection_tables(
    kb_id: int,
    conn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据库连接的所有表"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if not _has_kb_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有访问权限")
    
    db_connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == conn_id,
        DatabaseConnection.knowledge_base_id == kb_id
    ).first()
    
    if db_connection is None:
        raise HTTPException(status_code=404, detail="数据库连接不存在")
    
    try:
        tables = database_service.get_tables(db_connection)
        
        # 获取已保存的表元数据
        saved_tables = db.query(TableMetadata).filter(
            TableMetadata.connection_id == conn_id
        ).all()
        
        # 创建已保存表的映射
        saved_map = {t.table_name: t for t in saved_tables}
        
        # 为每个表添加ID，如果不存在则创建
        for table in tables:
            if table["table_name"] in saved_map:
                table["id"] = saved_map[table["table_name"]].id
                table["is_selected"] = saved_map[table["table_name"]].is_selected
            else:
                # 自动创建表元数据记录
                new_table_meta = TableMetadata(
                    connection_id=conn_id,
                    table_name=table["table_name"],
                    is_selected=True
                )
                db.add(new_table_meta)
                db.flush()
                table["id"] = new_table_meta.id
                table["is_selected"] = True
        
        db.commit()
        
        # 重新查询以获取最新数据
        saved_tables = db.query(TableMetadata).filter(
            TableMetadata.connection_id == conn_id
        ).all()
        saved_map = {t.table_name: t for t in saved_tables}
        for table in tables:
            if table["table_name"] in saved_map:
                table["id"] = saved_map[table["table_name"]].id
                table["is_selected"] = saved_map[table["table_name"]].is_selected
        
        return {"tables": tables}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取表列表失败: {str(e)}")


@router.post("/{kb_id}/database/connections/{conn_id}/tables")
def save_table_metadata(
    kb_id: int,
    conn_id: int,
    tables_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存表元数据（选择需要接入的表）"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if not _has_kb_write_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有写入权限")
    
    db_connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == conn_id,
        DatabaseConnection.knowledge_base_id == kb_id
    ).first()
    
    if db_connection is None:
        raise HTTPException(status_code=404, detail="数据库连接不存在")
    
    try:
        tables = tables_data.get("tables", [])
        
        # 删除旧的表元数据
        db.query(TableMetadata).filter(TableMetadata.connection_id == conn_id).delete()
        
        # 保存新的表元数据
        saved_tables = []
        for table in tables:
            table_meta = TableMetadata(
                connection_id=conn_id,
                table_name=table.get("table_name", ""),
                table_name_cn=table.get("table_name_cn"),
                description=table.get("description"),
                business_tags=table.get("business_tags"),
                is_selected=table.get("is_selected", True),
                recommended_questions=table.get("recommended_questions")
            )
            db.add(table_meta)
            db.flush()  # 获取ID
            saved_tables.append({
                "id": table_meta.id,
                "table_name": table_meta.table_name,
                "is_selected": table_meta.is_selected
            })
        
        db.commit()
        
        return {"message": "表元数据保存成功", "tables": saved_tables}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"保存失败: {str(e)}")


@router.get("/{kb_id}/database/connections/{conn_id}/metadata/{table_id}")
def get_table_metadata_config(
    kb_id: int,
    conn_id: int,
    table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取表和字段的元数据配置"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if not _has_kb_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有访问权限")
    
    table_meta = db.query(TableMetadata).filter(
        TableMetadata.id == table_id,
        TableMetadata.connection_id == conn_id
    ).first()
    
    if table_meta is None:
        raise HTTPException(status_code=404, detail="表元数据不存在")
    
    # 获取字段元数据
    columns = db.query(ColumnMetadata).filter(ColumnMetadata.table_id == table_id).all()
    
    # 获取指标定义
    metrics = db.query(MetricDefinition).filter(MetricDefinition.table_id == table_id).all()
    
    return {
        "table": {
            "id": table_meta.id,
            "table_name": table_meta.table_name,
            "table_name_cn": table_meta.table_name_cn,
            "description": table_meta.description,
            "business_tags": table_meta.business_tags,
            "recommended_questions": table_meta.recommended_questions
        },
        "columns": [
            {
                "id": col.id,
                "column_name": col.column_name,
                "column_type": col.column_type,
                "column_comment": col.column_comment,
                "synonyms": col.synonyms,
                "is_selected": col.is_selected
            }
            for col in columns
        ],
        "metrics": [
            {
                "id": m.id,
                "metric_name": m.metric_name,
                "metric_definition": m.metric_definition,
                "description": m.description
            }
            for m in metrics
        ]
    }


@router.post("/{kb_id}/database/connections/{conn_id}/metadata/{table_id}")
def save_table_metadata_config(
    kb_id: int,
    conn_id: int,
    table_id: int,
    metadata_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存表的字段和指标元数据配置"""
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if not _has_kb_write_access(current_user, knowledge_base, db):
        raise HTTPException(status_code=403, detail="没有写入权限")
    
    table_meta = db.query(TableMetadata).filter(
        TableMetadata.id == table_id,
        TableMetadata.connection_id == conn_id
    ).first()
    
    if table_meta is None:
        raise HTTPException(status_code=404, detail="表元数据不存在")
    
    try:
        # 更新表基本信息
        table_meta.table_name_cn = metadata_data.get("table_name_cn")
        table_meta.description = metadata_data.get("description")
        table_meta.business_tags = metadata_data.get("business_tags")
        
        # 保存字段元数据
        columns_data = metadata_data.get("columns", [])
        db.query(ColumnMetadata).filter(ColumnMetadata.table_id == table_id).delete()
        
        for col in columns_data:
            column_meta = ColumnMetadata(
                table_id=table_id,
                column_name=col.get("column_name", ""),
                column_type=col.get("column_type"),
                column_comment=col.get("column_comment"),
                synonyms=col.get("synonyms"),
                is_selected=col.get("is_selected", True)
            )
            db.add(column_meta)
        
        # 保存指标定义
        metrics_data = metadata_data.get("metrics", [])
        db.query(MetricDefinition).filter(MetricDefinition.table_id == table_id).delete()
        
        for metric in metrics_data:
            metric_def = MetricDefinition(
                table_id=table_id,
                metric_name=metric.get("metric_name", ""),
                metric_definition=metric.get("metric_definition", ""),
                description=metric.get("description")
            )
            db.add(metric_def)
        
        db.commit()
        
        return {"message": "元数据保存成功"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"保存失败: {str(e)}")