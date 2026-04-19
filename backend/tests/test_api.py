import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from backend.app.main import app


client = TestClient(app)


class TestHealthEndpoints:
    def test_root_endpoint(self):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data

    def test_health_endpoint(self):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "services" in data


class TestDocumentEndpoints:
    @patch("app.api.endpoints.rag_engine")
    def test_upload_document_success(self, mock_rag_engine):
        """测试文档上传成功"""
        # 模拟服务响应
        mock_rag_engine.process_document_upload.return_value = {
            "document_id": "test-doc-id",
            "filename": "test.pdf",
            "chunks_count": 5,
            "processing_time": 1.5,
            "conversation_id": None
        }

        # 模拟文件上传
        files = {"file": ("test.pdf", b"test content", "application/pdf")}

        response = client.post("/api/v1/documents/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["document_id"] == "test-doc-id"
        assert data["filename"] == "test.pdf"
        assert data["chunks_count"] == 5

    @patch("app.api.endpoints.rag_engine")
    def test_upload_document_with_conversation(self, mock_rag_engine):
        """测试带对话ID的文档上传"""
        mock_rag_engine.process_document_upload.return_value = {
            "document_id": "test-doc-id",
            "filename": "test.pdf",
            "chunks_count": 5,
            "processing_time": 1.5,
            "conversation_id": "test-conv-id"
        }

        files = {"file": ("test.pdf", b"test content", "application/pdf")}
        params = {"conversation_id": "test-conv-id"}

        response = client.post("/api/v1/documents/upload", files=files, params=params)

        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "test-conv-id"


class TestQueryEndpoints:
    @patch("app.api.endpoints.rag_engine")
    def test_query_document_success(self, mock_rag_engine):
        """测试文档查询成功"""
        # 模拟服务响应
        mock_rag_engine.process_query.return_value = {
            "answer": "测试回答",
            "conversation_id": "test-conv-id",
            "is_in_scope": True,
            "confidence": 0.85,
            "search_results": [
                {
                    "chunk_id": "chunk-1",
                    "content": "测试内容",
                    "similarity_score": 0.85,
                    "metadata": {"filename": "test.pdf"}
                }
            ],
            "scope_reasoning": "在范围内",
            "processing_time": 0.5,
            "timestamp": "2024-01-01T00:00:00"
        }

        # 发送查询请求
        payload = {
            "question": "测试问题",
            "conversation_id": "test-conv-id"
        }

        response = client.post("/api/v1/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "测试回答"
        assert data["conversation_id"] == "test-conv-id"
        assert data["is_in_scope"] is True
        assert len(data["search_results"]) == 1

    @patch("app.api.endpoints.rag_engine")
    def test_query_out_of_scope(self, mock_rag_engine):
        """测试超出范围的查询"""
        from backend.app.core.exceptions import OutOfScopeError

        # 模拟超出范围异常
        mock_rag_engine.process_query.side_effect = OutOfScopeError("超出范围")

        payload = {"question": "超出范围的问题"}
        response = client.post("/api/v1/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["is_in_scope"] is False
        assert "抱歉" in data["answer"] or "超出" in data["answer"]


class TestConversationEndpoints:
    @patch("app.api.endpoints.conversation_manager")
    def test_get_conversation(self, mock_conversation_manager):
        """测试获取对话"""
        from backend.app.models.schemas import ConversationHistory, Message
        from datetime import datetime

        # 模拟对话数据
        mock_conversation = ConversationHistory(
            conversation_id="test-conv-id",
            messages=[
                Message(
                    role="user",
                    content="测试问题",
                    timestamp=datetime.now()
                ),
                Message(
                    role="assistant",
                    content="测试回答",
                    timestamp=datetime.now()
                )
            ],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            document_ids=["doc-1"]
        )

        mock_conversation_manager.get_conversation.return_value = mock_conversation

        response = client.get("/api/v1/conversations/test-conv-id")

        assert response.status_code == 200
        data = response.json()
        assert data["conversation"]["conversation_id"] == "test-conv-id"
        assert data["total_messages"] == 2

    @patch("app.api.endpoints.conversation_manager")
    def test_delete_conversation(self, mock_conversation_manager):
        """测试删除对话"""
        mock_conversation_manager.delete_conversation.return_value = True

        response = client.delete("/api/v1/conversations/test-conv-id")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "已删除" in data["message"]


class TestStatsEndpoint:
    @patch("app.api.endpoints.rag_engine")
    def test_get_system_stats(self, mock_rag_engine):
        """测试获取系统统计"""
        # 模拟向量存储统计
        mock_rag_engine.vector_store.get_collection_stats.return_value = {
            "collection_name": "document_embeddings",
            "total_documents": 100
        }

        # 模拟对话统计
        mock_rag_engine.conversation_manager.get_conversation_count.return_value = 5
        mock_rag_engine.conversation_manager.get_all_conversations.return_value = []

        response = client.get("/api/v1/stats")

        assert response.status_code == 200
        data = response.json()
        assert "system_info" in data
        assert "vector_store_stats" in data
        assert "conversation_stats" in data
        assert "model_info" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])