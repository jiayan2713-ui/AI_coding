#!/usr/bin/env python3
"""生成RAG系统流程图的Python脚本"""

import os
import subprocess
import sys

def generate_mermaid_diagram():
    """生成Mermaid流程图"""
    mmd_file = "docs/diagrams/rag-system-flowchart.mmd"
    output_dir = "docs/diagrams/output"

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    print(f"生成流程图从: {mmd_file}")

    return True

if __name__ == "__main__":
    generate_mermaid_diagram()