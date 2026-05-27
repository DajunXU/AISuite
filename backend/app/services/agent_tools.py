"""
Agent 工具实现 - LangChain 标准格式
使用 @tool 装饰器定义工具
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from langchain_core.tools import tool

from ..services.rag import RAGService
from ..services.sql_agent import create_sql_agent_from_kb
from ..core.database import get_db

from ..core.logger import get_logger

logger = get_logger("agent_tools")


class RAGToolOutput:
    """RAG 工具输出"""
    def __init__(self, result: str, sources: List[str] = None):
        self.result = result
        self.sources = sources or []
    
    def __str__(self) -> str:
        return self.result


@tool
def knowledge_base_qa(query: str, kb_ids: List[int] = None) -> str:
    """
    知识库问答工具。用于回答基于知识库内容的问题。
    
    Args:
        query: 用户问题
        kb_ids: 知识库 ID 列表
    
    Returns:
        知识库回答结果和来源
    """
    logger.info(f"[knowledge_base_qa] 查询: {query[:50]}..., kb_ids: {kb_ids}")
    
    try:
        db = next(get_db())
        
        try:
            rag_service = RAGService(db)
            
            answer, sources = rag_service.generate_answer_sync(
                question=query,
                kb_ids=kb_ids or []
            )
            
            if sources:
                source_text = "\n\n来源:\n" + "\n".join([f"- {s}" for s in sources])
                return answer + source_text
            
            return answer or "未找到相关信息"
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[knowledge_base_qa] 执行失败: {e}")
        return f"知识库查询失败: {str(e)}"


@tool
def database_query(query: str, kb_id: int = None) -> str:
    """
    数据库查询工具。用于执行 SQL 查询业务数据库。
    
    Args:
        query: 用户问题或查询意图
        kb_id: 数据库知识库 ID
    
    Returns:
        查询结果
    """
    logger.info(f"[database_query] 查询: {query[:50]}..., kb_id: {kb_id}")
    
    if not kb_id:
        return "未指定数据库知识库 ID"
    
    try:
        db = next(get_db())
        
        try:
            sql_agent = create_sql_agent_from_kb(kb_id, db)
            
            result = sql_agent.query(query)
            sql_agent.close()
            
            if result.get("success"):
                return result.get("answer", "查询完成但无结果")
            else:
                return f"查询失败: {result.get('error', '未知错误')}"
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[database_query] 执行失败: {e}")
        return f"数据库查询失败: {str(e)}"


@tool
def plain_chat(query: str) -> str:
    """
    直接对话工具。用于不需要外部数据的通用对话。
    
    Args:
        query: 用户消息
    
    Returns:
        AI 回复
    """
    logger.info(f"[plain_chat] 对话: {query[:50]}...")
    
    return "请提供更多上下文信息以便我更好地回答您的问题。"


class RAGTool:
    """知识库问答工具（旧版兼容）"""
    
    name = "knowledge_base_qa"
    description = "回答基于知识库内容的问题"
    
    def __init__(self, kb_ids: List[int], db: Session):
        self.kb_ids = kb_ids
        self.db = db
    
    async def execute(self, tool_input) -> RAGToolOutput:
        """执行知识库问答"""
        
        try:
            rag_service = RAGService(self.db)
            
            answer, sources = await rag_service.generate_answer(
                question=tool_input.query,
                kb_ids=self.kb_ids
            )
            
            return RAGToolOutput(
                result=answer,
                sources=sources or []
            )
            
        except Exception as e:
            logger.error(f"[RAGTool] 执行失败: {e}")
            return RAGToolOutput(
                result=f"知识库查询失败: {str(e)}",
                sources=[]
            )


class SQLTool:
    """SQL 数据库查询工具（旧版兼容）"""
    
    name = "database_query"
    description = "执行 SQL 查询业务数据库"
    
    def __init__(self, kb_id: int, db: Session):
        self.kb_id = kb_id
        self.db = db
    
    async def execute(self, tool_input) -> RAGToolOutput:
        """执行 SQL 查询"""
        
        try:
            sql_agent = create_sql_agent_from_kb(self.kb_id, self.db)
            
            result = sql_agent.query(tool_input.query)
            
            return RAGToolOutput(
                result=str(result),
                sources=[]
            )
            
        except Exception as e:
            logger.error(f"[SQLTool] 执行失败: {e}")
            return RAGToolOutput(
                result=f"数据库查询失败: {str(e)}",
                sources=[]
            )


def create_rag_tools(kb_ids: List[int], db: Session) -> List:
    """
    创建 RAG 工具列表
    
    Args:
        kb_ids: 知识库 ID 列表
        db: 数据库会话
    
    Returns:
        LangChain 工具列表
    """
    from langchain_core.tools import tool
    
    tools = []
    
    for kb_id in kb_ids:
        
        def make_rag_tool(kb_id: int):
            @tool
            def rag_tool(query: str) -> str:
                """
                知识库问答工具。用于回答基于知识库内容的问题。
                """
                import asyncio
                
                async def _run():
                    db = next(get_db())
                    try:
                        rag_service = RAGService(db)
                        answer, sources = await rag_service.generate_answer(
                            question=query,
                            kb_ids=[kb_id]
                        )
                        if sources:
                            source_text = "\n\n来源:\n" + "\n".join([f"- {s}" for s in sources])
                            return answer + source_text
                        return answer or "未找到相关信息"
                    finally:
                        db.close()
                
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            future = pool.submit(asyncio.run, _run())
                            return future.result()
                    else:
                        return asyncio.run(_run())
                except Exception as e:
                    return f"知识库查询失败: {str(e)}"
            
            rag_tool.name = f"knowledge_base_qa_{kb_id}"
            return rag_tool
        
        tools.append(make_rag_tool(kb_id))
    
    return tools


def create_sql_tools(kb_id: int, db: Session) -> List:
    """
    创建 SQL 查询工具
    
    Args:
        kb_id: 数据库知识库 ID
        db: 数据库会话
    
    Returns:
        LangChain 工具列表
    """
    @tool
    def sql_tool(query: str) -> str:
        """
        数据库查询工具。用于执行 SQL 查询业务数据库。
        """
        return database_query.invoke({"query": query, "kb_id": kb_id})
    
    sql_tool.name = f"database_query_{kb_id}"
    sql_tool.description = f"查询数据库知识库 ID {kb_id} 中的数据"
    
    return [sql_tool]


def create_chat_tool(llm: Any) -> Any:
    """
    创建对话工具
    
    Args:
        llm: LangChain LLM 实例
    
    Returns:
        LangChain 工具
    """
    return plain_chat


def get_tools_for_context(
    db: Session,
    llm: Any = None,
    text_kb_id: int = None,
    db_kb_id: int = None
) -> List:
    """
    根据上下文获取可用的工具列表
    
    Args:
        db: 数据库会话
        llm: LLM 实例
        text_kb_id: 文本知识库 ID
        db_kb_id: 数据库知识库 ID
    
    Returns:
        LangChain 工具列表
    """
    tools = []
    
    if text_kb_id:
        tools.extend(create_rag_tools(kb_ids=[text_kb_id], db=db))
    
    if db_kb_id:
        tools.extend(create_sql_tools(kb_id=db_kb_id, db=db))
    
    if not tools:
        tools.append(plain_chat)
    
    return tools
