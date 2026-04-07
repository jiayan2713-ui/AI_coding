# RAG系统流程图

基于Mermaid.js生成的RAG智能文档问答系统高层次架构图。

## 文件结构

- `rag-system-flowchart.mmd` - Mermaid图表源文件
- `generate_flowchart.py` - 生成脚本
- `output/` - 生成的图像文件
  - `rag-system-architecture.png` - 最终PNG图像
  - `rag-system-architecture.svg` - SVG矢量图

## 生成流程

```bash
# 安装依赖
pip install -r requirements-diagrams.txt

# 生成图像
python generate_flowchart.py
```

## 更新流程

1. 编辑 `rag-system-flowchart.mmd`
2. 运行生成脚本
3. 检查输出图像
4. 提交更改