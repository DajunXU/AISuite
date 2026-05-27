from typing import List, Optional, Generator, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, text, create_engine

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage

import asyncio

from ..core.config import settings
from ..core.logger import get_logger
from ..models.knowledge import DocumentChunk, KnowledgeBase
from ..models.llm import LLMKeyManager
from ..models.embedding import EmbeddingModel, EmbeddingKeyManager
from ..schemas.chat import ChatStreamResponse
from .sql_agent import create_sql_agent_from_kb

logger = get_logger("rag")


class RAGService:
    def __init__(self, db: Session = None):
        self.db = db
        self.llm = None
        self.embeddings = None

        # 从数据库获取默认向量模型的维度
        self.embedding_dimensions = self._get_default_embedding_dimensions()

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )

    def _get_default_embedding_dimensions(self) -> int:
        """从数据库获取默认向量模型的维度"""
        if not self.db:
            return 1024  # 如果没有数据库会话，使用 1024 作为后备

        try:
            default_model = self.db.query(EmbeddingModel).filter(
                EmbeddingModel.is_default == True,
                EmbeddingModel.is_active == True
            ).first()

            if default_model and default_model.dimensions:
                logger.info(f"[LangChain RAG] 从数据库获取默认向量维度: {default_model.dimensions}")
                return default_model.dimensions
        except Exception as e:
            logger.warning(f"[LangChain RAG] 获取默认向量维度失败: {e}")

        return 1024  # 默认使用 1024

    def _init_llm(self, api_key: str = None, base_url: str = None, provider: str = "openai", model: object = None):
        """初始化 LangChain LLM 客户端"""
        api_key = api_key or settings.OPENAI_API_KEY

        model_name = "gpt-3.5-turbo"
        if model and hasattr(model, 'model_name'):
            model_name = model.model_name

        if not base_url:
            if provider and (provider.lower() == "zhipu" or provider.lower() == "智谱"):
                base_url = "https://open.bigmodel.cn/api/paas/v4/"
            elif provider and ("qwen" in provider.lower() or "千问" in provider):
                base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

        logger.info(f"初始化 LLM (LangChain)，base_url: {base_url}, model: {model_name}")
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0.7,
            streaming=True
        )

        self.current_model = model

    def _init_embeddings(self, api_key: str = None, base_url: str = None, embeddings_model: str = None):
        """初始化 LangChain Embeddings - 仅作为备用，向量模型由知识库配置决定"""
        api_key = api_key or settings.OPENAI_API_KEY

        if embeddings_model is None:
            embeddings_model = settings.EMBEDDING_MODEL

        embeddings_base_url = base_url

        logger.info(f"初始化Embeddings(备用): model={embeddings_model}, base_url={embeddings_base_url}")
        self.embeddings = OpenAIEmbeddings(
            model=embeddings_model,
            api_key=api_key,
            base_url=embeddings_base_url,
            timeout=120
        )

    def _init_embeddings_from_model(self, embedding_model: EmbeddingModel):
        """根据向量模型配置初始化 Embeddings"""
        try:
            key_manager = EmbeddingKeyManager()
            api_key = ""

            if embedding_model.api_key_encrypted:
                api_key = key_manager.decrypt_api_key(embedding_model.api_key_encrypted)

            if not api_key:
                if embedding_model.provider == "qwen" or "dashscope" in (embedding_model.base_url or ""):
                    import os
                    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
                elif embedding_model.provider == "zhipu":
                    import os
                    api_key = os.environ.get("ZHIPU_API_KEY", "")
                elif embedding_model.provider == "openai":
                    api_key = settings.OPENAI_API_KEY

            if not api_key:
                raise ValueError(f"向量模型 {embedding_model.name} 未配置API密钥")

            base_url = embedding_model.base_url or "https://api.openai.com/v1"

            logger.info(
                f"[LangChain RAG] 初始化向量模型: name={embedding_model.name}, model={embedding_model.model_name}, base_url={base_url}")

            self.embeddings = OpenAIEmbeddings(
                model=embedding_model.model_name,
                api_key=api_key,
                base_url=base_url,
                timeout=120
            )

            if hasattr(embedding_model, 'dimensions') and embedding_model.dimensions:
                self.embedding_dimensions = embedding_model.dimensions
                logger.info(f"[LangChain RAG] 向量维度已设置为: {self.embedding_dimensions}")
        except Exception as e:
            logger.error(f"[LangChain RAG] 初始化向量模型失败: {e}")
            raise

    def set_db(self, db: Session):
        """设置数据库会话"""
        self.db = db

    async def generate_answer(self, question: str, user_id: int, text_kb_id: Optional[int] = None,
                              db_kb_id: Optional[int] = None, api_key: str = None, base_url: str = None,
                              provider: str = None, model: object = None, system_prompt: str = None) -> tuple[
        str, List[str]]:
        """生成回答（异步）"""
        logger.info(f"[LangChain RAG] 开始处理问题: {question}")

        try:
            relevant_chunks = []
            sources = []

            if text_kb_id:
                text_chunks = await self._get_relevant_chunks(question, text_kb_id)
                relevant_chunks.extend(text_chunks)
                logger.info(f"[LangChain RAG] 从文本知识库获取到 {len(text_chunks)} 个相关文档片段")

            db_answer = None
            db_source = None
            if db_kb_id:
                try:
                    sql_agent = create_sql_agent_from_kb(db_kb_id, self.db)
                    result = sql_agent.query(question)
                    if result.get("success"):
                        answer_text = result.get("answer", "")
                        if answer_text and len(answer_text) > 10:
                            db_answer = answer_text
                            db_source = "数据库查询"
                            logger.info("[LangChain RAG] SQL Agent 查询成功")
                        else:
                            logger.info("[LangChain RAG] SQL Agent 返回结果为空")
                    else:
                        logger.warning(f"[LangChain RAG] SQL Agent 查询失败: {result.get('error')}")
                    sql_agent.close()
                except Exception as e:
                    logger.error(f"[LangChain RAG] SQL Agent 初始化或执行失败: {e}")

            # 没有选择知识库时，直接调用 LLM 回答
            if not text_kb_id and not db_kb_id:
                logger.info("[LangChain RAG] 未选择知识库，直接调用 LLM 回答")
                if self.llm is None:
                    self._init_llm(api_key=api_key, base_url=base_url, provider=provider, model=model)

                # 构建简单提示词
                prompt = f"请回答以下问题：\n\n问题：{question}"
                if system_prompt:
                    prompt = f"{system_prompt}\n\n问题：{question}"

                logger.info("[LangChain RAG] 调用 LLM 生成回答...")
                response = await self.llm.agenerate([[HumanMessage(content=prompt)]])
                answer = response.generations[0][0].text

                return answer, []

            if not relevant_chunks and not db_answer:
                return "抱歉，我没有找到相关的信息来回答您的问题。", []

            if db_answer and not relevant_chunks:
                return db_answer, [db_source] if db_source else ["数据库查询"]

            context_parts = []
            if relevant_chunks:
                context_parts.extend([chunk.content for chunk in relevant_chunks])
                sources.extend([f"文档片段 {i + 1}" for i in range(len(relevant_chunks))])

            if db_answer:
                context_parts.append(f"数据库查询结果:\n{db_answer}")
                sources.append("数据库查询")

            context = "\n\n".join(context_parts)
            prompt = self._build_prompt(question, context, system_prompt)

            if self.llm is None:
                self._init_llm(api_key=api_key, base_url=base_url, provider=provider, model=model)

            logger.info("[LangChain RAG] 调用 LLM 生成回答...")
            response = await self.llm.agenerate([[HumanMessage(content=prompt)]])
            answer = response.generations[0][0].text

            return answer, sources

        except Exception as e:
            logger.error(f"[LangChain RAG] 处理错误: {e}", exc_info=True)
            return f"生成回答时出现错误：{str(e)}", []

    async def stream_answer(self, question: str, user_id: int, text_kb_id: Optional[int] = None,
                            db_kb_id: Optional[int] = None, api_key: str = None, base_url: str = None,
                            provider: str = None, model: object = None, system_prompt: str = None) -> Generator[
        ChatStreamResponse, None, None]:
        """流式生成回答"""
        relevant_chunks = []

        if text_kb_id:
            text_chunks = await self._get_relevant_chunks(question, text_kb_id)
            relevant_chunks.extend(text_chunks)

        db_answer = None
        db_source = None
        if db_kb_id:
            try:
                sql_agent = create_sql_agent_from_kb(db_kb_id, self.db)
                result = sql_agent.query(question)
                if result.get("success"):
                    answer_text = result.get("answer", "")
                    if answer_text and len(answer_text) > 10:
                        db_answer = answer_text
                        db_source = "数据库查询"
                        logger.info("SQL Agent 查询成功")
                    else:
                        logger.info("SQL Agent 返回结果为空")
                else:
                    logger.warning(f"SQL Agent 查询失败: {result.get('error')}")
                sql_agent.close()
            except Exception as e:
                logger.error(f"SQL Agent 初始化或执行失败: {e}")

        # 没有选择知识库时，直接调用 LLM 回答
        if not text_kb_id and not db_kb_id:
            logger.info("[LangChain RAG] 未选择知识库，直接调用 LLM 回答")
            try:
                if self.llm is None:
                    if model:
                        key_manager = LLMKeyManager()
                        api_key_decrypted = api_key or key_manager.decrypt_api_key(model.api_key_encrypted) if hasattr(
                            model, 'api_key_encrypted') else api_key
                        self._init_llm(
                            api_key=api_key_decrypted,
                            base_url=base_url or (model.base_url if model else None),
                            provider=provider or (model.provider if model else None),
                            model=model
                        )
                    else:
                        self._init_llm()

                prompt = f"请回答以下问题：\n\n问题：{question}"
                if system_prompt:
                    prompt = f"{system_prompt}\n\n问题：{question}"

                logger.info("[LangChain RAG] 调用 LLM 生成回答...")
                full_response = ""

                async for chunk in self.llm.astream(prompt):
                    if chunk.content:
                        full_response += chunk.content
                        yield ChatStreamResponse(content=chunk.content, is_final=False)

                yield ChatStreamResponse(content="", is_final=True, sources=[])

            except Exception as e:
                yield ChatStreamResponse(content=f"生成回答时出现错误：{str(e)}", is_final=True)
            return

        if not relevant_chunks and not db_answer:
            yield ChatStreamResponse(content="抱歉，我没有找到相关的信息来回答您的问题。", is_final=True)
            return

        if db_answer and not relevant_chunks:
            yield ChatStreamResponse(content=db_answer, is_final=True,
                                     sources=[db_source] if db_source else ["数据库查询"])
            return

        context_parts = []
        if relevant_chunks:
            context_parts.extend([chunk.content for chunk in relevant_chunks])

        if db_answer:
            context_parts.append(f"数据库查询结果:\n{db_answer}")

        context = "\n\n".join(context_parts)
        prompt = self._build_prompt(question, context, system_prompt)

        try:
            if self.llm is None:
                if model:
                    key_manager = LLMKeyManager()
                    api_key_decrypted = api_key or key_manager.decrypt_api_key(model.api_key_encrypted) if hasattr(
                        model, 'api_key_encrypted') else api_key
                    self._init_llm(
                        api_key=api_key_decrypted,
                        base_url=base_url or (model.base_url if model else None),
                        provider=provider or (model.provider if model else None),
                        model=model
                    )
                else:
                    self._init_llm()

            full_response = ""

            async for chunk in self.llm.astream(prompt):
                if chunk.content:
                    full_response += chunk.content
                    yield ChatStreamResponse(content=chunk.content, is_final=False)

            sources = [f"文档片段 {i + 1}" for i in range(len(relevant_chunks))]
            yield ChatStreamResponse(content="", is_final=True, sources=sources)

        except Exception as e:
            yield ChatStreamResponse(content=f"生成回答时出现错误：{str(e)}", is_final=True)

    async def _get_relevant_chunks(self, question: str, knowledge_base_id: Optional[int] = None) -> List[DocumentChunk]:
        """获取相关的文档片段"""
        if not self.db:
            return []

        logger.info(f"[LangChain RAG] 开始检索知识库 {knowledge_base_id}...")

        base_query = self.db.query(DocumentChunk)

        if knowledge_base_id:
            base_query = base_query.filter(DocumentChunk.knowledge_base_id == knowledge_base_id)

            kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == knowledge_base_id).first()
            if kb and kb.embedding_model_id:
                embedding_model = self.db.query(EmbeddingModel).filter(
                    EmbeddingModel.id == kb.embedding_model_id).first()
                if embedding_model:
                    logger.info(f"[LangChain RAG] 使用知识库配置的向量模型: {embedding_model.name}")
                    self._init_embeddings_from_model(embedding_model)
                elif not embedding_model or not embedding_model.is_active:
                    logger.warning(f"[LangChain RAG] 知识库 {knowledge_base_id} 的向量模型已被删除或禁用")
                    return []

        vector_chunks = await self._vector_search(question, base_query)

        if vector_chunks:
            return vector_chunks

        logger.info("[LangChain RAG] 向量搜索无结果，使用关键词匹配...")
        keywords = []
        try:
            import jieba
            words = jieba.lcut(question)
            keywords = [word for word in words if len(word) > 1]
        except ImportError:
            for n in range(2, min(7, len(question) + 1)):
                for i in range(len(question) - n + 1):
                    keyword = question[i:i + n]
                    if '·' not in keyword and '。' not in keyword and '，' not in keyword:
                        keywords.append(keyword)
            keywords = list(set(keywords))[:10]

        if not keywords:
            return []

        conditions = [DocumentChunk.content.ilike(f'%{keyword}%') for keyword in keywords]
        query = base_query.filter(or_(*conditions))
        relevant_chunks = query.limit(5).all()

        return relevant_chunks

    async def _vector_search(self, question: str, base_query) -> List[DocumentChunk]:
        """使用向量相似度搜索"""
        try:
            if self.embeddings is None:
                self._init_embeddings()

            question_embedding = await self._generate_embedding(question)
            if not question_embedding or all(v == 0 for v in question_embedding):
                return []

            embedding_str = "[" + ",".join(map(str, question_embedding)) + "]"

            engine = create_engine(settings.DATABASE_URL)
            conn = engine.connect()

            kb_id = None
            if base_query is not None:
                try:
                    for criterion in base_query._criterion:
                        if hasattr(criterion, 'left') and hasattr(criterion.left, 'key'):
                            if criterion.left.key == 'knowledge_base_id':
                                kb_id = criterion.right.value
                                break
                except AttributeError:
                    pass

            try:
                if kb_id:
                    sql = text(f"""
                        SELECT id, knowledge_base_id, content, chunk_metadata, chunk_index, created_at
                        FROM document_chunks
                        WHERE knowledge_base_id = :kb_id
                        ORDER BY embedding <=> CAST(:embedding AS vector({self.embedding_dimensions}))
                        LIMIT 5
                    """)
                    params = {"embedding": embedding_str, "kb_id": kb_id}
                else:
                    sql = text(f"""
                        SELECT id, knowledge_base_id, content, chunk_metadata, chunk_index, created_at
                        FROM document_chunks
                        ORDER BY embedding <=> CAST(:embedding AS vector({self.embedding_dimensions}))
                        LIMIT 5
                    """)
                    params = {"embedding": embedding_str}

                result = conn.execute(sql, params)
                rows = result.fetchall()
            finally:
                conn.close()
                engine.dispose()

            if not rows:
                return []

            chunks = []
            for row in rows:
                chunk = DocumentChunk()
                chunk.id = row[0]
                chunk.knowledge_base_id = row[1]
                chunk.content = row[2]
                chunk.chunk_metadata = row[3]
                chunk.chunk_index = row[4]
                chunk.created_at = row[5]
                chunks.append(chunk)

            return chunks

        except Exception as e:
            logger.error(f"[LangChain RAG] 向量搜索失败: {e}")
            return []

    def _build_prompt(self, question: str, context: str, system_prompt: str = None) -> str:
        """构建提示词"""
        system_part = f"{system_prompt}\n\n" if system_prompt else ""

        prompt_template = """{system}基于以下上下文信息，请回答用户的问题。如果上下文信息不足以回答问题，请诚实地告知用户。

        上下文信息：
        {context}

        用户问题：{question}

        请用中文回答，回答要准确、简洁、有帮助："""

        return prompt_template.format(system=system_part, context=context, question=question)

    def process_document(self, content: str, knowledge_base_id: int) -> List[DocumentChunk]:
        """处理文档内容并存储为向量"""
        chunks = self.text_splitter.split_text(content)

        document_chunks = []
        for i, chunk in enumerate(chunks):
            document_chunk = DocumentChunk(
                knowledge_base_id=knowledge_base_id,
                content=chunk,
                chunk_index=i,
                metadata=f"{{\"chunk_size\": {len(chunk)}}}"
            )

            self.db.add(document_chunk)
            document_chunks.append(document_chunk)

        self.db.commit()
        return document_chunks

    async def _generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        try:
            if self.embeddings is None:
                self._init_embeddings()

            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self.embeddings.embed_query,
                text
            )
            return embedding
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            return [0.0] * self.embedding_dimensions

    async def generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量（兼容旧接口）"""
        return await self._generate_embedding(text)

    def generate_answer_sync(
            self,
            question: str,
            kb_ids: List[int] = None,
            user_id: int = 1
    ) -> tuple:
        """
        同步版本的知识库问答

        Args:
            question: 用户问题
            kb_ids: 知识库 ID 列表
            user_id: 用户 ID

        Returns:
            (answer, sources) 元组
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.generate_answer(question, user_id, text_kb_id=kb_ids[0] if kb_ids else None)
                    )
                    return future.result()
            else:
                return asyncio.run(self.generate_answer(question, user_id, text_kb_id=kb_ids[0] if kb_ids else None))
        except Exception as e:
            logger.error(f"[RAGService] 同步调用失败: {e}")
            return f"查询失败: {str(e)}", []


rag_service = RAGService()
