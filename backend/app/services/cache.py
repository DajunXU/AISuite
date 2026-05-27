import hashlib
import uuid
import time
import json
import logging
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from ..models.cache import ConversationMeta, ConversationMessage, ConversationVectorMetadata
from ..models.embedding import EmbeddingModel

logger = logging.getLogger(__name__)


class CacheService:
    """缓存服务 - 实现精确匹配 + 向量匹配"""
    
    SIMILARITY_THRESHOLD = 0.85
    
    def __init__(self, db: Session):
        self.db = db
        self.vector_dimension = self._get_default_embedding_dimensions()
    
    def _get_default_embedding_dimensions(self) -> int:
        """从数据库获取默认向量模型的维度"""
        try:
            default_model = self.db.query(EmbeddingModel).filter(
                EmbeddingModel.is_default == True,
                EmbeddingModel.is_active == True
            ).first()
            
            if default_model and default_model.dimensions:
                logger.info(f"[CacheService] 从数据库获取默认向量维度: {default_model.dimensions}")
                return default_model.dimensions
        except Exception as e:
            logger.warning(f"[CacheService] 获取默认向量维度失败: {e}")
        
        return 1024  # 默认使用 1024
    
    @staticmethod
    def compute_question_hash(question_text: str) -> str:
        """计算问题的 SHA256 哈希值"""
        return hashlib.sha256(question_text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_uuid() -> str:
        """生成 UUID"""
        return str(uuid.uuid4())
    
    def get_or_create_conversation(
        self,
        conversation_id: Optional[str],
        user_key: str,
        module_key: str = "chat",
        source_system: str = "web",
        title: Optional[str] = None
    ) -> Tuple[ConversationMeta, bool]:
        """获取或创建会话"""
        is_new = False
        
        if conversation_id:
            meta = self.db.query(ConversationMeta).filter(
                ConversationMeta.conversation_id == conversation_id
            ).first()
            
            if not meta:
                meta = ConversationMeta(
                    conversation_id=conversation_id,
                    user_key=user_key,
                    module_key=module_key,
                    source_system=source_system,
                    title=title or "新对话",
                    message_count=0,
                    total_tokens=0
                )
                self.db.add(meta)
                self.db.commit()
                self.db.refresh(meta)
                is_new = True
        else:
            new_conv_id = self.generate_uuid()
            meta = ConversationMeta(
                conversation_id=new_conv_id,
                user_key=user_key,
                module_key=module_key,
                source_system=source_system,
                title=title or "新对话",
                message_count=0,
                total_tokens=0
            )
            self.db.add(meta)
            self.db.commit()
            self.db.refresh(meta)
            is_new = True
        
        return meta, is_new
    
    def exact_match_lookup(
        self,
        question_text: str,
        module_key: str = "chat"
    ) -> Optional[ConversationMessage]:
        """精确匹配查询"""
        question_hash = self.compute_question_hash(question_text)
        
        msg = self.db.query(ConversationMessage).filter(
            ConversationMessage.question_hash == question_hash,
            ConversationMessage.module_key == module_key,
            ConversationMessage.status == 1
        ).order_by(ConversationMessage.created_time.desc()).first()
        
        if msg:
            logger.info(f"[Cache] 精确命中: {question_text[:30]}...")
        else:
            logger.info(f"[Cache] 精确未命中: {question_text[:30]}...")
        
        return msg
    
    def vector_similarity_search(
        self,
        question_vector: List[float],
        module_key: str = "chat",
        top_k: int = 5
    ) -> Optional[Tuple[Dict[str, Any], float]]:
        """向量相似度搜索"""
        try:
            from sqlalchemy import cast
            
            sql = text("""
                SELECT 
                    v.message_id,
                    v.question_text,
                    v.answer_text,
                    v.quality_score,
                    v.hit_count,
                    1 - (v.question_vector <=> cast(:vector as vector)) as similarity
                FROM llm_qa_vectors_pg v
                WHERE v.module_key = :module_key
                AND v.status = 1
                ORDER BY v.question_vector <=> cast(:vector as vector)
                LIMIT :top_k
            """)
            
            result = self.db.execute(sql, {
                "vector": question_vector,
                "module_key": module_key,
                "top_k": top_k
            })
            
            rows = result.fetchall()
            
            if not rows:
                logger.info(f"[Cache] 向量搜索无结果")
                return None
            
            best_match = rows[0]
            similarity = float(best_match[5])
            
            logger.info(f"[Cache] 向量匹配最佳相似度: {similarity:.3f}")
            
            if similarity >= self.SIMILARITY_THRESHOLD:
                return {
                    "message_id": best_match[0],
                    "question_text": best_match[1],
                    "answer_text": best_match[2],
                    "quality_score": float(best_match[3]) if best_match[3] else 0,
                    "hit_count": best_match[4]
                }, similarity
            
            return None
            
        except Exception as e:
            logger.error(f"[Cache] 向量搜索失败: {e}")
            return None
    
    def update_vector_hit_count(self, message_id: str):
        """更新向量命中次数"""
        try:
            sql = text("""
                UPDATE llm_qa_vectors_pg 
                SET hit_count = hit_count + 1, 
                    last_hit_time = NOW()
                WHERE message_id = :message_id
            """)
            self.db.execute(sql, {"message_id": message_id})
            self.db.commit()
        except Exception as e:
            logger.error(f"更新向量命中次数失败: {e}")
    
    def save_message(
        self,
        conversation_id: str,
        user_key: str,
        question_text: str,
        answer_text: str,
        model_name: str,
        module_key: str = "chat",
        source_system: str = "web",
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_duration: int = 0,
        answer_source: int = 0,
        similarity_score: Optional[float] = None,
        source_message_id: Optional[str] = None,
        tool_calls: Optional[List] = None,
        attachments: Optional[List] = None,
        messages_json: Optional[List] = None
    ) -> ConversationMessage:
        """保存消息"""
        question_hash = self.compute_question_hash(question_text)
        
        sequence_num = self.db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id
        ).count() + 1
        
        message_id = self.generate_uuid()
        
        msg = ConversationMessage(
            message_id=message_id,
            conversation_id=conversation_id,
            user_key=user_key,
            module_key=module_key,
            source_system=source_system,
            question_text=question_text,
            question_hash=question_hash,
            answer_text=answer_text,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            total_duration=total_duration,
            answer_source=answer_source,
            similarity_score=similarity_score,
            source_message_id=source_message_id,
            tool_calls=json.dumps(tool_calls) if tool_calls else None,
            attachments=json.dumps(attachments) if attachments else None,
            messages_json=json.dumps(messages_json) if messages_json else None,
            is_vectorized=0,
            status=1,
            sequence_num=sequence_num
        )
        
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        
        self._update_conversation_stats(
            conversation_id=conversation_id,
            total_tokens=prompt_tokens + completion_tokens,
            model_name=model_name
        )
        
        logger.info(f"[Cache] 消息保存成功: {message_id}, answer_source={answer_source}")
        
        return msg
    
    def _update_conversation_stats(
        self,
        conversation_id: str,
        total_tokens: int,
        model_name: str
    ):
        """更新会话统计"""
        try:
            meta = self.db.query(ConversationMeta).filter(
                ConversationMeta.conversation_id == conversation_id
            ).first()
            
            if meta:
                meta.message_count += 1
                meta.total_tokens += total_tokens
                meta.last_message_time = datetime.now()
                
                if not meta.first_message_at:
                    meta.first_message_at = datetime.now()
                
                meta.model_name = model_name
                
                if model_name.startswith("gpt") or model_name.startswith("GPT"):
                    meta.model_provider = "openai"
                elif model_name.startswith("claude"):
                    meta.model_provider = "anthropic"
                elif model_name.startswith("glm"):
                    meta.model_provider = "zhipu"
                elif model_name.startswith("qwen"):
                    meta.model_provider = "alibaba"
                else:
                    meta.model_provider = "unknown"
                
                self.db.commit()
                
        except Exception as e:
            logger.error(f"更新会话统计失败: {e}")
    
    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[ConversationMessage]:
        """获取会话历史"""
        messages = self.db.query(ConversationMessage).filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.status == 1
        ).order_by(ConversationMessage.sequence_num.asc()).limit(limit).all()
        
        return messages
    
    def submit_feedback(
        self,
        message_id: str,
        feedback: int,
        remark: Optional[str] = None
    ) -> bool:
        """提交用户反馈"""
        msg = self.db.query(ConversationMessage).filter(
            ConversationMessage.message_id == message_id
        ).first()
        
        if not msg:
            return False
        
        if msg.user_feedback is not None:
            logger.info(f"消息 {message_id} 已反馈过，跳过")
            return False
        
        msg.user_feedback = feedback
        msg.feedback_remark = remark
        self.db.commit()
        
        self._update_quality_score(message_id, feedback)
        
        return True
    
    def _update_quality_score(self, message_id: str, feedback: int):
        """更新质量分"""
        try:
            delta = 0.2 if feedback == 1 else -0.3
            
            sql = text("""
                UPDATE llm_qa_vectors_pg 
                SET quality_score = LEAST(1.0, GREATEST(0.0, quality_score + :delta))
                WHERE message_id = :message_id
            """)
            self.db.execute(sql, {"delta": delta, "message_id": message_id})
            self.db.commit()
            
        except Exception as e:
            logger.error(f"更新质量分失败: {e}")
    
    def get_conversation_by_id(self, conversation_id: str) -> Optional[ConversationMeta]:
        """根据 ID 获取会话"""
        return self.db.query(ConversationMeta).filter(
            ConversationMeta.conversation_id == conversation_id
        ).first()
    
    def get_pending_vectorization(self, limit: int = 100) -> List[ConversationMessage]:
        """获取待向量化的消息"""
        return self.db.query(ConversationMessage).filter(
            ConversationMessage.is_vectorized == 0,
            ConversationMessage.answer_source == 0,
            ConversationMessage.status == 1
        ).limit(limit).all()
    
    def mark_vectorized(self, message_id: str):
        """标记为已向量化"""
        msg = self.db.query(ConversationMessage).filter(
            ConversationMessage.message_id == message_id
        ).first()
        
        if msg:
            msg.is_vectorized = 1
            msg.vectorized_at = datetime.now()
            self.db.commit()
