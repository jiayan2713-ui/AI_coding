from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """文档类型枚举"""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    TXT = "txt"
    MD = "md"
    JSON = "json"
    CSV = "csv"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    UNKNOWN = "unknown"


class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="消息角色: user 或 assistant")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ConversationHistory(BaseModel):
    """对话历史模型"""
    conversation_id: str = Field(..., description="对话ID")
    messages: List[Message] = Field(default_factory=list, description="消息列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    document_ids: List[str] = Field(default_factory=list, description="关联的文档ID列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class DocumentChunk(BaseModel):
    """文档分块模型"""
    chunk_id: str = Field(..., description="分块ID")
    content: str = Field(..., description="内容")
    document_id: str = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    chunk_index: int = Field(..., description="分块索引")
    total_chunks: int = Field(..., description="总分块数")
    document_type: DocumentType = Field(..., description="文档类型")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class DocumentUploadRequest(BaseModel):
    """文档上传请求模型"""
    filename: str = Field(..., description="文件名")
    file_content: bytes = Field(..., description="文件内容")


class DocumentUploadResponse(BaseModel):
    """文档上传响应模型"""
    status: str = Field(default="success", description="状态")
    document_id: str = Field(..., description="文档ID")
    filename: str = Field(..., description="文件名")
    chunks_count: int = Field(..., description="分块数量")
    processing_time: float = Field(..., description="处理时间(秒)")
    conversation_id: Optional[str] = Field(None, description="关联的对话ID")
    message: str = Field(default="文档上传成功", description="消息")


class QueryRequest(BaseModel):
    """查询请求模型"""
    question: str = Field(..., description="问题")
    conversation_id: Optional[str] = Field(None, description="对话ID")
    similarity_threshold: Optional[float] = Field(None, description="相似度阈值")
    max_results: Optional[int] = Field(None, description="最大结果数")


class SearchResult(BaseModel):
    """搜索结果模型"""
    chunk_id: str = Field(..., description="分块ID")
    content: str = Field(..., description="内容")
    similarity_score: float = Field(..., description="相似度分数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class QueryResponse(BaseModel):
    """查询响应模型"""
    answer: str = Field(..., description="回答")
    conversation_id: str = Field(..., description="对话ID")
    is_in_scope: bool = Field(..., description="是否在范围内")
    confidence: float = Field(..., description="置信度")
    search_results: List[SearchResult] = Field(default_factory=list, description="搜索结果")
    scope_reasoning: Optional[str] = Field(None, description="范围判断理由")
    processing_time: float = Field(..., description="处理时间(秒)")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ConversationResponse(BaseModel):
    """对话响应模型"""
    conversation: ConversationHistory = Field(..., description="对话历史")
    total_messages: int = Field(..., description="总消息数")
    total_documents: int = Field(..., description="关联文档数")


class ConversationDeleteResponse(BaseModel):
    """对话删除响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    conversation_id: str = Field(..., description="对话ID")


class SystemStats(BaseModel):
    """系统统计模型"""
    model_config = ConfigDict(protected_namespaces=())

    system_info: Dict[str, Any] = Field(default_factory=dict, description="系统信息")
    vector_store_stats: Dict[str, Any] = Field(default_factory=dict, description="向量存储统计")
    conversation_stats: Dict[str, Any] = Field(default_factory=dict, description="对话统计")
    model_info: Dict[str, Any] = Field(default_factory=dict, description="模型信息")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="状态: healthy, degraded, unhealthy")
    version: str = Field(..., description="版本号")
    services: Dict[str, str] = Field(default_factory=dict, description="服务状态")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细错误信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")