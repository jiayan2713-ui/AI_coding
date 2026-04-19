import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from loguru import logger


class VectorStore:
    def __init__(self, persist_directory: str, collection_name: str = "document_embeddings"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None

        os.makedirs(persist_directory, exist_ok=True)
        self._initialize_client()

    def _initialize_client(self):
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )

            try:
                self.collection = self.client.get_collection(self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info(f"Created collection: {self.collection_name}")
        except Exception as exc:
            logger.error(f"Failed to initialize vector store: {exc}")
            raise

    async def add_documents(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> int:
        if not chunks or not embeddings:
            return 0

        try:
            ids: List[str] = []
            documents: List[str] = []
            metadatas: List[Dict[str, Any]] = []

            for chunk in chunks:
                chunk_id = f"{chunk['document_id']}_{chunk['chunk_index']}"
                ids.append(chunk_id)
                documents.append(chunk["content"])
                metadatas.append(
                    {
                        "document_id": chunk["document_id"],
                        "filename": chunk["filename"],
                        "chunk_index": chunk["chunk_index"],
                        "total_chunks": chunk["total_chunks"],
                        "document_type": chunk["document_type"],
                        **chunk.get("metadata", {}),
                    }
                )

            self.collection.upsert(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )

            logger.info(f"Upserted {len(chunks)} chunks into vector store")
            return len(chunks)
        except Exception as exc:
            logger.error(f"Failed to add documents to vector store: {exc}")
            raise

    async def search_similar(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"],
            )

            formatted_results: List[Dict[str, Any]] = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    formatted_results.append(
                        {
                            "chunk_id": results["ids"][0][i] if results["ids"] else "",
                            "content": results["documents"][0][i],
                            "similarity_score": 1 - results["distances"][0][i],
                            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        }
                    )

            return formatted_results
        except Exception as exc:
            logger.error(f"Failed to query vector store: {exc}")
            raise

    async def delete_document(self, document_id: str) -> int:
        try:
            results = self.collection.get(
                where={"document_id": document_id},
                include=["ids"],
            )

            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted document {document_id}, chunks={len(results['ids'])}")
                return len(results["ids"])

            logger.warning(f"Document not found in vector store: {document_id}")
            return 0
        except Exception as exc:
            logger.error(f"Failed to delete document: {exc}")
            raise

    async def get_collection_stats(self) -> Dict[str, Any]:
        try:
            count = self.collection.count()
            sample = self.collection.peek(limit=1)
            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "sample_metadata": sample["metadatas"][0] if sample["metadatas"] else None,
            }
        except Exception as exc:
            logger.error(f"Failed to get collection stats: {exc}")
            raise

    async def reset_collection(self) -> bool:
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Reset collection: {self.collection_name}")
            return True
        except Exception as exc:
            logger.error(f"Failed to reset collection: {exc}")
            raise


def create_vector_store() -> VectorStore:
    from dotenv import load_dotenv

    load_dotenv()

    persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "document_embeddings")

    return VectorStore(
        persist_directory=persist_directory,
        collection_name=collection_name,
    )
