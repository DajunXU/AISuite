from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from ...core.database import get_db
from ...core.logger import get_logger
from ...models.knowledge import KnowledgeBase, UploadedFile, DocumentChunk

logger = get_logger("kb_stats")
router = APIRouter()


class FileStatsResponse(BaseModel):
    file_id: int
    file_name: str
    total_chunks: int
    vector_count: int
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class KnowledgeBaseStatsResponse(BaseModel):
    kb_id: int
    kb_name: str
    kb_type: str
    total_files: int
    total_chunks: int
    total_vectors: int
    processed_files: int
    error_files: int
    files: List[FileStatsResponse]
    
    class Config:
        from_attributes = True


@router.get("/{kb_id}/stats", response_model=KnowledgeBaseStatsResponse)
def get_knowledge_base_stats(
    kb_id: int,
    db: Session = Depends(get_db)
):
    """获取知识库统计信息（包含向量数量）"""
    
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    
    if knowledge_base.kb_type == "file":
        files = db.query(UploadedFile).filter(UploadedFile.knowledge_base_id == kb_id).all()
        
        total_chunks = db.query(DocumentChunk).filter(
            DocumentChunk.knowledge_base_id == kb_id
        ).count()
        
        total_vectors = db.query(DocumentChunk).filter(
            DocumentChunk.knowledge_base_id == kb_id,
            DocumentChunk.embedding.isnot(None)
        ).count()
        
        processed_files = 0
        error_files = 0
        
        for file in files:
            if file.status == "processed":
                processed_files += 1
            elif file.status == "error":
                error_files += 1
        
        avg_chunks = total_chunks // len(files) if files else 0
        avg_vectors = total_vectors // len(files) if files else 0
        
        file_stats = []
        for file in files:
            file_stats.append(FileStatsResponse(
                file_id=file.id,
                file_name=file.original_filename,
                total_chunks=avg_chunks,
                vector_count=avg_vectors,
                processed_at=file.vectorized_at
            ))
        
        return KnowledgeBaseStatsResponse(
            kb_id=kb_id,
            kb_name=knowledge_base.name,
            kb_type=knowledge_base.kb_type,
            total_files=len(files),
            total_chunks=total_chunks,
            total_vectors=total_vectors,
            processed_files=processed_files,
            error_files=error_files,
            files=file_stats
        )
    else:
        return KnowledgeBaseStatsResponse(
            kb_id=kb_id,
            kb_name=knowledge_base.name,
            kb_type=knowledge_base.kb_type,
            total_files=0,
            total_chunks=0,
            total_vectors=0,
            processed_files=0,
            error_files=0,
            files=[]
        )
