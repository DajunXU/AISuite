import json
from typing import Dict, Any, Tuple

from ..core.logger import get_logger

logger = get_logger("intent_classifier")


class IntentClassifier:
    """意图分类器 - 识别用户问题需要调用向量化知识库还是数据库"""
    
    def __init__(self):
        pass
    
    async def classify_intent(self, question: str, knowledge_base_type: str) -> Tuple[str, Dict[str, Any]]:
        """
        分类用户问题意图
        
        Args:
            question: 用户问题
            knowledge_base_type: 知识库类型 ("file" 或 "db")
            
        Returns:
            Tuple[str, Dict]: (意图类型, 额外信息)
        """
        
        # 如果知识库类型是数据库，优先使用数据库查询
        if knowledge_base_type == "db":
            return "database_query", {"reason": "知识库类型为数据库连接"}
        
        # 如果知识库类型是文件，需要判断问题类型
        elif knowledge_base_type == "file":
            # 使用规则和模型结合的方式判断意图
            intent = await self._analyze_question_intent(question)
            return intent
        
        else:
            # 默认使用向量化查询
            return "vector_search", {"reason": "默认处理方式"}
    
    async def _analyze_question_intent(self, question: str) -> Tuple[str, Dict[str, Any]]:
        """分析问题意图"""
        
        # 规则匹配：检测明显的数据库查询关键词
        db_keywords = ["查询", "统计", "数量", "总数", "平均", "最大", "最小", 
                      "列表", "显示", "查找", "搜索", "筛选", "过滤", "排序"]
        
        question_lower = question.lower()
        
        # 检查是否包含数据库查询关键词
        db_keyword_count = sum(1 for keyword in db_keywords if keyword in question_lower)
        
        if db_keyword_count >= 2:
            return "database_query", {"reason": "检测到数据库查询关键词", "keyword_count": db_keyword_count}
        
        # 使用大模型进行更精确的意图分类
        return await self._model_based_classification(question)
    
    async def _model_based_classification(self, question: str) -> Tuple[str, Dict[str, Any]]:
        """基于大模型的意图分类"""
        
        prompt = f"""
        请分析以下用户问题的意图，判断它更适合使用哪种方式处理：
        
        问题："{question}"
        
        处理方式选项：
        1. vector_search - 适合基于文档内容的语义搜索，如概念解释、知识问答、内容理解等
        2. database_query - 适合需要精确数据查询、统计计算、数据筛选等操作
        
        请根据以下标准判断：
        - 如果问题涉及具体的数据查询、统计计算、数值比较，选择 database_query
        - 如果问题涉及概念理解、知识解释、内容分析，选择 vector_search
        - 如果问题模糊不清，默认选择 vector_search
        
        请以JSON格式返回结果，包含：
        {{
            "intent": "vector_search" 或 "database_query",
            "confidence": 0.0-1.0之间的置信度,
            "reason": "判断理由"
        }}
        """
        
        try:
            response = await self.rag_service.generate_response(prompt, is_intent_classification=True)
            
            # 尝试解析JSON响应
            try:
                result = json.loads(response)
                intent = result.get("intent", "vector_search")
                confidence = result.get("confidence", 0.5)
                reason = result.get("reason", "模型分析结果")
                
                return intent, {"confidence": confidence, "reason": reason}
                
            except json.JSONDecodeError:
                # 如果JSON解析失败，使用简单的文本分析
                if "database" in response.lower() or "查询" in response:
                    return "database_query", {"confidence": 0.6, "reason": "模型响应包含数据库关键词"}
                else:
                    return "vector_search", {"confidence": 0.6, "reason": "模型响应默认向量搜索"}
                    
        except Exception as e:
            logger.error(f"意图分类模型调用失败: {e}")
            # 模型调用失败时使用规则匹配
            return self._rule_based_fallback(question)
    
    def _rule_based_fallback(self, question: str) -> Tuple[str, Dict[str, Any]]:
        """规则匹配回退方案"""
        
        question_lower = question.lower()
        
        # 数据库查询特征
        db_patterns = [
            "有多少", "总数", "统计", "查询", "显示所有", "列出",
            "最大值", "最小值", "平均值", "求和", "计数",
            "where", "select", "from", "order by", "group by"
        ]
        
        # 向量搜索特征
        vector_patterns = [
            "什么是", "解释", "说明", "介绍", "如何", "为什么",
            "概念", "定义", "含义", "理解", "分析"
        ]
        
        db_score = sum(1 for pattern in db_patterns if pattern in question_lower)
        vector_score = sum(1 for pattern in vector_patterns if pattern in question_lower)
        
        if db_score > vector_score:
            return "database_query", {"confidence": 0.7, "reason": "规则匹配数据库查询特征"}
        elif vector_score > db_score:
            return "vector_search", {"confidence": 0.7, "reason": "规则匹配向量搜索特征"}
        else:
            return "vector_search", {"confidence": 0.5, "reason": "规则匹配平局，默认向量搜索"}


# 全局意图分类器实例
intent_classifier = IntentClassifier()