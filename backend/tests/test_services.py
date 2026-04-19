import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime, timedelta

from backend.app.services.deepseek_client import DeepSeekClient
from backend.app.services.document_processor import DocumentProcessor
from backend.app.services.vector_store import VectorStore
from backend.app.services.conversation_manager import ConversationManager
from backend.app.services.rag_engine import RAGEngine
from backend.app.core.exceptions import OutOfScopeError


class TestDeepSeekClient:
    """测试DeepSeek客户端"""

    @pytest.fixture
    def client(self):
        from backend.app.services.deepseek_client import DeepSeekConfig
        config = DeepSeekConfig(
            api_key="test_key",
            base_url="https://api.deepseek.com",
            chat_model="deepseek-chat",
            embedding_model="deepseek-embedding"
        )
        return DeepSeekClient(config)

    @patch("app.services.deepseek_client.AsyncClient")
    def test_generate_chat_completion_success(self, mock_async_client, client):
        """测试生成聊天补全成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "测试回答"}}]
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value = mock_client_instance

        response = client.generate_chat_completion("测试问题", [])

        assert response == "测试回答"

    @patch("app.services.deepseek_client.AsyncClient")
    def test_generate_embeddings_success(self, mock_async_client, client):
        """测试生成嵌入向量成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1, 0.2, 0.3]}]
        }

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_async_client.return_value = mock_client_instance

        embeddings = client.generate_embeddings(["测试文本"])

        assert len(embeddings) == 1
        assert embeddings[0] == [0.1, 0.2, 0.3]

    def test_is_question_in_scope_true(self, client):
        """测试问题在范围内"""
        context = "这是相关上下文。"
        question = "这个问题相关吗？"

        with patch.object(client, 'generate_chat_completion', return_value="是的，这个问题在文档范围内。") as mock_generate:
            result = client.is_question_in_scope(question, context)

            assert result is True

    def test_is_question_in_scope_false(self, client):
        """测试问题不在范围内"""
        context = "这是相关上下文。"
        question = "这个问题相关吗？"

        with patch.object(client, 'generate_chat_completion', return_value="不，这个问题不在文档范围内。") as mock_generate:
            result = client.is_question_in_scope(question, context)

            assert result is False


class TestDocumentProcessor:
    """测试文档处理器"""

    @pytest.fixture
    def processor(self):
        return DocumentProcessor(
            chunk_size=1000,
            chunk_overlap=200
        )

    @pytest.mark.asyncio
    async def test_process_pdf_document(self, processor):
        """测试处理PDF文档"""
        test_pdf_content = b"%PDF-1.4 test content"

        with patch("PyPDF2.PdfReader") as mock_pdf_reader:
            mock_reader = MagicMock()
            mock_reader.pages = [MagicMock(extract_text=lambda: "页面内容")]
            mock_pdf_reader.return_value = mock_reader

            document_id, chunks = await processor.process_document("test.pdf", test_pdf_content)

            assert len(chunks) > 0
            assert "页面内容" in chunks[0].content

    @pytest.mark.asyncio
    async def test_process_text_document(self, processor):
        """测试处理文本文档"""
        test_text = "这是纯文本内容。".encode('utf-8')

        document_id, chunks = await processor.process_document("test.txt", test_text)

        assert len(chunks) == 1
        assert "纯文本内容" in chunks[0].content

    def test_chunk_text(self, processor):
        """测试文本分块"""
        from backend.app.services.document_processor import DocumentType
        text = "a " * 600  # 大约1200字符，应该分成2块

        chunks = processor.chunk_text(text, "test_doc_id", "test.txt", DocumentType.TXT)

        assert len(chunks) >= 2


class TestVectorStore:
    """测试向量存储"""

    @pytest.fixture
    def vector_store(self):
        return VectorStore(
            persist_directory="./test_chroma_db",
            collection_name="test_collection"
        )

    @patch("app.services.vector_store.chromadb.PersistentClient")
    @pytest.mark.asyncio
    async def test_add_documents(self, mock_chroma_client, vector_store):
        """测试添加文档"""
        mock_collection = MagicMock()
        mock_collection.add.return_value = True
        mock_chroma_client.return_value.get_or_create_collection.return_value = mock_collection

        chunks = [
            {"content": "文档1内容", "document_id": "doc1", "filename": "doc1.txt", "chunk_index": 0, "total_chunks": 1, "document_type": "txt", "metadata": {}},
            {"content": "文档2内容", "document_id": "doc2", "filename": "doc2.txt", "chunk_index": 0, "total_chunks": 1, "document_type": "txt", "metadata": {}}
        ]
        embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

        result = await vector_store.add_documents(chunks, embeddings)

        assert result == 2  # 返回添加的文档数

    @patch("app.services.vector_store.chromadb.PersistentClient")
    @pytest.mark.asyncio
    async def test_search_similar(self, mock_chroma_client, vector_store):
        """测试相似性搜索"""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "documents": [["检索到的内容"]],
            "metadatas": [[{"filename": "test.txt"}]],
            "distances": [[0.1]],
            "ids": [["chunk_1"]]
        }
        mock_chroma_client.return_value.get_or_create_collection.return_value = mock_collection

        results = await vector_store.search_similar([0.1, 0.2, 0.3], n_results=3)

        assert len(results) == 1
        assert results[0]["content"] == "检索到的内容"


class TestConversationManager:
    """测试对话管理器"""

    @pytest.fixture
    def manager(self):
        return ConversationManager(max_history=5, ttl_hours=1)

    def test_create_conversation(self, manager):
        """测试创建对话"""
        conv_id = manager.create_conversation()

        assert conv_id is not None
        assert conv_id in manager.conversations

    @pytest.mark.asyncio
    async def test_add_message(self, manager):
        """测试添加消息"""
        conv_id = manager.create_conversation()

        await manager.add_message(conv_id, "user", "测试问题")
        await manager.add_message(conv_id, "assistant", "测试回答")

        conv = await manager.get_conversation(conv_id)

        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[1].content == "测试回答"

    @pytest.mark.asyncio
    async def test_conversation_ttl(self):
        """测试对话TTL过期"""
        manager = ConversationManager(max_history=5, ttl_hours=1/3600)  # 1秒TTL

        conv_id = manager.create_conversation()
        # 手动设置updated_at为过去的时间
        conversation = manager.conversations[conv_id]
        conversation.updated_at = datetime.now() - timedelta(hours=1)

        # 清理过期对话
        await manager._cleanup_expired_conversations()

        assert conv_id not in manager.conversations


class TestRAGEngine:
    """测试RAG引擎"""

    @pytest.fixture
    def rag_engine(self):
        with patch("backend.app.services.rag_engine.DeepSeekClient") as mock_deepseek, \
             patch("backend.app.services.rag_engine.VectorStore") as mock_vector, \
             patch("backend.app.services.rag_engine.DocumentProcessor") as mock_doc, \
             patch("backend.app.services.rag_engine.ConversationManager") as mock_conv:

            from backend.app.services.rag_engine import RAGEngine
            # 创建mock实例
            mock_deepseek_instance = MagicMock()
            mock_vector_instance = MagicMock()
            mock_doc_instance = MagicMock()
            mock_conv_instance = MagicMock()
            # 返回带有mock实例的RAGEngine
            return RAGEngine(
                deepseek_client=mock_deepseek_instance,
                vector_store=mock_vector_instance,
                conversation_manager=mock_conv_instance
            )

    def test_process_document_upload(self, rag_engine):
        """测试处理文档上传"""
        mock_document = "测试文档内容".encode('utf-8')
        filename = "test.pdf"

        # 模拟处理器返回分块
        rag_engine.document_processor.process_document.return_value = [
            {"content": "分块1", "metadata": {"filename": "test.pdf"}},
            {"content": "分块2", "metadata": {"filename": "test.pdf"}}
        ]

        # 模拟向量存储添加成功
        rag_engine.vector_store.add_documents.return_value = True

        result = rag_engine.process_document_upload(mock_document, filename)

        assert "document_id" in result
        assert result["filename"] == "test.pdf"
        assert result["chunks_count"] == 2

    def test_process_query_in_scope(self, rag_engine):
        """测试处理范围内查询"""
        question = "测试问题"
        conversation_id = "test-conv-id"

        # 模拟向量搜索返回结果
        rag_engine.vector_store.search_similar.return_value = [
            {"content": "相关上下文", "similarity_score": 0.85, "metadata": {"filename": "test.pdf"}}
        ]

        # 模拟范围判断为真
        rag_engine.deepseek_client.is_question_in_scope.return_value = True

        # 模拟生成回答
        rag_engine.deepseek_client.generate_chat_completion.return_value = "测试回答"

        result = rag_engine.process_query(question, conversation_id)

        assert result["answer"] == "测试回答"
        assert result["is_in_scope"] is True
        assert len(result["search_results"]) == 1

    def test_process_query_out_of_scope(self, rag_engine):
        """测试处理范围外查询"""
        question = "不相关问题"
        conversation_id = "test-conv-id"

        # 模拟向量搜索返回结果
        rag_engine.vector_store.search_similar.return_value = [
            {"content": "不相关上下文", "similarity_score": 0.3, "metadata": {"filename": "test.pdf"}}
        ]

        # 模拟范围判断为假
        rag_engine.deepseek_client.is_question_in_scope.return_value = False

        with pytest.raises(OutOfScopeError):
            rag_engine.process_query(question, conversation_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])