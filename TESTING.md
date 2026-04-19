# RAG系统测试指南

## 测试配置

### 环境要求
- Python 3.9-3.11（推荐3.11，避免Python 3.14与pydantic v1的兼容性问题）
- Docker和Docker Compose（用于集成测试）
- DeepSeek API密钥（测试中使用mock，但需要占位符）

### 测试结构
```
backend/tests/
├── test_api.py           # API端点测试
├── test_services.py      # 核心服务测试
└── conftest.py          # 测试配置和共享fixture
```

### 运行测试

#### 1. 设置测试环境
```bash
# 复制测试环境配置
cp .env.test .env

# 安装依赖
cd backend && pip install -r requirements.txt
```

#### 2. 运行所有测试
```bash
# 使用Makefile
make test

# 或直接运行pytest
cd backend && pytest tests/ -v
```

#### 3. 运行特定测试
```bash
# 运行API测试
cd backend && pytest tests/test_api.py -v

# 运行服务测试
cd backend && pytest tests/test_services.py -v

# 运行单个测试类
cd backend && pytest tests/test_api.py::TestHealthEndpoints -v
```

#### 4. 测试覆盖率
```bash
cd backend && pytest tests/ --cov=app --cov-report=html
```

## 测试说明

### 模拟策略
测试使用`unittest.mock`模拟外部依赖：
- **DeepSeek API**：模拟HTTP请求，避免实际API调用
- **ChromaDB**：模拟向量存储操作
- **文档处理器**：模拟文件解析

### 测试覆盖范围

#### API测试 (`test_api.py`)
1. **健康检查端点** (`TestHealthEndpoints`)
   - 根端点返回系统信息
   - 健康检查端点返回服务状态

2. **文档端点** (`TestDocumentEndpoints`)
   - 文档上传成功（返回文档ID、分块数等）
   - 带对话ID的文档上传

3. **查询端点** (`TestQueryEndpoints`)
   - 文档查询成功（返回答案、对话ID、搜索结果）
   - 超出范围查询（返回婉拒回答）

4. **对话端点** (`TestConversationEndpoints`)
   - 获取对话历史
   - 删除对话

5. **统计端点** (`TestStatsEndpoint`)
   - 获取系统统计信息

#### 服务测试 (`test_services.py`)
1. **DeepSeek客户端** (`TestDeepSeekClient`)
   - 生成聊天补全
   - 生成嵌入向量
   - 范围判断逻辑

2. **文档处理器** (`TestDocumentProcessor`)
   - PDF文档处理
   - 文本分块逻辑

3. **向量存储** (`TestVectorStore`)
   - 添加文档到向量库
   - 相似性搜索

4. **对话管理器** (`TestConversationManager`)
   - 创建对话
   - 添加消息
   - TTL过期清理

5. **RAG引擎** (`TestRAGEngine`)
   - 文档上传处理
   - 范围内查询处理
   - 范围外查询处理

### 测试数据
测试使用独立的测试数据目录 (`test_data/`)：
- `test_data/chroma_db/` - 测试向量存储
- `test_data/uploads/` - 测试上传文件
- `test_data/logs/` - 测试日志

### 环境变量
测试使用`.env.test`配置文件，包含：
- 测试API密钥（`test_key`）
- 较小的文件大小限制（10MB）
- 较短的对话TTL（300秒）
- 较低的相似度阈值（0.5）

## Docker测试

### 启动测试环境
```bash
# 构建并启动所有服务
docker-compose up -d --build

# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 停止测试环境
```bash
docker-compose down
```

### 在容器内运行测试
```bash
# 进入后端容器
docker-compose exec backend bash

# 在容器内运行测试
cd /app && pytest tests/ -v
```

## 故障排除

### 常见问题

#### 1. 导入错误（chromadb/pydantic兼容性）
**问题**：Python 3.14与pydantic v1不兼容
**解决方案**：使用Python 3.9-3.11版本

#### 2. 测试依赖缺失
**问题**：缺少pytest或其他测试依赖
**解决方案**：
```bash
pip install pytest pytest-asyncio pytest-mock
```

#### 3. 环境变量未设置
**问题**：测试需要API密钥占位符
**解决方案**：
```bash
cp .env.test .env
# 编辑.env文件，设置DEEPSEEK_API_KEY（测试中使用mock，但仍需占位符）
```

#### 4. 测试数据目录权限
**问题**：无法创建测试数据目录
**解决方案**：
```bash
mkdir -p test_data/chroma_db test_data/uploads test_data/logs
chmod 755 test_data/
```

### 调试测试
```bash
# 详细输出
pytest tests/ -v --tb=long

# 仅显示失败测试
pytest tests/ -x

# 调试特定测试
pytest tests/test_api.py::TestHealthEndpoints::test_root_endpoint -v --capture=no
```

## 持续集成建议

### GitHub Actions配置示例
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v
```

## 性能测试

### 基准测试
```bash
# 运行性能测试（如果存在）
cd backend && pytest tests/ -m performance -v
```

### 负载测试建议
1. 使用`locust`进行API负载测试
2. 测试文档上传并发处理
3. 测试查询响应时间
4. 测试内存使用情况

## 安全测试

### 建议测试项
1. 文件上传安全（文件类型、大小限制）
2. API端点认证（如果实现）
3. SQL注入防护（如果使用数据库）
4. XSS防护（前端渲染）

## 扩展测试

### 添加新测试
1. 在相应测试文件中添加测试类或方法
2. 使用适当的mock和fixture
3. 确保测试独立且可重复
4. 添加清晰的测试文档

### 测试命名约定
- 测试类：`Test{ComponentName}`
- 测试方法：`test_{scenario}_{expected_result}`
- Fixture：`{resource_name}`

### 测试最佳实践
1. 每个测试只测试一个功能
2. 使用setup和teardown管理测试状态
3. 避免测试间依赖
4. 使用assert语句明确期望结果
5. 包含错误场景测试