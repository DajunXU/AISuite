"""
LangChain Agent 核心模块
采用标准 LangChain 架构，支持多种 Agent 类型和动态工具加载
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
import json
import uuid

from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .agent_tools import create_rag_tools, create_sql_tools, create_chat_tool

from ..core.logger import get_logger
from ..core.config import settings

logger = get_logger("agent")


class AgentType(str, Enum):
    """支持的 Agent 类型"""
    CONVERSATIONAL_REACT_DESCRIPTION = "conversational-react-description"
    REACT_DOCSTORE = "react-docstore"
    OPENAI_FUNCTIONS = "openai-functions"
    STRUCTURED_CHAT_ZERO_SHOT_REACT = "structured-chat-zero-shot-react"


class AgentResponse(BaseModel):
    """Agent 响应"""
    answer: str
    sources: Optional[List[str]] = None
    tools_used: List[str] = []
    tool_calls: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = Field(default_factory=dict)
    conversation_id: Optional[str] = None
    user_id: Optional[int] = None


class ToolInput(BaseModel):
    """工具输入基类"""
    query: str


class ToolOutput(BaseModel):
    """工具输出基类"""
    result: Any
    sources: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class ToolRegistry:
    """
    工具注册中心
    负责工具的注册、获取和列表
    """
    _tools: Dict[str, Callable] = {}
    _tool_instances: Dict[str, Any] = {}
    
    @classmethod
    def register(cls, name: str, tool_func: Callable):
        """注册工具函数"""
        cls._tools[name] = tool_func
        logger.info(f"[ToolRegistry] 注册工具: {name}")
    
    @classmethod
    def register_instance(cls, name: str, instance: Any):
        """注册工具实例"""
        cls._tool_instances[name] = instance
        logger.info(f"[ToolRegistry] 注册工具实例: {name}")
    
    @classmethod
    def get_tool(cls, name: str) -> Optional[Callable]:
        """获取工具函数"""
        return cls._tools.get(name)
    
    @classmethod
    def get_instance(cls, name: str) -> Optional[Any]:
        """获取工具实例"""
        return cls._tool_instances.get(name)
    
    @classmethod
    def list_tools(cls) -> List[str]:
        """列出所有已注册工具"""
        return list(cls._tools.keys())
    
    @classmethod
    def clear(cls):
        """清空注册表"""
        cls._tools.clear()
        cls._tool_instances.clear()


class BaseLangChainTool(ABC):
    """
    基础工具类 - 封装自定义工具为 LangChain 工具
    用于兼容现有的工具实现
    """
    
    name: str = "base_tool"
    description: str = "基础工具"
    
    @abstractmethod
    async def execute(self, query: str) -> str:
        """执行工具，返回字符串结果"""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """获取 LangChain 工具 schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "用户问题或查询内容"
                    }
                },
                "required": ["query"]
            }
        }
    
    def to_langchain_tool(self) -> BaseTool:
        """转换为 LangChain BaseTool"""
        from langchain_core.tools import tool
        
        tool_instance = self
        
        @tool(tool_instance.name, description=tool_instance.description)
        async def langchain_wrapper(query: str) -> str:
            """LangChain 工具包装器"""
            try:
                result = await tool_instance.execute(query)
                return result
            except Exception as e:
                logger.error(f"[{tool_instance.name}] 执行失败: {e}")
                return f"工具执行失败: {str(e)}"
        
        return langchain_wrapper


class UnifiedAgent:
    """
    统一 Agent 核心类
    使用 LangChain Agent 架构，支持多种 Agent 类型
    """
    
    def __init__(
        self,
        llm: Any,
        tools: List[BaseTool],
        agent_type: AgentType = AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        conversation_id: str = None,
        user_id: int = None,
        system_prompt: str = None
    ):
        self.llm = llm
        self.tools = tools
        self.agent_type = agent_type
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.user_id = user_id
        self.system_prompt = system_prompt or self._default_system_prompt()
        
        self._agent_executor = None
        self._init_agent_executor()
        
        logger.info(
            f"[UnifiedAgent] 初始化, Agent类型: {agent_type}, "
            f"工具数: {len(tools)}, conversation_id: {self.conversation_id}"
        )
    
    def _default_system_prompt(self) -> str:
        """默认系统提示词"""
        tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.description}"
            for tool in self.tools
        ])
        
        return f"""你是一个智能助手，可以使用多种工具来帮助用户解决问题。

可用工具:
{tool_descriptions}

请根据用户问题，选择合适的工具来回答。如果需要使用工具，请明确指出使用的工具名称。
如果不需要工具，请直接回答。
"""
    
    def _init_agent_executor(self):
        """初始化 LangChain Agent Executor"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        self._agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        logger.info("[UnifiedAgent] Agent Executor 初始化完成")
    
    async def process(
        self,
        user_input: str,
        context: Dict = None,
        chat_history: List = None
    ) -> AgentResponse:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入
            context: 额外上下文信息
            chat_history: 对话历史 [(human_message, ai_message), ...]
        
        Returns:
            AgentResponse: Agent 响应结果
        """
        logger.info(f"[UnifiedAgent] 处理问题: {user_input[:50]}...")
        
        context = context or {}
        chat_history = chat_history or []
        
        try:
            input_data = {
                "input": user_input,
                "chat_history": chat_history
            }
            
            result = await self._agent_executor.ainvoke(input_data)
            
            output = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])
            
            tools_used = []
            tool_calls = []
            sources = []
            
            for step in intermediate_steps:
                if len(step) >= 2:
                    action = step[0]
                    observation = step[1]
                    
                    tools_used.append(action.tool)
                    tool_calls.append({
                        "tool": action.tool,
                        "input": action.tool_input,
                        "output": str(observation)[:500]
                    })
                    
                    if hasattr(observation, "sources"):
                        sources.extend(observation.sources or [])
            
            logger.info(
                f"[UnifiedAgent] 完成, 使用工具: {tools_used}, "
                f"中间步骤: {len(intermediate_steps)}"
            )
            
            return AgentResponse(
                answer=output,
                sources=list(set(sources)) if sources else None,
                tools_used=tools_used,
                tool_calls=tool_calls,
                metadata={
                    "agent_type": self.agent_type.value,
                    "intermediate_steps": len(intermediate_steps),
                    **context
                },
                conversation_id=self.conversation_id,
                user_id=self.user_id
            )
            
        except Exception as e:
            logger.error(f"[UnifiedAgent] 处理失败: {e}", exc_info=True)
            return AgentResponse(
                answer=f"处理失败: {str(e)}",
                tools_used=[],
                tool_calls=[],
                metadata={"error": str(e)},
                conversation_id=self.conversation_id,
                user_id=self.user_id
            )


class AgentFactory:
    """
    Agent 工厂类
    根据配置创建不同类型的 Agent
    """
    
    @staticmethod
    def create_rag_agent(
        llm: Any,
        kb_ids: List[int],
        db: Any,
        agent_type: AgentType = AgentType.OPENAI_FUNCTIONS,
        conversation_id: str = None,
        user_id: int = None
    ) -> UnifiedAgent:
        """创建基于知识库的 Agent"""
        tools = create_rag_tools(kb_ids=kb_ids, db=db)
        
        system_prompt = f"""你是一个知识库问答助手。你的任务是回答用户关于知识库的问题。

知识库 ID: {kb_ids}

请先尝试使用知识库工具查找相关信息，如果知识库无法回答，再使用其他工具。
请始终引用你找到的来源。"""
        
        return UnifiedAgent(
            llm=llm,
            tools=tools,
            agent_type=agent_type,
            conversation_id=conversation_id,
            user_id=user_id,
            system_prompt=system_prompt
        )
    
    @staticmethod
    def create_sql_agent(
        llm: Any,
        kb_id: int,
        db: Any,
        agent_type: AgentType = AgentType.OPENAI_FUNCTIONS,
        conversation_id: str = None,
        user_id: int = None
    ) -> UnifiedAgent:
        """创建 SQL 查询 Agent"""
        tools = create_sql_tools(kb_id=kb_id, db=db)
        
        system_prompt = """你是一个数据库查询助手。你的任务是帮助用户查询和分析数据库中的数据。

你可以直接执行 SQL 查询来获取数据。请确保查询是安全的，不要执行危险操作。"""
        
        return UnifiedAgent(
            llm=llm,
            tools=tools,
            agent_type=agent_type,
            conversation_id=conversation_id,
            user_id=user_id,
            system_prompt=system_prompt
        )
    
    @staticmethod
    def create_multi_tool_agent(
        llm: Any,
        text_kb_ids: List[int],
        db_kb_id: int,
        db: Any,
        agent_type: AgentType = AgentType.OPENAI_FUNCTIONS,
        conversation_id: str = None,
        user_id: int = None
    ) -> UnifiedAgent:
        """创建多工具 Agent（同时支持 RAG 和 SQL）"""
        
        tools = []
        
        if text_kb_ids:
            tools.extend(create_rag_tools(kb_ids=text_kb_ids, db=db))
        
        if db_kb_id:
            tools.extend(create_sql_tools(kb_id=db_kb_id, db=db))
        
        if not tools:
            tools.append(create_chat_tool(llm=llm))
        
        system_prompt = """你是一个多功能助手，结合了知识库问答和数据库查询能力。

你可以：
1. 使用知识库工具回答关于文档、内容的问题
2. 使用数据库工具查询业务数据（销售、订单、统计等）
3. 如果问题不需要外部工具，直接回答

请根据用户问题选择合适的工具。"""
        
        return UnifiedAgent(
            llm=llm,
            tools=tools,
            agent_type=agent_type,
            conversation_id=conversation_id,
            user_id=user_id,
            system_prompt=system_prompt
        )
    
    @staticmethod
    def create_chat_agent(
        llm: Any,
        conversation_id: str = None,
        user_id: int = None,
        system_prompt: str = None
    ) -> UnifiedAgent:
        """创建纯对话 Agent（无工具）"""
        
        tools = [create_chat_tool(llm=llm)]
        
        return UnifiedAgent(
            llm=llm,
            tools=tools,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            conversation_id=conversation_id,
            user_id=user_id,
            system_prompt=system_prompt
        )


def create_agent(
    llm: Any,
    tools: List[BaseTool],
    agent_type: AgentType = AgentType.OPENAI_FUNCTIONS,
    conversation_id: str = None,
    user_id: int = None,
    system_prompt: str = None
) -> UnifiedAgent:
    """
    创建 Agent 的工厂函数
    
    Args:
        llm: LangChain LLM 实例
        tools: LangChain 工具列表
        agent_type: Agent 类型
        conversation_id: 会话 ID
        user_id: 用户 ID
        system_prompt: 系统提示词
    
    Returns:
        UnifiedAgent: 配置好的 Agent 实例
    """
    return UnifiedAgent(
        llm=llm,
        tools=tools,
        agent_type=agent_type,
        conversation_id=conversation_id,
        user_id=user_id,
        system_prompt=system_prompt
    )
