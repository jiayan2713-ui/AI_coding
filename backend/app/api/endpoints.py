from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from backend.app.core.config import settings
from backend.app.core.exceptions import (
    ConversationNotFoundError,
    FileSizeExceededError,
    OutOfScopeError,
    RAGException,
)
from backend.app.models.schemas import (
    ConversationDeleteResponse,
    ConversationResponse,
    DocumentUploadResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    SystemStats,
)
from backend.app.services.rag_engine import create_rag_engine

router = APIRouter()

rag_engine = create_rag_engine()
conversation_manager = rag_engine.conversation_manager


@router.get("/", response_model=dict)
async def root():
    return {
        "message": "RAG document Q&A API",
        "version": settings.APP_VERSION,
        "status": "running",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        services={
            "vector_store": "healthy",
            "deepseek_api": "healthy",
            "document_processor": "healthy",
        },
        timestamp=datetime.now(),
    )


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None,
):
    try:
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)

        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise FileSizeExceededError(settings.MAX_FILE_SIZE_MB)

        result = await rag_engine.process_document_upload(
            filename=file.filename,
            file_content=file_content,
            conversation_id=conversation_id,
        )

        return DocumentUploadResponse(
            status="success",
            document_id=result["document_id"],
            filename=result["filename"],
            chunks_count=result["chunks_count"],
            processing_time=result["processing_time"],
            conversation_id=result.get("conversation_id"),
            message="文档上传成功",
        )
    except RAGException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(exc)}")


@router.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    try:
        document_filter = None
        if request.conversation_id:
            conversation = await conversation_manager.get_conversation(request.conversation_id)
            if conversation and conversation.document_ids:
                if len(conversation.document_ids) == 1:
                    document_filter = {"document_id": conversation.document_ids[0]}
                else:
                    document_filter = {"document_id": {"$in": conversation.document_ids}}

        result = await rag_engine.process_query(
            question=request.question,
            conversation_id=request.conversation_id,
            document_filter=document_filter,
        )

        return QueryResponse(**result)
    except OutOfScopeError as exc:
        return QueryResponse(
            answer=exc.message,
            conversation_id=request.conversation_id or "",
            is_in_scope=False,
            confidence=0.0,
            search_results=[],
            scope_reasoning=exc.detail,
            processing_time=0.0,
            timestamp=datetime.now(),
        )
    except RAGException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(exc)}")


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    try:
        conversation = await conversation_manager.get_conversation(conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)

        return ConversationResponse(
            conversation=conversation,
            total_messages=len(conversation.messages),
            total_documents=len(conversation.document_ids),
        )
    except RAGException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取会话失败: {str(exc)}")


@router.delete("/conversations/{conversation_id}", response_model=ConversationDeleteResponse)
async def delete_conversation(conversation_id: str):
    try:
        success = await conversation_manager.delete_conversation(conversation_id)
        if not success:
            raise ConversationNotFoundError(conversation_id)

        return ConversationDeleteResponse(
            success=True,
            message=f"会话 {conversation_id} 已删除",
            conversation_id=conversation_id,
        )
    except RAGException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"删除会话失败: {str(exc)}")


@router.get("/stats", response_model=SystemStats)
async def get_system_stats():
    try:
        vector_stats = await rag_engine.vector_store.get_collection_stats()
        conversation_count = await conversation_manager.get_conversation_count()
        all_conversations = await conversation_manager.get_all_conversations()
        total_messages = sum(len(conv.messages) for conv in all_conversations)

        return SystemStats(
            system_info={
                "app_name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": "development" if settings.DEBUG else "production",
                "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
                "chunk_size": settings.CHUNK_SIZE,
                "similarity_threshold": settings.SIMILARITY_THRESHOLD,
            },
            vector_store_stats={
                "collection_name": vector_stats.get("collection_name"),
                "total_documents": vector_stats.get("total_documents"),
                "persist_directory": settings.CHROMA_PERSIST_DIRECTORY,
            },
            conversation_stats={
                "total_conversations": conversation_count,
                "total_messages": total_messages,
                "max_history": settings.CONVERSATION_MAX_HISTORY,
                "ttl_hours": settings.CONVERSATION_TTL_HOURS,
            },
            model_info={
                "chat_model": settings.DEEPSEEK_MODEL,
                "embedding_model": settings.DEEPSEEK_EMBEDDING_MODEL,
                "base_url": settings.DEEPSEEK_BASE_URL,
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(exc)}")


@router.get("/documents/formats")
async def get_supported_formats():
    return {
        "supported_formats": [
            "pdf",
            "docx",
            "xlsx",
            "txt",
            "md",
            "json",
            "csv",
            "jpg",
            "jpeg",
            "png",
        ],
        "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
    }
