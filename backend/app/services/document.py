import os
from typing import List
from fastapi import UploadFile, HTTPException
import PyPDF2
from docx import Document

from ..core.config import settings
from ..models.knowledge import DocumentChunk
from .rag import RAGService


class DocumentService:
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service
    
    async def process_uploaded_file(self, file: UploadFile, knowledge_base_id: int) -> List[DocumentChunk]:
        """处理上传的文件"""
        # 检查文件类型
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # 读取文件内容
        content = await self._read_file_content(file, file_extension)
        
        if not content:
            raise HTTPException(status_code=400, detail="无法读取文件内容")
        
        # 处理文档内容
        return self.rag_service.process_document(content, knowledge_base_id)
    
    async def _read_file_content(self, file: UploadFile, file_extension: str) -> str:
        """根据文件类型读取内容"""
        content = ""
        
        if file_extension == '.pdf':
            content = await self._read_pdf(file)
        elif file_extension == '.docx':
            content = await self._read_docx(file)
        elif file_extension in ['.txt', '.md']:
            content = await self._read_text(file)
        
        return content
    
    async def _read_pdf(self, file: UploadFile) -> str:
        """读取PDF文件内容"""
        try:
            # 读取文件内容
            content = await file.read()
            
            # 使用PyPDF2解析PDF
            pdf_reader = PyPDF2.PdfReader(content)
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF文件解析失败：{str(e)}")
    
    async def _read_docx(self, file: UploadFile) -> str:
        """读取Word文档内容"""
        try:
            # 读取文件内容
            content = await file.read()
            
            # 使用python-docx解析Word文档
            doc = Document(content)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Word文档解析失败：{str(e)}")
    
    async def _read_text(self, file: UploadFile) -> str:
        """读取文本文件内容"""
        try:
            content = await file.read()
            return content.decode('utf-8')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"文本文件读取失败：{str(e)}")