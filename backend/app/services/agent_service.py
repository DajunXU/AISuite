"""
简化版 Agent 服务 - 集成 RAG 和 SQL 功能
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from ..core.logger import get_logger
from .rag import RAGService
from .sql_agent import create_sql_agent_from_kb

logger = get_logger("agent_service")


class AgentService:
    """简化版 Agent 服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process(
        self,
        question: str,
        user_id: int,
        text_kb_id: Optional[int] = None,
        db_kb_id: Optional[int] = None,
        model=None,
        api_key: str = None,
        base_url: str = None,
        provider: str = None
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        处理用户问题 - Agent 模式
        返回: (answer, sources, metadata)
        """
        logger.info(f"[AgentService] 处理问题: {question[:50]}...")
        
        answer = None
        sources = []
        metadata = {
            "tools_used": [],
            "answer_source": 0
        }
        
        # 构建工具列表
        tools_to_try = []
        
        if text_kb_id:
            tools_to_try.append({
                "type": "rag",
                "kb_id": text_kb_id,
                "name": "知识库问答"
            })
        
        if db_kb_id:
            tools_to_try.append({
                "type": "sql",
                "kb_id": db_kb_id,
                "name": "数据库查询"
            })
        
        # 如果没有任何工具，使用纯 LLM
        if not tools_to_try:
            logger.info("[AgentService] 无知识库，使用纯对话")
            return await self._plain_chat(
                question, model, api_key, base_url, provider
            )
        
        # 尝试各个工具
        for tool_info in tools_to_try:
            tool_type = tool_info["type"]
            
            try:
                if tool_type == "rag":
                    result, src = await self._call_rag(
                        question, user_id, tool_info["kb_id"],
                        model, api_key, base_url, provider
                    )
                    if result and len(result) > 10:
                        answer = result
                        sources = src or []
                        metadata["tools_used"].append("rag")
                        metadata["answer_source"] = 0
                        logger.info(f"[AgentService] RAG 工具返回结果")
                        break
                
                elif tool_type == "sql":
                    result = await self._call_sql(
                        question, tool_info["kb_id"]
                    )
                    if result:
                        answer = result
                        metadata["tools_used"].append("sql")
                        metadata["answer_source"] = 0
                        logger.info(f"[AgentService] SQL 工具返回结果")
                        break
                        
            except Exception as e:
                logger.error(f"[AgentService] 工具 {tool_type} 调用失败: {e}")
                continue
        
        # 如果没有工具返回结果，使用纯对话
        if not answer:
            logger.info("[AgentService] 工具未返回结果，使用纯对话")
            answer, _, meta = await self._plain_chat(
                question, model, api_key, base_url, provider
            )
            metadata["tools_used"] = meta.get("tools_used", [])
        
        return answer, sources, metadata
    
    async def _call_rag(
        self,
        question: str,
        user_id: int,
        kb_id: int,
        model,
        api_key: str,
        base_url: str,
        provider: str
    ) -> Tuple[str, List[str]]:
        """调用 RAG 服务"""
        rag_service = RAGService(self.db)
        
        answer, sources = await rag_service.generate_answer(
            question=question,
            user_id=user_id,
            text_kb_id=kb_id,
            api_key=api_key,
            base_url=base_url,
            provider=provider,
            model=model
        )
        
        return answer, sources
    
    async def _call_sql(self, question: str, kb_id: int) -> str:
        """调用 SQL Agent"""
        try:
            sql_agent = create_sql_agent_from_kb(kb_id, self.db)
            result = sql_agent.query(question)
            sql_agent.close()
            
            if result.get("success"):
                return result.get("answer", "")
            else:
                logger.warning(f"[AgentService] SQL 查询失败: {result.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"[AgentService] SQL 调用异常: {e}")
            return None
    
    async def _plain_chat(
        self,
        question: str,
        model,
        api_key: str,
        base_url: str,
        provider: str
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """纯对话"""
        
        # 如果没有有效的模型配置，返回错误
        if not model or not api_key:
            logger.error("[AgentService] 纯对话模式需要有效的模型和API密钥")
            return "抱歉，无法连接到语言模型。请检查模型配置。", [], {"tools_used": [], "error": "no_model_config"}
        
        # 调试信息
        logger.info(f"[AgentService] _plain_chat - model: {model}, api_key: {api_key[:10] if api_key else None}..., base_url: {base_url}")
        
        llm = ChatOpenAI(
            model=model.name if hasattr(model, 'name') else str(model),
            api_key=api_key,
            base_url=base_url or "https://open.bigmodel.cn/api/paas/v4/",
            streaming=False
        )
        
        # 正确格式：agenerate 需要 [[message1, message2, ...]]
        messages = [[HumanMessage(content=question)]]
        logger.info(f"[AgentService] LLM initialized, calling with question: {question[:20]}...")
        response = await llm.agenerate(messages=messages)
        answer = response.generations[0][0].text
        
        return answer, [], {"tools_used": ["llm"]}
