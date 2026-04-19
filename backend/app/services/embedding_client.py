"""
本地嵌入模型客户端
使用 sentence-transformers 进行文本嵌入计算
"""

import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from loguru import logger
from pydantic import BaseModel


class EmbeddingResponse(BaseModel):
    """嵌入响应模型"""
    embedding: List[float]
    model: str
    dimensions: int


class BaseEmbeddingClient(ABC):
    """嵌入客户端基类"""

    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[EmbeddingResponse]:
        """获取文本嵌入向量"""
        pass

    @abstractmethod
    def get_model_info(self) -> dict:
        """获取模型信息"""
        pass


class LocalEmbeddingClient(BaseEmbeddingClient):
    """本地嵌入模型客户端"""

    def __init__(self, model_name: str, device: str = "cpu",
                 batch_size: int = 32, cache_dir: Optional[str] = None,
                 normalize: bool = True):
        """
        初始化本地嵌入模型客户端

        Args:
            model_name: 模型名称，如 "BAAI/bge-small-zh-v1.5"
            device: 运行设备，"cpu" 或 "cuda"
            batch_size: 批处理大小
            cache_dir: 模型缓存目录
            normalize: 是否归一化嵌入向量
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.cache_dir = cache_dir
        self.normalize = normalize
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """初始化本地模型"""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"正在加载本地嵌入模型: {self.model_name}, device={self.device}")

            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_dir
            )

            logger.info(f"本地嵌入模型加载完成: {self.model_name}, 维度={self.model.get_sentence_embedding_dimension()}")

        except ImportError as e:
            logger.error(f"导入 sentence-transformers 失败: {e}")
            logger.error("请安装依赖: pip install sentence-transformers torch")
            raise
        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            raise

    async def get_embeddings(self, texts: List[str]) -> List[EmbeddingResponse]:
        """获取文本嵌入向量（本地推理）"""
        if not self.model:
            raise RuntimeError("模型未初始化")

        if not texts:
            return []

        try:
            # 检查文本长度，避免过长文本
            processed_texts = []
            for text in texts:
                if len(text) > 10000:  # 超长文本截断
                    logger.warning(f"文本过长 ({len(text)} 字符)，截断为前10000字符")
                    processed_texts.append(text[:10000])
                else:
                    processed_texts.append(text)

            # 分批处理以避免内存问题
            all_embeddings = []
            for i in range(0, len(processed_texts), self.batch_size):
                batch = processed_texts[i:i + self.batch_size]

                batch_embeddings = self.model.encode(
                    batch,
                    batch_size=len(batch),
                    normalize_embeddings=self.normalize,
                    show_progress_bar=False,
                    convert_to_numpy=True
                )

                # 转换为EmbeddingResponse对象
                for embedding in batch_embeddings:
                    all_embeddings.append(
                        EmbeddingResponse(
                            embedding=embedding.tolist(),
                            model=self.model_name,
                            dimensions=embedding.shape[0]
                        )
                    )

            logger.debug(f"成功生成 {len(all_embeddings)} 个嵌入向量，批次大小={self.batch_size}")
            return all_embeddings

        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise

    def get_model_info(self) -> dict:
        """获取模型信息"""
        if not self.model:
            return {
                "type": "local",
                "model": self.model_name,
                "device": self.device,
                "status": "not_initialized"
            }

        return {
            "type": "local",
            "model": self.model_name,
            "device": self.device,
            "dimensions": self.model.get_sentence_embedding_dimension(),
            "normalize": self.normalize,
            "batch_size": self.batch_size,
            "cache_dir": self.cache_dir,
            "status": "ready"
        }


class EmbeddingClientFactory:
    """嵌入客户端工厂"""

    @staticmethod
    def create_client(embedding_type: str = "local", **kwargs):
        """
        创建嵌入客户端

        Args:
            embedding_type: 嵌入类型，目前只支持 "local"
            **kwargs: 客户端参数

        Returns:
            BaseEmbeddingClient 实例
        """
        if embedding_type == "local":
            return LocalEmbeddingClient(
                model_name=kwargs.get("model_name", "BAAI/bge-small-zh-v1.5"),
                device=kwargs.get("device", "cpu"),
                batch_size=kwargs.get("batch_size", 32),
                cache_dir=kwargs.get("cache_dir"),
                normalize=kwargs.get("normalize", True)
            )
        else:
            raise ValueError(f"不支持的嵌入类型: {embedding_type}")


# 便捷函数
def create_embedding_client() -> BaseEmbeddingClient:
    """
    创建嵌入客户端（基于配置）

    从环境变量读取配置创建本地嵌入客户端
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    embedding_type = os.getenv("EMBEDDING_MODEL_TYPE", "local")

    if embedding_type == "local":
        return EmbeddingClientFactory.create_client(
            embedding_type="local",
            model_name=os.getenv("LOCAL_EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5"),
            device=os.getenv("LOCAL_EMBEDDING_DEVICE", "cpu"),
            batch_size=int(os.getenv("LOCAL_EMBEDDING_BATCH_SIZE", "32")),
            cache_dir=os.getenv("LOCAL_EMBEDDING_CACHE_DIR"),
            normalize=os.getenv("LOCAL_EMBEDDING_NORMALIZE", "true").lower() == "true"
        )
    else:
        # 理论上不会执行，因为只支持本地模型
        raise ValueError(f"不支持的嵌入类型: {embedding_type}")