"""
SQL Agent - 基于 LangChain 的业务增强 SQL 查询 Agent
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase

from ..models.knowledge import DatabaseConnection, TableMetadata, ColumnMetadata, MetricDefinition, KnowledgeBase
from ..models.llm import LLMModel, LLMKeyManager
from ..core.config import settings
from ..core.logger import get_logger

logger = get_logger("sql_agent")


class BusinessSQLAgent:
    """基于 LangChain 的业务增强 SQL Agent 类"""
    
    def __init__(self, datasource_id: int, rag_service: Any = None, db: Session = None, user_context: Optional[Dict] = None):
        self.datasource_id = datasource_id
        self.rag_service = rag_service
        self.db = db
        self.user_context = user_context or {}
        
        self.datasource = None
        self.llm = None
        self.metadata_dict = {}
        self.metrics_dict = {}
        self.engine = None
        self.sql_db = None
        
        self._load_datasource()
        self._load_metadata()
        self._load_metrics()
        self._init_llm()
        self._init_database()
        
        self.system_prompt = self._build_enhanced_prompt()
    
    def _load_datasource(self):
        """加载数据源信息"""
        self.datasource = self.db.query(DatabaseConnection).filter(
            DatabaseConnection.id == self.datasource_id
        ).first()
        
        if not self.datasource:
            raise ValueError(f"数据源不存在: {self.datasource_id}")
        
        logger.info(f"[LangChain SQL Agent] 加载数据源: {self.datasource.name} ({self.datasource.db_type})")
    
    def _load_metadata(self):
        """加载表和字段元数据"""
        tables = self.db.query(TableMetadata).filter(
            TableMetadata.connection_id == self.datasource_id,
            TableMetadata.is_selected == True
        ).all()
        
        for table in tables:
            table_info = {
                "comment": table.description or table.table_name_cn or table.table_name,
                "columns": []
            }
            
            columns = self.db.query(ColumnMetadata).filter(
                ColumnMetadata.table_id == table.id,
                ColumnMetadata.is_selected == True
            ).all()
            
            for col in columns:
                col_info = {
                    "name": col.column_name,
                    "type": col.column_type or "unknown",
                    "comment": col.column_comment or "",
                }
                
                if col.synonyms:
                    col_info["synonyms"] = [s.strip() for s in col.synonyms.split(",") if s.strip()]
                
                table_info["columns"].append(col_info)
            
            self.metadata_dict[table.table_name] = table_info
        
        logger.info(f"[LangChain SQL Agent] 加载了 {len(self.metadata_dict)} 个表的元数据")
    
    def _load_metrics(self):
        """加载指标口径定义"""
        tables = self.db.query(TableMetadata).filter(
            TableMetadata.connection_id == self.datasource_id,
            TableMetadata.is_selected == True
        ).all()
        
        table_ids = [t.id for t in tables]
        
        metrics = self.db.query(MetricDefinition).filter(
            MetricDefinition.table_id.in_(table_ids)
        ).all()
        
        for metric in metrics:
            self.metrics_dict[metric.metric_name] = {
                "definition": metric.metric_definition,
                "description": metric.description or "",
                "table": metric.table.table_name if metric.table else ""
            }
        
        logger.info(f"[LangChain SQL Agent] 加载了 {len(self.metrics_dict)} 个指标口径")
    
    def _init_llm(self):
        """初始化 LangChain LLM"""
        model = None
        api_key = settings.OPENAI_API_KEY
        base_url = None
        model_name = "gpt-3.5-turbo"
        
        if self.rag_service and hasattr(self.rag_service, 'llm') and self.rag_service.llm:
            self.llm = self.rag_service.llm
            if hasattr(self.rag_service, 'current_model'):
                model = self.rag_service.current_model
        else:
            llm_model = self.db.query(LLMModel).filter(
                LLMModel.is_default == True,
                LLMModel.is_active == True
            ).first()
            
            if llm_model:
                key_manager = LLMKeyManager()
                api_key = key_manager.decrypt_api_key(llm_model.api_key_encrypted)
                base_url = llm_model.base_url
                model_name = llm_model.model_name
            
            self.llm = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=base_url,
                temperature=0.1,
                streaming=True
            )
        
        self.current_model = model
        logger.info("[LangChain SQL Agent] LLM 初始化完成")
    
    def _init_database(self):
        """初始化 LangChain SQLDatabase"""
        connection_string = self._build_connection_string()
        
        try:
            self.engine = create_engine(
                connection_string,
                pool_pre_ping=True
            )
            
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.sql_db = SQLDatabase.from_uri(connection_string)
            logger.info("[LangChain SQL Agent] 数据库连接成功")
            
        except Exception as e:
            logger.error(f"[LangChain SQL Agent] 数据库连接失败: {e}")
            raise
    
    def _build_connection_string(self) -> str:
        """构建数据库连接字符串"""
        db_type = self.datasource.db_type.lower()
        ds = self.datasource
        
        if ds.connection_string:
            return ds.connection_string
        
        if db_type == "mysql":
            return f"mysql+pymysql://{ds.username}:{ds.password}@{ds.host}:{ds.port}/{ds.database}"
        elif db_type == "postgresql":
            return f"postgresql://{ds.username}:{ds.password}@{ds.host}:{ds.port}/{ds.database}"
        elif db_type == "sqlserver":
            return f"mssql+pyodbc://{ds.username}:{ds.password}@{ds.host}:{ds.port}/{ds.database}?driver=ODBC+Driver+17+for+SQL+Server"
        elif db_type == "sqlite":
            return f"sqlite:///{ds.database}"
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    def _build_enhanced_prompt(self) -> str:
        """构建增强的系统提示词"""
        
        current_date = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        
        metadata_text = "\n".join([
            f"表名: {table_name} ({info['comment']})"
            + "\n  字段: "
            + ", ".join([
                f"{col['name']} ({col['type']})" +
                (f": {col['comment']}" if col['comment'] else "") +
                (f" (同义词: {', '.join(col['synonyms'])})" if col.get('synonyms') else "")
                for col in info['columns']
            ])
            for table_name, info in self.metadata_dict.items()
        ])
        
        metrics_text = ""
        if self.metrics_dict:
            metrics_text = "预定义指标（请优先使用这些口径）：\n"
            for name, info in self.metrics_dict.items():
                metrics_text += f"- {name}: {info['description'] or '无描述'} (SQL: {info['definition']})\n"
        else:
            metrics_text = "（暂无预定义指标）\n"
        
        prompt = f"""你是专业的数据库分析师，擅长根据用户问题生成精确的SQL查询并解读结果。

        【当前时间】
        {current_date}

        【可用数据表】
        {metadata_text}

        【{metrics_text}】

        【工作原则】
        1. 首先理解用户问题的业务意图
        2. 对于业务指标（如"销售额"、"订单量"等），必须严格使用预定义口径
        3. 生成SQL前要确认查询的表和字段存在
        4. 生成的SQL必须是SELECT语句，禁止UPDATE/DELETE/INSERT/ALTER等操作
        5. 限制返回行数不超过{self.datasource.max_rows}行
        6. 如果SQL执行出错，尝试修正（最多3次）
        7. 使用正确的JOIN逻辑关联表

        【回答格式要求】
        请按以下格式回答：

        📊 查询结果：[准确的数据结果]

        🔍 业务解读：[数据背后的业务含义]

        💡 关键洞察：[重要发现和亮点]

        ⚙️ 口经说明：[本次查询使用的指标定义]

        【安全限制】
        - 只允许SELECT查询
        - 如果用户请求超出权限，礼貌拒绝"""
        
        return prompt
    
    def query(self, user_question: str) -> Dict[str, Any]:
        """执行用户查询"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                sql_prompt = self._build_sql_prompt(user_question)
                sql_query = self._call_llm(sql_prompt)
                logger.info(f"[SQL] LLM生成的SQL: {sql_query}")
                
                if not sql_query:
                    return {
                        "success": False,
                        "error": "无法生成有效的SQL查询",
                        "fallback": "抱歉，我无法理解您的查询意图"
                    }
                
                sql_query = self._extract_sql_from_response(sql_query)
                
                if not sql_query:
                    return {
                        "success": False,
                        "error": "无法生成有效的SQL查询",
                        "fallback": "抱歉，我无法理解您的查询意图"
                    }
                
                sql_upper = sql_query.strip().upper()
                if not sql_upper.startswith("SELECT"):
                    return {
                        "success": False,
                        "error": "生成的SQL不是查询语句",
                        "fallback": "抱歉，无法执行该查询"
                    }
                
                if "LIMIT" not in sql_upper:
                    sql_query = sql_query.rstrip().rstrip(';') + f" LIMIT {self.datasource.max_rows}"
                
                result = self._execute_query(sql_query)
                
                if result["success"]:
                    interpretation = self._interpret_results(user_question, result["data"], sql_query)
                    return {
                        "success": True,
                        "answer": interpretation,
                        "data_source": self.datasource.name,
                        "datasource_id": self.datasource_id,
                        "sql_query": sql_query
                    }
                else:
                    if attempt < max_retries - 1:
                        user_question = f"之前的SQL查询出错：{result['error']}。请修正后重新查询。用户问题：{user_question}"
                        continue
                    else:
                        return {
                            "success": False,
                            "error": result["error"],
                            "fallback": "查询遇到问题，请稍后重试或联系管理员"
                        }
                        
            except Exception as e:
                if attempt < max_retries - 1:
                    user_question = f"之前的查询出错：{str(e)}。请重新查询。用户问题：{user_question}"
                    continue
                else:
                    return {
                        "success": False,
                        "error": str(e),
                        "fallback": "查询遇到问题，请稍后重试或联系管理员"
                    }
        
        return {
            "success": False,
            "error": "达到最大重试次数",
            "fallback": "查询遇到问题，请稍后重试或联系管理员"
        }
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LangChain LLM"""
        logger.info(f"[SQL] LLM Prompt:\n{prompt}")
        try:
            response = self.llm.invoke(prompt)
            result = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"[SQL] LLM Response:\n{result}")
            return result
        except Exception as e:
            logger.error(f"[LangChain SQL Agent] LLM 调用失败: {e}")
            raise
    
    def _build_sql_prompt(self, user_question: str) -> str:
        """构建生成 SQL 的提示词"""
        table_schemas = []
        for table_name, info in self.metadata_dict.items():
            columns = []
            for col in info['columns']:
                col_str = f"  - {col['name']} ({col['type']})"
                if col.get('comment'):
                    col_str += f": {col['comment']}"
                if col.get('synonyms'):
                    col_str += f" (同义词: {', '.join(col['synonyms'])})"
                columns.append(col_str)
            
            table_schemas.append(f"表名: {table_name} ({info['comment']})\n" + "\n".join(columns))
        
        table_schema_text = "\n\n".join(table_schemas)
        
        metrics_text = ""
        if self.metrics_dict:
            metrics_text = "预定义指标（必须使用这些口径）：\n"
            for name, info in self.metrics_dict.items():
                metrics_text += f"- {name}: {info['description']} (SQL: {info['definition']})\n"
        
        prompt = f"""你是一个SQL专家。请根据用户问题生成SQL查询。

        可用表结构：
        {table_schema_text}

        {metrics_text}

        用户问题：{user_question}

        要求：
        1. 首先判断用户问题是否与数据库中的任何表数据相关（只要问题涉及到的数据存在于上述表中，就是相关的）
        2. 如果问题与上述任何表都无关（如询问天气、闲聊等），请只返回"INVALID"
        3. 如果问题与上述表相关（即使是与聊天记录、用户信息、系统配置等相关），请生成SELECT查询语句
        4. 只生成SELECT查询语句
        5. 必须使用正确的表名和字段名
        6. 如果问题涉及业务指标（如销售额、订单量），必须使用预定义口径
        7. 返回结果不超过{self.datasource.max_rows}行
        8. 只返回SQL语句，不要其他解释

        判断结果和SQL："""
        return prompt
    
    def _extract_sql_from_response(self, response: str) -> str:
        """从 LLM 响应中提取 SQL"""
        sql = response.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()
        if sql.upper().startswith("SQL"):
            sql = sql[3:].strip()
        
        if sql.upper() == "INVALID":
            logger.info("[SQL Agent] 问题与数据库无关，返回INVALID")
            return None
        
        logger.info(f"[SQL Agent] 生成的SQL: {sql}")
        return sql
    
    def _execute_query(self, sql_query: str) -> Dict[str, Any]:
        """执行 SQL 查询"""
        logger.info(f"[SQL] 执行SQL: {sql_query}")
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql_query))
                columns = result.keys()
                rows = result.fetchall()
                
                data = [dict(zip(columns, row)) for row in rows]
                
                return {
                    "success": True,
                    "data": data,
                    "row_count": len(data)
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _interpret_results(self, user_question: str, data: List[Dict], sql_query: str) -> str:
        """让 LLM 解读查询结果"""
        if not data:
            return "查询结果为空"
        
        data_str = "\n".join([str(row) for row in data[:10]])
        if len(data) > 10:
            data_str += f"\n... (共 {len(data)} 条)"
        
        metric_info = ""
        if self.metrics_dict:
            for name, info in self.metrics_dict.items():
                if name in user_question:
                    metric_info = f"\n\n使用的指标口径：{name} - {info['description']}"
        
        prompt = f"""根据以下查询结果，回答用户问题。

        用户问题：{user_question}

        查询结果：
        {data_str}
        {metric_info}

        请按以下格式回答：
        📊 查询结果：[简洁的数据结果]

        🔍 业务解读：[数据背后的业务含义]

        💡 关键洞察：[重要发现和亮点]

        ⚙️ 口经说明：[本次使用的指标定义]"""
        try:
            result = self._call_llm(prompt)
            return result if result else f"查询结果：{data_str}"
        except Exception as e:
            return f"查询结果：{data_str}\n\n（结果解读失败：{e}）"
    
    def get_available_tables(self) -> List[Dict]:
        """获取可用的表列表"""
        return [
            {
                "name": table_name,
                "comment": info["comment"],
                "column_count": len(info["columns"])
            }
            for table_name, info in self.metadata_dict.items()
        ]
    
    def get_metrics(self) -> Dict[str, Dict]:
        """获取指标口径定义"""
        return self.metrics_dict
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("[LangChain SQL Agent] 数据库连接已关闭")


def create_sql_agent_from_kb(kb_id: int, db: Session) -> BusinessSQLAgent:
    """从知识库ID创建 SQL Agent 的工厂函数"""
    from .rag import RAGService
    
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb or kb.kb_type != 'db':
        raise ValueError("该知识库不是数据库类型")
    
    db_conn = db.query(DatabaseConnection).filter(
        DatabaseConnection.knowledge_base_id == kb_id
    ).first()
    
    if not db_conn:
        raise ValueError("该知识库未配置数据源")
    
    rag_service = RAGService(db)
    
    return BusinessSQLAgent(
        datasource_id=db_conn.id,
        rag_service=rag_service,
        db=db
    )
