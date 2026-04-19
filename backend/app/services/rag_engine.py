import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from loguru import logger

from .conversation_manager import ConversationManager, create_conversation_manager
from .deepseek_client import DeepSeekClient, create_deepseek_client
from .embedding_client import BaseEmbeddingClient, create_embedding_client
from .vector_store import VectorStore, create_vector_store


class RAGEngine:
    def __init__(
        self,
        deepseek_client: DeepSeekClient,
        embedding_client: BaseEmbeddingClient,
        vector_store: VectorStore,
        conversation_manager: ConversationManager,
        similarity_threshold: float = 0.45,
        max_retrieval_docs: int = 5,
    ):
        self.deepseek_client = deepseek_client
        self.embedding_client = embedding_client
        self.vector_store = vector_store
        self.conversation_manager = conversation_manager
        self.similarity_threshold = similarity_threshold
        self.max_retrieval_docs = max_retrieval_docs

    async def process_query(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        document_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        start_time = datetime.now()

        try:
            conversation_id = self.conversation_manager.create_conversation(
                conversation_id=conversation_id
            )

            await self.conversation_manager.add_message(
                conversation_id,
                "user",
                question,
                {"timestamp": datetime.now().isoformat()},
            )

            query_embedding = await self._get_query_embedding(question)
            resolved_filter = await self._resolve_document_filter(conversation_id, document_filter)

            search_results = await self.vector_store.search_similar(
                query_embedding=query_embedding,
                n_results=self.max_retrieval_docs,
                where=resolved_filter,
            )

            is_in_scope, confidence, scope_reasoning = await self._check_scope(
                question,
                search_results,
            )

            if is_in_scope:
                answer = await self._generate_answer(question, search_results, conversation_id)
            else:
                answer = await self.deepseek_client.generate_out_of_scope_response(question)

            await self.conversation_manager.add_message(
                conversation_id,
                "assistant",
                answer,
                {
                    "is_in_scope": is_in_scope,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                "answer": answer,
                "conversation_id": conversation_id,
                "is_in_scope": is_in_scope,
                "confidence": confidence,
                "search_results": [
                    {
                        "chunk_id": result["chunk_id"],
                        "content": result["content"],
                        "similarity_score": result["similarity_score"],
                        "metadata": result["metadata"],
                    }
                    for result in search_results
                ],
                "scope_reasoning": scope_reasoning,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            logger.error(f"Failed to process query: {exc}")
            raise

    async def _get_query_embedding(self, question: str) -> List[float]:
        embeddings_response = await self.embedding_client.get_embeddings([question])
        if embeddings_response and embeddings_response[0].embedding:
            return embeddings_response[0].embedding
        raise ValueError("Failed to generate query embedding")

    async def _check_scope(
        self,
        question: str,
        search_results: List[Dict[str, Any]],
    ) -> Tuple[bool, float, Optional[str]]:
        max_similarity = max((r["similarity_score"] for r in search_results), default=0.0)
        effective_threshold = min(self.similarity_threshold, 0.45)
        similarity_based = max_similarity >= effective_threshold

        if not search_results or not similarity_based:
            return False, max_similarity, "similarity below threshold"

        try:
            context = "\n".join(
                [
                    f"[片段 {i + 1}] {result['content'][:500]}..."
                    for i, result in enumerate(search_results[:3])
                ]
            )
            scope_check = await self.deepseek_client.check_scope(question, context)
            return scope_check.is_in_scope, scope_check.confidence, scope_check.reasoning
        except Exception as exc:
            logger.warning(f"Scope check failed, fallback to similarity: {exc}")
            return similarity_based, max_similarity, f"scope check failed: {str(exc)}"

    async def _resolve_document_filter(
        self,
        conversation_id: Optional[str],
        document_filter: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if document_filter:
            return document_filter

        if not conversation_id:
            return None

        conversation = await self.conversation_manager.get_conversation(conversation_id)
        if not conversation or not conversation.document_ids:
            return None

        if len(conversation.document_ids) == 1:
            return {"document_id": conversation.document_ids[0]}

        return {"document_id": {"$in": conversation.document_ids}}

    async def _generate_answer(
        self,
        question: str,
        search_results: List[Dict[str, Any]],
        conversation_id: str,
    ) -> str:
        try:
            conversation_context = await self.conversation_manager.get_conversation_context(
                conversation_id,
                max_tokens=1000,
            )

            retrieved_context = "\n\n".join(
                [
                    f"[相关文档片段 {i + 1} - 相似度: {result['similarity_score']:.2f}]:\n{result['content']}"
                    for i, result in enumerate(search_results)
                ]
            )

            system_prompt = (
                "你是一个基于检索结果回答问题的助手。"
                "请严格依据检索到的文档内容作答，不要编造信息。"
                "如果文档中没有足够依据，请明确说明。"
                f"\n\n对话历史:\n{conversation_context}"
                f"\n\n检索结果:\n{retrieved_context}"
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ]

            response = await self.deepseek_client.chat_completion(messages)
            return response.response
        except Exception as exc:
            logger.error(f"Failed to generate answer: {exc}")
            return f"生成回答时出现错误: {str(exc)}"

    async def process_document_upload(
        self,
        filename: str,
        file_content: bytes,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_time = datetime.now()

        try:
            from .document_processor import create_document_processor

            processor = create_document_processor()
            document_id, chunks = await processor.process_document(filename, file_content)

            chunk_texts = [chunk.content for chunk in chunks]
            embeddings_response = await self.embedding_client.get_embeddings(chunk_texts)
            embeddings = [resp.embedding for resp in embeddings_response]
            chunk_dicts = [chunk.model_dump() if hasattr(chunk, "model_dump") else chunk.dict() for chunk in chunks]
            chunks_count = await self.vector_store.add_documents(chunk_dicts, embeddings)

            if conversation_id:
                self.conversation_manager.create_conversation(conversation_id=conversation_id)
                await self.conversation_manager.add_document_to_conversation(
                    conversation_id,
                    document_id,
                )

            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                "document_id": document_id,
                "filename": filename,
                "chunks_count": chunks_count,
                "processing_time": processing_time,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as exc:
            logger.error(f"Failed to process document upload: {exc}")
            raise

    async def get_conversation_history(self, conversation_id: str) -> Dict[str, Any]:
        conversation = await self.conversation_manager.get_conversation(conversation_id)
        if not conversation:
            return {"error": "conversation not found"}

        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in conversation.messages
            ],
            "document_ids": conversation.document_ids,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "metadata": conversation.metadata,
        }


def create_rag_engine() -> RAGEngine:
    load_dotenv()

    deepseek_client = create_deepseek_client()
    embedding_client = create_embedding_client()
    vector_store = create_vector_store()
    conversation_manager = create_conversation_manager()

    similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.45"))
    max_retrieval_docs = int(os.getenv("MAX_RETRIEVAL_DOCS", "5"))

    return RAGEngine(
        deepseek_client=deepseek_client,
        embedding_client=embedding_client,
        vector_store=vector_store,
        conversation_manager=conversation_manager,
        similarity_threshold=similarity_threshold,
        max_retrieval_docs=max_retrieval_docs,
    )
