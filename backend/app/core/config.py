import os
from typing import Dict, Any
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import yaml

# 加载环境变量
load_dotenv()


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "RAG智能文档问答系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # DeepSeek API配置
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    DEEPSEEK_EMBEDDING_MODEL: str = "deepseek-embedding"  # 已弃用，保留用于兼容性
    DEEPSEEK_TIMEOUT: int = 30
    DEEPSEEK_MAX_RETRIES: int = 3

    # 嵌入模型类型配置
    EMBEDDING_MODEL_TYPE: str = "local"  # local 或 deepseek

    # 本地嵌入模型配置
    LOCAL_EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    LOCAL_EMBEDDING_DEVICE: str = "cpu"
    LOCAL_EMBEDDING_BATCH_SIZE: int = 32
    LOCAL_EMBEDDING_CACHE_DIR: str = "./data/model_cache"
    LOCAL_EMBEDDING_NORMALIZE: bool = True
    EMBEDDING_DIMENSIONS: int = 384  # 本地模型维度

    # 向量存储配置
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "document_embeddings"

    # 文档处理配置
    MAX_FILE_SIZE_MB: int = 50
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # 范围判断配置
    SIMILARITY_THRESHOLD: float = 0.45
    MAX_RETRIEVAL_DOCS: int = 5

    # 对话管理配置
    CONVERSATION_MAX_HISTORY: int = 10
    CONVERSATION_TTL_HOURS: int = 1

    # CORS配置
    CORS_ORIGINS: list = [
        "http://localhost:8501",
        "http://127.0.0.1:8501"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """加载YAML配置文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载YAML配置文件失败: {e}")
        return {}


# 加载YAML配置文件
settings_yaml = load_yaml_config("config/settings.yaml")
model_config_yaml = load_yaml_config("config/model_config.yaml")

# 创建全局配置实例
settings = Settings()

# 从YAML文件合并配置
if settings_yaml:
    # 合并服务器配置
    if 'server' in settings_yaml:
        server = settings_yaml['server']
        settings.HOST = server.get('host', settings.HOST)
        settings.PORT = server.get('port', settings.PORT)

    # 合并日志配置
    if 'logging' in settings_yaml:
        logging = settings_yaml['logging']
        settings.LOG_LEVEL = logging.get('level', settings.LOG_LEVEL)

    # 合并文档处理配置
    if 'document_processing' in settings_yaml:
        doc_processing = settings_yaml['document_processing']
        settings.CHUNK_SIZE = doc_processing.get('chunk_size', settings.CHUNK_SIZE)
        settings.CHUNK_OVERLAP = doc_processing.get('chunk_overlap', settings.CHUNK_OVERLAP)
        settings.MAX_FILE_SIZE_MB = doc_processing.get('max_file_size_mb', settings.MAX_FILE_SIZE_MB)

    # 合并检索配置
    if 'retrieval' in settings_yaml:
        retrieval = settings_yaml['retrieval']
        settings.SIMILARITY_THRESHOLD = retrieval.get('similarity_threshold', settings.SIMILARITY_THRESHOLD)
        settings.MAX_RETRIEVAL_DOCS = retrieval.get('max_results', settings.MAX_RETRIEVAL_DOCS)

    # 合并对话配置
    if 'conversation' in settings_yaml:
        conversation = settings_yaml['conversation']
        settings.CONVERSATION_MAX_HISTORY = conversation.get('max_history', settings.CONVERSATION_MAX_HISTORY)
        settings.CONVERSATION_TTL_HOURS = conversation.get('ttl_hours', settings.CONVERSATION_TTL_HOURS)

    # 合并CORS配置
    if 'security' in settings_yaml and 'cors_origins' in settings_yaml['security']:
        settings.CORS_ORIGINS = settings_yaml['security']['cors_origins']

# 从模型配置合并
if model_config_yaml:
    if 'deepseek' in model_config_yaml:
        deepseek = model_config_yaml['deepseek']
        settings.DEEPSEEK_BASE_URL = deepseek.get('base_url', settings.DEEPSEEK_BASE_URL)
        settings.DEEPSEEK_TIMEOUT = deepseek.get('timeout', settings.DEEPSEEK_TIMEOUT)
        settings.DEEPSEEK_MAX_RETRIES = deepseek.get('max_retries', settings.DEEPSEEK_MAX_RETRIES)

    if 'models' in model_config_yaml:
        models = model_config_yaml['models']
        if 'chat' in models:
            chat = models['chat']
            settings.DEEPSEEK_MODEL = chat.get('name', settings.DEEPSEEK_MODEL)
        if 'embedding' in models:
            embedding = models['embedding']
            settings.DEEPSEEK_EMBEDDING_MODEL = embedding.get('name', settings.DEEPSEEK_EMBEDDING_MODEL)
            # 合并嵌入模型类型配置
            settings.EMBEDDING_MODEL_TYPE = embedding.get('type', settings.EMBEDDING_MODEL_TYPE)
            settings.LOCAL_EMBEDDING_MODEL = embedding.get('local_model', settings.LOCAL_EMBEDDING_MODEL)
            settings.EMBEDDING_DIMENSIONS = embedding.get('dimensions', settings.EMBEDDING_DIMENSIONS)

    # 合并本地模型配置
    if 'local_models' in model_config_yaml:
        local_models = model_config_yaml['local_models']
        if 'embedding' in local_models:
            embedding = local_models['embedding']
            settings.LOCAL_EMBEDDING_MODEL = embedding.get('name', settings.LOCAL_EMBEDDING_MODEL)
            settings.LOCAL_EMBEDDING_DEVICE = embedding.get('device', settings.LOCAL_EMBEDDING_DEVICE)
            settings.LOCAL_EMBEDDING_BATCH_SIZE = embedding.get('batch_size', settings.LOCAL_EMBEDDING_BATCH_SIZE)
            settings.LOCAL_EMBEDDING_CACHE_DIR = embedding.get('cache_dir', settings.LOCAL_EMBEDDING_CACHE_DIR)
            settings.LOCAL_EMBEDDING_NORMALIZE = embedding.get('normalize_embeddings', settings.LOCAL_EMBEDDING_NORMALIZE)
