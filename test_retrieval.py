#!/usr/bin/env python
"""测试检索功能"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.services.vector_store import create_vector_store
from backend.app.services.embedding_client import create_embedding_client
import asyncio

async def test_retrieval():
    """测试检索功能"""
    print("测试检索功能...")

    try:
        # 创建向量存储和嵌入客户端
        vector_store = create_vector_store()
        embedding_client = create_embedding_client()

        # 测试查询
        test_queries = [
            "前端无法连接后端",  # 技术问题
            "文档内容",           # 通用查询
            "赵佳炎",             # 文档中可能包含的名字
            "简历",               # 可能的相关查询
            "工作经验",           # 可能的相关查询
            "测试"                # 通用查询
        ]

        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"查询: '{query}'")
            print(f"{'='*60}")

            # 获取查询嵌入
            embeddings = await embedding_client.get_embeddings([query])
            if not embeddings:
                print("获取嵌入失败")
                continue

            query_embedding = embeddings[0].embedding

            # 搜索相似文档
            results = await vector_store.search_similar(
                query_embedding=query_embedding,
                n_results=3
            )

            if not results:
                print("没有检索到结果")
                continue

            print(f"检索到 {len(results)} 个结果:")
            for i, result in enumerate(results):
                print(f"\n--- 结果 {i+1} ---")
                print(f"相似度: {result['similarity_score']:.4f}")
                print(f"文档类型: {result['metadata'].get('document_type', '未知')}")
                print(f"文件名: {result['metadata'].get('filename', '未知')}")

                # 显示内容预览（处理Unicode）
                content = result['content']
                preview = content[:300]
                try:
                    print(f"内容预览: {preview}")
                except UnicodeEncodeError:
                    # 如果编码失败，显示字节表示
                    print(f"内容预览 (编码问题): {preview.encode('utf-8', 'replace')[:200]}")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

async def check_document_content():
    """检查文档内容"""
    print("\n\n检查文档内容...")
    print("="*60)

    try:
        vector_store = create_vector_store()
        collection = vector_store.collection

        # 获取所有文档
        results = collection.get(limit=10)

        print(f"总文档数: {len(results['documents'])}")

        for i, (doc_id, document, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            print(f"\n{'='*60}")
            print(f"文档 {i+1}: {metadata.get('filename', '未知')}")
            print(f"文档ID: {doc_id}")
            print(f"类型: {metadata.get('document_type', '未知')}")
            print(f"块: {metadata.get('chunk_index', '未知')}/{metadata.get('total_chunks', '未知')}")
            print(f"单词数: {metadata.get('word_count', '未知')}")
            print(f"处理时间: {metadata.get('processed_at', '未知')}")

            # 将内容保存到文件以便查看
            filename = f"document_{i+1}_content.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(document)

            print(f"内容已保存到: {filename}")
            print(f"内容长度: {len(document)} 字符")
            print(f"前500字符预览:")
            print(document[:500])
            print("...")

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("="*60)
    print("检索系统测试")
    print("="*60)

    await test_retrieval()
    await check_document_content()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())