import time
import uuid
import logging
import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..models.cache import ConversationMessage
from ..models.embedding import EmbeddingModel
from ..core.database import SessionLocal
from .cache import CacheService
from .rag import RAGService

logger = logging.getLogger(__name__)


class VectorizationTask:
    """异步向量化任务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_service = CacheService(db)
    
    def run(self, batch_size: int = 100):
        """执行向量化任务"""
        logger.info("开始异步向量化任务...")
        
        pending_messages = self.cache_service.get_pending_vectorization(limit=batch_size)
        
        if not pending_messages:
            logger.info("没有待向量化的消息")
            return
        
        logger.info(f"找到 {len(pending_messages)} 条待向量化的消息")
        
        try:
            rag_service = RAGService(self.db)
            
            embedding_model = self.db.query(EmbeddingModel).filter(
                EmbeddingModel.is_default == True,
                EmbeddingModel.is_active == True
            ).first()
            
            if embedding_model:
                rag_service._init_embeddings_from_model(embedding_model)
                logger.info(f"使用默认embedding模型: {embedding_model.name}")
            else:
                rag_service._init_embeddings()
                logger.info("使用备用embedding模型")
            
            for msg in pending_messages:
                try:
                    self._vectorize_message(rag_service, msg)
                except Exception as e:
                    logger.error(f"向量化消息 {msg.message_id} 失败: {e}")
                    self.db.rollback()
                    continue
        
        except Exception as e:
            logger.error(f"向量化任务执行失败: {e}")
    
    def _vectorize_message(self, rag_service: RAGService, msg: ConversationMessage):
        """向量化单条消息"""
        question_vector = rag_service.embeddings.embed_query(msg.question_text)
        
        vector_id = str(uuid.uuid4())
        now = int(time.time())
        
        sql = text("""
            INSERT INTO llm_qa_vectors_pg (
                vector_id, question_vector, module_key, status, created_time,
                message_id, question_text, answer_text, quality_score, hit_count,
                embedding_model, expire_time
            ) VALUES (
                :vector_id, cast(:vector as vector), :module_key, 1, :created_time,
                :message_id, :question_text, :answer_text, 0.50, 0,
                :embedding_model, :expire_time
            )
        """)
        
        self.db.execute(sql, {
            "vector_id": vector_id,
            "vector": question_vector,
            "module_key": msg.module_key,
            "created_time": now,
            "message_id": msg.message_id,
            "question_text": msg.question_text,
            "answer_text": msg.answer_text,
            "embedding_model": msg.embedding_model or "default",
            "expire_time": now + (90 * 24 * 3600)
        })
        
        sql_metadata = text("""
            INSERT INTO conversation_vector_metadata (
                vector_id, message_id, question_hash, question_text, answer_text,
                module_key, embedding_model, vector_dimension, collection_name,
                quality_score, hit_count, status, expire_time
            ) VALUES (
                :vector_id, :message_id, :question_hash, :question_text, :answer_text,
                :module_key, :embedding_model, :vector_dimension, :collection_name,
                0.50, 0, 1, :expire_time
            )
        """)
        
        question_hash = CacheService.compute_question_hash(msg.question_text)
        
        # 获取向量维度
        vector_dimension = 1024
        if embedding_model and embedding_model.dimensions:
            vector_dimension = embedding_model.dimensions
        
        self.db.execute(sql_metadata, {
            "vector_id": vector_id,
            "message_id": msg.message_id,
            "question_hash": question_hash,
            "question_text": msg.question_text,
            "answer_text": msg.answer_text,
            "module_key": msg.module_key,
            "embedding_model": msg.embedding_model or "default",
            "vector_dimension": vector_dimension,
            "collection_name": "llm_qa_vectors_pg",
            "expire_time": now + (90 * 24 * 3600)
        })
        
        self.cache_service.mark_vectorized(msg.message_id)
        
        logger.info(f"消息 {msg.message_id} 向量化完成")


def start_vectorization_scheduler(interval_seconds: int = 30):
    """启动向量化调度器"""
    
    logger.info(f"启动向量化调度器，间隔 {interval_seconds} 秒")
    
    while True:
        try:
            db = SessionLocal()
            try:
                task = VectorizationTask(db)
                task.run()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"向量化调度器错误: {e}")
        
        time.sleep(interval_seconds)
