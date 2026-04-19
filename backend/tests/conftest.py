"""
测试配置文件，提供共享的fixture和配置
"""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Mock chromadb在导入app之前
sys.modules['chromadb'] = MagicMock()
sys.modules['chromadb'].PersistentClient = MagicMock()
sys.modules['chromadb'].Settings = MagicMock()
# Mock chromadb.config 子模块
sys.modules['chromadb.config'] = MagicMock()
sys.modules['chromadb.config'].Settings = MagicMock()

# Mock pytesseract和PIL用于OCR测试
sys.modules['pytesseract'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['docx'] = MagicMock()
sys.modules['openpyxl'] = MagicMock()
sys.modules['markdown'] = MagicMock()
sys.modules['bs4'] = MagicMock()
sys.modules['bs4.BeautifulSoup'] = MagicMock()

# Mock pydantic_settings和yaml用于配置
sys.modules['pydantic_settings'] = MagicMock()
sys.modules['pydantic_settings'].BaseSettings = MagicMock()
sys.modules['yaml'] = MagicMock()
sys.modules['yaml'].safe_load = MagicMock()

# 创建假配置模块
class MockSettings:
    APP_NAME = "RAG智能文档问答系统"
    APP_VERSION = "1.0.0"
    DEBUG = True
    LOG_LEVEL = "INFO"
    HOST = "0.0.0.0"
    PORT = 8000
    DEEPSEEK_API_KEY = ""
    DEEPSEEK_BASE_URL = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"
    DEEPSEEK_EMBEDDING_MODEL = "deepseek-embedding"
    DEEPSEEK_TIMEOUT = 30
    DEEPSEEK_MAX_RETRIES = 3
    CHROMA_PERSIST_DIRECTORY = "./data/chroma_db"
    CHROMA_COLLECTION_NAME = "document_embeddings"
    MAX_FILE_SIZE_MB = 50
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    SIMILARITY_THRESHOLD = 0.7
    MAX_RETRIEVAL_DOCS = 5
    CONVERSATION_MAX_HISTORY = 10
    CONVERSATION_TTL_HOURS = 1
    CORS_ORIGINS = ["http://localhost:8501", "http://127.0.0.1:8501"]

# 创建假配置模块
mock_config_module = MagicMock()
mock_config_module.settings = MockSettings()
mock_config_module.Settings = MockSettings
mock_config_module.load_yaml_config = MagicMock(return_value={})
sys.modules['backend.app.core.config'] = mock_config_module
sys.modules['app.core.config'] = mock_config_module

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def sample_document_chunks():
    """提供示例文档分块"""
    return [
        {
            "content": "这是第一个文档分块的内容。",
            "metadata": {
                "filename": "test.pdf",
                "chunk_index": 0,
                "total_chunks": 3
            }
        },
        {
            "content": "这是第二个文档分块的内容。",
            "metadata": {
                "filename": "test.pdf",
                "chunk_index": 1,
                "total_chunks": 3
            }
        },
        {
            "content": "这是第三个文档分块的内容。",
            "metadata": {
                "filename": "test.pdf",
                "chunk_index": 2,
                "total_chunks": 3
            }
        }
    ]


@pytest.fixture
def sample_search_results():
    """提供示例搜索结果"""
    return [
        {
            "content": "检索到的第一个相关段落。",
            "similarity_score": 0.92,
            "metadata": {"filename": "document1.pdf"}
        },
        {
            "content": "检索到的第二个相关段落。",
            "similarity_score": 0.85,
            "metadata": {"filename": "document2.pdf"}
        },
        {
            "content": "检索到的第三个相关段落。",
            "similarity_score": 0.78,
            "metadata": {"filename": "document3.pdf"}
        }
    ]


@pytest.fixture
def sample_conversation_messages():
    """提供示例对话消息"""
    from app.models.schemas import Message
    from datetime import datetime

    return [
        Message(
            role="user",
            content="第一个问题是什么？",
            timestamp=datetime.now()
        ),
        Message(
            role="assistant",
            content="这是第一个回答。",
            timestamp=datetime.now()
        ),
        Message(
            role="user",
            content="第二个问题是什么？",
            timestamp=datetime.now()
        ),
        Message(
            role="assistant",
            content="这是第二个回答。",
            timestamp=datetime.now()
        )
    ]