# RAG智能文档问答系统

基于DeepSeek模型的RAG（检索增强生成）智能文档问答系统，支持多格式文档上传、智能范围判断和多轮对话。

## 功能特性

- 📚 **多格式文档支持**: PDF、Word、Excel、TXT、Markdown、JSON、CSV、图片（OCR）
- 🤖 **智能范围判断**: 自动判断问题是否在文档范围内，超出范围婉拒回答
- 💬 **多轮对话**: 支持上下文感知的连续对话
- ⚡ **高性能异步处理**: 基于FastAPI的异步API，支持并发请求
- 🔍 **智能检索**: 基于向量相似度的语义检索
- 📱 **响应式界面**: Streamlit前端，支持桌面端和移动端
- 🐳 **容器化部署**: 支持Docker和Docker Compose一键部署

## 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **AI框架**: LangChain
- **向量数据库**: ChromaDB
- **模型**: DeepSeek（语言模型 + 嵌入模型）
- **文档解析**: PyPDF2, python-docx, openpyxl, Pillow, pytesseract

### 前端
- **框架**: Streamlit
- **UI组件**: 原生Streamlit组件
- **图表**: Plotly

### 部署
- **容器**: Docker + Docker Compose
- **配置管理**: 环境变量 + YAML配置文件

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
make install

# 初始化项目设置
make setup
```

### 2. 配置设置

编辑 `.env` 文件，设置您的DeepSeek API密钥：
```bash
DEEPSEEK_API_KEY=your_api_key_here
```

### 3. 启动服务

#### 方式一：使用Makefile（推荐）

```bash
# 同时启动后端和前端
make run

# 或分别启动
make run-backend
make run-frontend
```

#### 方式二：使用Docker

```bash
# 使用Docker Compose启动所有服务
make docker-up
```

### 4. 访问应用

- **前端界面**: http://localhost:8501
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 使用指南

### 1. 上传文档

1. 打开前端界面 (http://localhost:8501)
2. 在侧边栏选择要上传的文档文件
3. 支持多种格式：PDF、Word、Excel、TXT、Markdown、JSON、CSV、图片
4. 系统会自动处理文档并提取文本内容

### 2. 提问与回答

1. 在聊天输入框中输入您的问题
2. 系统会基于上传的文档内容生成回答
3. 如果问题超出文档范围，系统会友好地提示

### 3. 多轮对话

1. 系统会自动维护对话上下文
2. 可以在侧边栏查看当前对话ID
3. 点击"新对话"按钮可以开始新的对话

### 4. 系统设置

在侧边栏可以调整：
- **相似度阈值**: 控制范围判断的严格程度
- **最大检索结果**: 每次检索返回的文档片段数量

## 项目结构

```
rag-document-qa/
├── backend/                    # 后端FastAPI服务
│   ├── app/                   # 应用代码
│   │   ├── api/              # API端点
│   │   ├── core/             # 配置、异常、工具
│   │   ├── models/           # 数据模型
│   │   ├── services/         # 业务服务
│   │   └── utils/            # 工具函数
│   ├── tests/                # 测试代码
│   └── requirements.txt      # Python依赖
├── frontend/                  # 前端应用
│   ├── app.py               # Streamlit主应用
│   ├── components/           # UI组件
│   ├── utils/               # 工具函数
│   └── requirements.txt     # Python依赖
├── config/                   # 配置文件
├── data/                    # 数据存储
└── docker-compose.yml       # Docker编排
```

## API接口

### 主要端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/documents/upload` | POST | 上传文档 |
| `/api/v1/query` | POST | 查询文档 |
| `/api/v1/conversations/{id}` | GET | 获取对话历史 |
| `/api/v1/conversations/{id}` | DELETE | 删除对话 |
| `/api/v1/stats` | GET | 获取系统统计 |
| `/health` | GET | 健康检查 |

详细API文档请访问：http://localhost:8000/docs

## 开发指南

### 运行测试

```bash
# 运行所有测试
make test

# 设置测试环境
make test-env

# 清理测试数据
make test-clean
```

详细的测试指南请参考 [TESTING.md](TESTING.md)

### 测试覆盖
- **API测试**: 验证所有API端点的正确性
- **服务测试**: 测试核心业务逻辑
- **集成测试**: 验证组件间协作

### 代码规范

- 使用Black进行代码格式化
- 使用isort进行导入排序
- 使用mypy进行类型检查

## 部署指南

### Docker部署

```bash
# 构建并启动所有服务
make docker-up

# 查看日志
make docker-logs

# 停止服务
make docker-down
```

## 故障排除

### 常见问题

1. **文档上传失败**
   - 检查文件大小是否超过限制
   - 确认文件格式是否支持
   - 查看后端日志获取详细错误信息

2. **回答质量不佳**
   - 调整相似度阈值
   - 优化文档分割参数
   - 检查文档内容质量

## 许可证

本项目采用MIT许可证。

## 更新日志

### v1.0.0 (2026-04-07)
- 初始版本发布
- 支持多格式文档上传
- 实现智能范围判断
- 支持多轮对话
- 提供完整的API接口
- 开发Streamlit前端界面
- 支持Docker容器化部署