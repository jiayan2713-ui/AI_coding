#!/usr/bin/env python3
"""生成RAG系统流程图的Python脚本"""

import os
import subprocess
import sys

def validate_mermaid_syntax(mmd_content: str) -> bool:
    """验证Mermaid语法"""
    # 简单的语法检查
    required_elements = ["graph", "subgraph", "-->", "style"]
    for element in required_elements:
        if element not in mmd_content:
            print(f"警告: 缺少必需元素: {element}")
            return False
    return True

def generate_mermaid_diagram():
    """生成Mermaid流程图"""
    mmd_file = "docs/diagrams/rag-system-flowchart.mmd"
    output_dir = "docs/diagrams/output"

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 读取Mermaid文件
    with open(mmd_file, 'r', encoding='utf-8') as f:
        mmd_content = f.read()

    # 验证语法
    if not validate_mermaid_syntax(mmd_content):
        print("Mermaid语法检查失败")
        return False

    print(f"Mermaid文件读取成功: {mmd_file}")
    print(f"内容长度: {len(mmd_content)} 字符")

    return True

if __name__ == "__main__":
    generate_mermaid_diagram()