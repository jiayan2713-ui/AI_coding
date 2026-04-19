#!/usr/bin/env python
"""检查向量存储中的文档内容"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.vector_store import create_vector_store
import asyncio

async def check_vector_store():
    """检查向量存储"""
    print("检查向量存储...")

    try:
        # 创建向量存储实例
        vector_store = create_vector_store()

        # 获取集合统计信息
        stats = await vector_store.get_collection_stats()
        print(f"集合统计: {stats}")

        # 使用vector_store的collection属性来获取文档
        collection = vector_store.collection

        # 获取前10个文档
        results = collection.get(limit=10)

        print(f"\n集合中的文档数量: {collection.count()}")

        if results['documents']:
            print(f"\n前 {len(results['documents'])} 个文档:")
            for i, (doc_id, document, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
                print(f"\n--- 文档 {i+1} ---")
                print(f"ID: {doc_id}")
                print(f"元数据: {metadata}")
                print(f"内容预览: {document[:500]}...")
                print(f"内容长度: {len(document)} 字符")

                # 如果是docx文档，打印更多信息
                if metadata.get('document_type') == 'docx':
                    print(f"文档类型: Word文档")
                    print(f"文件名: {metadata.get('filename', '未知')}")
                    print(f"块索引: {metadata.get('chunk_index', '未知')}")
                    print(f"总块数: {metadata.get('total_chunks', '未知')}")
                    print(f"单词范围: {metadata.get('start_word', '未知')}-{metadata.get('end_word', '未知')}")
                    print(f"单词数: {metadata.get('word_count', '未知')}")
        else:
            print("\n集合为空")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

async def test_embedding_query():
    """测试嵌入查询"""
    print("\n\n测试嵌入查询...")

    try:
        from backend.app.services.embedding_client import create_embedding_client

        # 创建嵌入客户端
        embedding_client = create_embedding_client()

        # 测试查询
        test_queries = [
            "前端无法连接后端",
            "文档内容",
            "测试"
        ]

        for query in test_queries:
            print(f"\n查询: '{query}'")
            embeddings = await embedding_client.get_embeddings([query])
            if embeddings:
                print(f"嵌入维度: {embeddings[0].dimensions}")
                print(f"嵌入向量长度: {len(embeddings[0].embedding)}")
                print(f"嵌入向量前5个值: {embeddings[0].embedding[:5]}")

    except Exception as e:
        print(f"嵌入查询错误: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("=" * 60)
    print("向量存储检查脚本")
    print("=" * 60)

    await check_vector_store()
    await test_embedding_query()

    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())