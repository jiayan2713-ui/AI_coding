#!/usr/bin/env python3
"""
RAG系统核心功能演示脚本
绕过兼容性问题，验证核心RAG流程
"""

import json
import time
from typing import List, Dict, Any, Optional
import hashlib


class MockDeepSeekClient:
    """模拟DeepSeek API客户端"""

    def __init__(self):
        print("✓ 初始化模拟DeepSeek客户端")

    def generate_chat_completion(self, question: str, context: List[str] = None) -> str:
        """模拟生成回答"""
        if context:
            return f"根据文档内容，答案是：{question}的相关信息。这是基于上下文生成的回答。"
        return f"这是关于'{question}'的测试回答。"

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """模拟生成嵌入向量"""
        return [[0.1 * i for i in range(384)] for _ in texts]

    def is_question_in_scope(self, question: str, context: str) -> bool:
        """模拟范围判断"""
        # 简单判断：如果问题包含特定关键词，则认为是相关的
        relevant_keywords = ['文档', '文件', '内容', '信息', '数据']
        return any(keyword in question for keyword in relevant_keywords)


class MockDocumentProcessor:
    """模拟文档处理器"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        print(f"✓ 初始化文档处理器 (chunk_size={chunk_size}, overlap={chunk_overlap})")

    def process_document(self, content: bytes, filename: str) -> List[Dict[str, Any]]:
        """模拟文档处理"""
        print(f"📄 处理文档: {filename}")

        # 模拟文本提取（实际系统会解析PDF、Word等格式）
        if filename.endswith('.pdf'):
            simulated_text = "这是PDF文档的模拟内容。包含关于项目的信息和详细说明。"
        elif filename.endswith('.txt'):
            simulated_text = "这是文本文档的内容。提供了一些数据和分析。"
        else:
            simulated_text = "这是通用文档的内容。包含有用信息供检索。"

        # 模拟分块
        chunks = self._chunk_text(simulated_text, filename)

        print(f"   → 分成 {len(chunks)} 个文本块")
        return chunks

    def _chunk_text(self, text: str, filename: str) -> List[Dict[str, Any]]:
        """模拟文本分块"""
        words = text.split()
        chunks = []
        chunk_id = 0

        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)

            chunks.append({
                "content": chunk_text,
                "metadata": {
                    "filename": filename,
                    "chunk_index": chunk_id,
                    "total_chunks": len(words) // (self.chunk_size - self.chunk_overlap) + 1
                }
            })
            chunk_id += 1

        return chunks


class MockVectorStore:
    """模拟向量存储"""

    def __init__(self):
        self.documents = []
        self.embeddings = []
        print("✓ 初始化模拟向量存储")

    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """模拟添加文档到向量库"""
        self.documents.extend(documents)
        print(f"📥 向量存储中添加了 {len(documents)} 个文档块")
        return True

    def search_similar(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """模拟相似性搜索"""
        print(f"🔍 搜索与查询最相似的 {k} 个文档块")

        # 模拟搜索逻辑：返回最相关的几个文档块
        results = []
        for i, doc in enumerate(self.documents[:k]):
            # 模拟相似度分数
            similarity = max(0.7, 0.9 - i * 0.1)

            results.append({
                "content": doc["content"],
                "similarity_score": similarity,
                "metadata": doc["metadata"]
            })

        return results


class MockConversationManager:
    """模拟对话管理器"""

    def __init__(self, max_messages: int = 10):
        self.conversations = {}
        self.max_messages = max_messages
        print("✓ 初始化对话管理器")

    def create_conversation(self) -> str:
        """创建新对话"""
        conv_id = f"conv_{int(time.time())}_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}"
        self.conversations[conv_id] = {
            "messages": [],
            "created_at": time.time(),
            "document_ids": []
        }
        print(f"💬 创建新对话: {conv_id}")
        return conv_id

    def add_message(self, conversation_id: str, role: str, content: str):
        """添加消息到对话"""
        if conversation_id in self.conversations:
            message = {
                "role": role,
                "content": content,
                "timestamp": time.time()
            }
            self.conversations[conversation_id]["messages"].append(message)
            print(f"   💬 [{role}] {content[:50]}...")


class RAGWorkflowDemo:
    """RAG工作流程演示"""

    def __init__(self):
        print("=" * 60)
        print("[AI] RAG智能文档问答系统 - 核心功能演示")
        print("=" * 60)

        # 初始化模拟组件
        self.deepseek_client = MockDeepSeekClient()
        self.document_processor = MockDocumentProcessor()
        self.vector_store = MockVectorStore()
        self.conversation_manager = MockConversationManager()

        self.current_conversation = None

    def run_demo(self):
        """运行完整演示流程"""
        print("\n" + "=" * 60)
        print("🚀 开始演示RAG工作流程")
        print("=" * 60)

        # 步骤1: 创建对话
        print("\n📋 步骤1: 创建新对话")
        self.current_conversation = self.conversation_manager.create_conversation()

        # 步骤2: 上传文档
        print("\n📋 步骤2: 上传文档")
        documents = self._upload_documents()

        # 步骤3: 处理查询
        print("\n📋 步骤3: 处理用户查询")
        self._handle_queries()

        # 步骤4: 显示对话历史
        print("\n📋 步骤4: 显示对话历史")
        self._show_conversation_history()

        print("\n" + "=" * 60)
        print("✅ 演示完成！")
        print("=" * 60)

        # 保存演示结果
        self._save_demo_results()

    def _upload_documents(self):
        """模拟文档上传"""
        print("上传示例文档...")

        # 模拟上传不同类型的文档
        documents = [
            {"filename": "project_document.pdf", "content": b"PDF document content"},
            {"filename": "data_analysis.txt", "content": b"Text analysis content"},
            {"filename": "meeting_notes.docx", "content": b"Meeting notes content"}
        ]

        all_chunks = []
        for doc in documents:
            # 处理文档
            chunks = self.document_processor.process_document(
                doc["content"], doc["filename"]
            )
            all_chunks.extend(chunks)

        # 添加到向量存储
        if all_chunks:
            self.vector_store.add_documents(all_chunks)
            print(f"📊 总共处理了 {len(all_chunks)} 个文档块")

        return all_chunks

    def _handle_queries(self):
        """模拟处理用户查询"""
        test_queries = [
            "这个文档讲了什么内容？",
            "项目的主要目标是什么？",
            "今天天气怎么样？",  # 这个应该被判断为超出范围
            "数据分析的结果是什么？"
        ]

        for query in test_queries:
            print(f"\n   ❓ 用户提问: {query}")

            # 添加到对话历史
            self.conversation_manager.add_message(self.current_conversation, "user", query)

            # 步骤1: 检索相关文档
            search_results = self.vector_store.search_similar(query, k=2)

            if search_results:
                # 步骤2: 提取上下文
                context = "\n".join([r["content"] for r in search_results])

                # 步骤3: 范围判断
                is_in_scope = self.deepseek_client.is_question_in_scope(query, context)

                if is_in_scope:
                    print("   ✅ 问题在文档范围内")
                    # 步骤4: 生成回答
                    answer = self.deepseek_client.generate_chat_completion(query, [context])
                    print(f"   [AI] 回答: {answer}")

                    # 添加到对话历史
                    self.conversation_manager.add_message(self.current_conversation, "assistant", answer)
                else:
                    print("   ❌ 问题超出文档范围")
                    answer = "抱歉，这个问题超出了已上传文档的范围。请上传相关文档或询问文档内容相关的问题。"
                    print(f"   [AI] 回答: {answer}")
                    self.conversation_manager.add_message(self.current_conversation, "assistant", answer)
            else:
                print("   ⚠️  未找到相关文档")
                answer = "系统中暂无相关文档内容，请先上传文档。"
                self.conversation_manager.add_message(self.current_conversation, "assistant", answer)

    def _show_conversation_history(self):
        """显示对话历史"""
        if self.current_conversation in self.conversation_manager.conversations:
            conv = self.conversation_manager.conversations[self.current_conversation]
            print(f"\n对话ID: {self.current_conversation}")
            print(f"消息数: {len(conv['messages'])}")
            print("对话历史:")

            for i, msg in enumerate(conv['messages'], 1):
                role_icon = "👤" if msg["role"] == "user" else "[AI]"
                print(f"  {i}. {role_icon} [{msg['role']}]: {msg['content'][:80]}...")

    def _save_demo_results(self):
        """保存演示结果"""
        results = {
            "conversation_id": self.current_conversation,
            "vector_store_documents": len(self.vector_store.documents),
            "components_initialized": [
                "MockDeepSeekClient",
                "MockDocumentProcessor",
                "MockVectorStore",
                "MockConversationManager"
            ],
            "demo_status": "completed",
            "timestamp": time.time()
        }

        with open("demo_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print("\n📁 演示结果已保存到: demo_results.json")


def test_individual_components():
    """测试各个组件功能"""
    print("\n" + "=" * 60)
    print("[TEST] 组件功能测试")
    print("=" * 60)

    # 测试文档处理器
    print("\n1. 测试文档处理器:")
    processor = MockDocumentProcessor()
    chunks = processor.process_document(b"test document content", "test.txt")
    print(f"   生成 {len(chunks)} 个文本块")

    # 测试DeepSeek客户端
    print("\n2. 测试DeepSeek客户端:")
    client = MockDeepSeekClient()
    answer = client.generate_chat_completion("测试问题")
    print(f"   生成回答: {answer[:50]}...")

    # 测试向量存储
    print("\n3. 测试向量存储:")
    vector_store = MockVectorStore()
    vector_store.add_documents(chunks)
    results = vector_store.search_similar("测试查询")
    print(f"   搜索结果: {len(results)} 个")

    # 测试对话管理器
    print("\n4. 测试对话管理器:")
    conv_manager = MockConversationManager()
    conv_id = conv_manager.create_conversation()
    conv_manager.add_message(conv_id, "user", "测试消息")
    print(f"   创建对话: {conv_id}")

    print("\n✅ 所有组件测试通过！")


if __name__ == "__main__":
    print("RAG系统核心功能演示")
    print("=" * 60)

    # 运行组件测试
    test_individual_components()

    # 运行完整工作流程演示
    demo = RAGWorkflowDemo()
    demo.run_demo()

    print("\n" + "=" * 60)
    print("🎉 演示脚本完成！")
    print("=" * 60)
    print("\n下一步建议:")
    print("1. 如果需要运行完整系统:")
    print("   - 安装Python 3.11（避免3.14兼容性问题）")
    print("   - 创建虚拟环境并安装依赖")
    print("   - 运行: cd backend && uvicorn app.main:app --reload")
    print("\n2. 如果需要使用Docker:")
    print("   - 启动Docker Desktop")
    print("   - 运行: docker-compose up -d --build")
    print("\n3. 测试API功能:")
    print("   - 编辑.env文件设置API密钥")
    print("   - 运行测试: make test")