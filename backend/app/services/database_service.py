import json
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import Session

from ..models.knowledge import DatabaseConnection, KnowledgeBase, TableMetadata
from ..core.logger import get_logger

logger = get_logger("database_service")


class DatabaseService:
    """数据库服务 - 负责数据库连接、SQL生成和查询执行"""
    
    def __init__(self):
        pass
    
    def create_connection(self, db_connection: DatabaseConnection) -> Any:
        """创建数据库连接"""
        try:
            # 构建连接字符串
            if db_connection.connection_string:
                connection_string = db_connection.connection_string
            else:
                connection_string = self._build_connection_string(db_connection)
            
            # 创建引擎
            engine = create_engine(connection_string)
            
            # 测试连接
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            return engine
            
        except Exception as e:
            raise Exception(f"数据库连接失败: {e}")
    
    def _build_connection_string(self, db_connection: DatabaseConnection) -> str:
        """构建数据库连接字符串"""
        db_type = db_connection.db_type.lower()
        
        if db_type == "mysql":
            return f"mysql+pymysql://{db_connection.username}:{db_connection.password}@{db_connection.host}:{db_connection.port}/{db_connection.database}"
        
        elif db_type == "postgresql":
            return f"postgresql://{db_connection.username}:{db_connection.password}@{db_connection.host}:{db_connection.port}/{db_connection.database}"
        
        elif db_type == "sqlserver":
            return f"mssql+pyodbc://{db_connection.username}:{db_connection.password}@{db_connection.host}:{db_connection.port}/{db_connection.database}?driver=ODBC+Driver+17+for+SQL+Server"
        
        elif db_type == "sqlite":
            return f"sqlite:///{db_connection.database}"
        
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    def get_tables(self, db_connection: DatabaseConnection) -> List[Dict[str, Any]]:
        """获取数据库中的所有表"""
        try:
            engine = create_engine(self._build_connection_string(db_connection))
            inspector = inspect(engine)
            
            tables = []
            # MySQL 不使用 schema 参数
            schema = None if db_connection.db_type == "mysql" else db_connection.schema_name
            
            for table_name in inspector.get_table_names(schema=schema):
                tables.append({
                    "table_name": table_name,
                    "columns": self._get_table_columns(engine, table_name, schema)
                })
            
            return tables
            
        except Exception as e:
            raise Exception(f"获取表列表失败: {e}")
    
    def _get_table_columns(self, engine: Any, table_name: str, schema_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表的列信息"""
        inspector = inspect(engine)
        
        columns = []
        for col in inspector.get_columns(table_name, schema=schema_name):
            col_comment = ""
            try:
                col_comment = col.get("comment", "") or ""
            except:
                pass
            columns.append({
                "column_name": col["name"],
                "column_type": str(col["type"]),
                "column_comment": col_comment,
                "is_nullable": col["nullable"]
            })
        
        return columns
    
    async def generate_sql_query(self, question: str, db_connection: DatabaseConnection, engine: Any) -> str:
        """使用大模型生成SQL查询语句"""
        try:
            # 获取数据库表结构信息
            table_schema = self._get_table_schema(engine, db_connection.table_name, db_connection.schema_name)
            
            # 构建提示词
            prompt = self._build_sql_generation_prompt(question, table_schema)
            
            # 调用大模型生成SQL
            response = await self.rag_service.generate_response(prompt, is_sql_generation=True)
            
            # 提取SQL语句
            sql_query = self._extract_sql_from_response(response)
            
            # 验证SQL安全性
            self._validate_sql_security(sql_query)
            
            return sql_query
            
        except Exception as e:
            raise Exception(f"SQL生成失败: {e}")
    
    def _get_table_schema(self, engine: Any, table_name: str, schema_name: Optional[str] = None) -> Dict[str, Any]:
        """获取表结构信息"""
        inspector = inspect(engine)
        
        schema_info = {
            "table_name": table_name,
            "schema_name": schema_name,
            "columns": [],
            "primary_keys": [],
            "foreign_keys": []
        }
        
        # 获取列信息
        columns = inspector.get_columns(table_name, schema=schema_name)
        for column in columns:
            schema_info["columns"].append({
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"],
                "default": column.get("default")
            })
        
        # 获取主键信息
        primary_keys = inspector.get_pk_constraint(table_name, schema=schema_name)
        if primary_keys:
            schema_info["primary_keys"] = primary_keys.get("constrained_columns", [])
        
        # 获取外键信息
        foreign_keys = inspector.get_foreign_keys(table_name, schema=schema_name)
        for fk in foreign_keys:
            schema_info["foreign_keys"].append({
                "constrained_columns": fk["constrained_columns"],
                "referred_table": fk["referred_table"],
                "referred_columns": fk["referred_columns"]
            })
        
        return schema_info
    
    def _build_sql_generation_prompt(self, question: str, table_schema: Dict[str, Any]) -> str:
        """构建SQL生成提示词"""
        prompt = f"""
        你是一个专业的SQL生成助手。请根据用户的问题和数据库表结构生成合适的SQL查询语句。
        
        数据库表结构信息：
        {json.dumps(table_schema, indent=2, ensure_ascii=False)}
        
        用户问题：{question}
        
        要求：
        1. 只生成SELECT查询语句
        2. 不要包含DROP、DELETE、UPDATE等危险操作
        3. 确保SQL语法正确
        4. 如果有条件查询，请使用合适的WHERE子句
        5. 如果查询结果可能很大，请添加LIMIT限制
        6. 只返回SQL语句，不要包含其他解释
        
        请生成SQL查询语句：
        """
        return prompt
    
    def _extract_sql_from_response(self, response: str) -> str:
        """从大模型响应中提取SQL语句"""
        # 简单的SQL提取逻辑
        lines = response.strip().split('\n')
        sql_lines = []
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith(('SELECT', 'WITH')):
                sql_lines.append(line)
            elif sql_lines and not line.upper().startswith('```'):
                sql_lines.append(line)
        
        sql_query = ' '.join(sql_lines)
        
        # 移除可能的代码块标记
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        
        return sql_query
    
    def _validate_sql_security(self, sql_query: str):
        """验证SQL安全性"""
        sql_upper = sql_query.upper()
        
        # 禁止的危险操作
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'CREATE', 'GRANT', 'REVOKE']
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise SecurityError(f"检测到危险SQL操作: {keyword}")
        
        # 确保是SELECT查询
        if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
            raise SecurityError("只允许SELECT查询")
    
    def execute_sql_query(self, engine: Any, sql_query: str) -> List[Dict[str, Any]]:
        """执行SQL查询并返回结果"""
        try:
            with engine.connect() as conn:
                result = conn.execute(text(sql_query))
                
                # 转换为字典列表
                rows = []
                for row in result:
                    rows.append(dict(row._mapping))
                
                return rows
                
        except Exception as e:
            raise Exception(f"SQL执行失败: {e}")
    
    def get_sample_data(self, engine: Any, table_name: str, schema_name: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """获取表样例数据"""
        try:
            schema_part = f"{schema_name}." if schema_name else ""
            sql_query = f"SELECT * FROM {schema_part}{table_name} LIMIT {limit}"
            
            return self.execute_sql_query(engine, sql_query)
            
        except Exception as e:
            raise Exception(f"获取样例数据失败: {e}")


class SecurityError(Exception):
    """安全性错误"""
    pass


async def query_database_by_kb_id(kb_id: int, question: str, db: Any) -> List[str]:
    """根据知识库ID查询数据库"""
    
    knowledge_base = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not knowledge_base or knowledge_base.kb_type != 'db':
        return []
    
    db_connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.knowledge_base_id == kb_id
    ).first()
    
    if not db_connection:
        return []
    
    try:
        engine = database_service.create_connection(db_connection)
        
        tables = db.query(TableMetadata).filter(
            TableMetadata.connection_id == db_connection.id,
            TableMetadata.is_selected == True
        ).all()
        
        if not tables:
            return []
        
        table_names = [t.table_name for t in tables]
        
        sql_query = await database_service.generate_sql_query(
            question, db_connection, engine, table_names
        )
        
        if sql_query:
            results = database_service.execute_sql_query(engine, sql_query)
            return [str(dict(row)) for row in results]
        
        return []
        
    except Exception as e:
        logger.error(f"数据库查询失败: {e}")
        return []
    finally:
        if 'engine' in locals():
            engine.dispose()


# 全局数据库服务实例
database_service = DatabaseService()