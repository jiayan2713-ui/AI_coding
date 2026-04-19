from typing import Optional, Any, Dict
from fastapi import HTTPException, status


class RAGException(Exception):
    """RAG系统基础异常"""

    def __init__(self, message: str, detail: Optional[str] = None, status_code: int = 500):
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.message)


class DocumentProcessingError(RAGException):
    """文档处理异常"""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=f"文档处理失败: {message}",
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class UnsupportedFormatError(DocumentProcessingError):
    """不支持的文档格式异常"""

    def __init__(self, format: str, detail: Optional[str] = None):
        super().__init__(
            message=f"不支持的文档格式: {format}",
            detail=detail
        )


class VectorStoreError(RAGException):
    """向量存储异常"""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=f"向量存储操作失败: {message}",
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class EmbeddingError(RAGException):
    """嵌入向量生成异常"""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=f"嵌入向量生成失败: {message}",
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ModelAPIError(RAGException):
    """模型API调用异常"""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=f"模型API调用失败: {message}",
            detail=detail,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class OutOfScopeError(RAGException):
    """超出范围异常"""

    def __init__(self, message: str = "问题超出文档范围", detail: Optional[str] = None):
        super().__init__(
            message=message,
            detail=detail,
            status_code=status.HTTP_200_OK  # 注意：这是正常业务逻辑，不是错误
        )


class ConversationNotFoundError(RAGException):
    """对话不存在异常"""

    def __init__(self, conversation_id: str, detail: Optional[str] = None):
        super().__init__(
            message=f"对话不存在: {conversation_id}",
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND
        )


class DocumentNotFoundError(RAGException):
    """文档不存在异常"""

    def __init__(self, document_id: str, detail: Optional[str] = None):
        super().__init__(
            message=f"文档不存在: {document_id}",
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ValidationError(RAGException):
    """验证异常"""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=f"验证失败: {message}",
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class FileSizeExceededError(RAGException):
    """文件大小超出限制异常"""

    def __init__(self, max_size_mb: int, detail: Optional[str] = None):
        super().__init__(
            message=f"文件大小超过限制: {max_size_mb}MB",
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ConfigurationError(RAGException):
    """配置异常"""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message=f"配置错误: {message}",
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def handle_rag_exception(exc: RAGException) -> Dict[str, Any]:
    """处理RAG异常，返回标准错误响应"""
    return {
        "error": exc.message,
        "detail": exc.detail,
        "timestamp": "..."  # 实际实现中应该使用datetime
    }


def http_exception_handler(request, exc: HTTPException):
    """HTTP异常处理器"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": "..."  # 实际实现中应该使用datetime
    }


def generic_exception_handler(request, exc: Exception):
    """通用异常处理器"""
    return {
        "error": "内部服务器错误",
        "detail": str(exc),
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "timestamp": "..."  # 实际实现中应该使用datetime
    }