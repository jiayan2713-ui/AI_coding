.PHONY: help install setup run run-backend run-frontend test clean docker-up docker-down

help: ## 显示帮助信息
	@echo "可用命令:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## 安装所有依赖
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && pip install -r requirements.txt

setup: ## 初始化项目设置
	@echo "复制环境变量文件..."
	cp -n .env.example .env || true
	@echo "请编辑 .env 文件，设置您的DeepSeek API密钥"
	@echo "创建数据目录..."
	mkdir -p data/uploads data/chroma_db data/logs

run: run-backend run-frontend ## 同时启动后端和前端

run-backend: ## 启动后端服务
	@echo "启动后端服务 (FastAPI)..."
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

run-frontend: ## 启动前端服务
	@echo "启动前端服务 (Streamlit)..."
	cd frontend && streamlit run app.py --server.port 8501

test: ## 运行测试
	@echo "运行后端测试..."
	cd backend && python -m pytest tests/ -v

test-env: ## 设置测试环境
	@echo "设置测试环境..."
	cp -n .env.test .env || true
	@echo "创建测试数据目录..."
	mkdir -p test_data/chroma_db test_data/uploads test_data/logs

test-clean: ## 清理测试数据
	@echo "清理测试数据..."
	rm -rf test_data/

clean: ## 清理临时文件和数据
	@echo "清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "清理数据目录..."
	rm -rf data/uploads/* data/chroma_db/* data/logs/*

docker-up: ## 使用Docker Compose启动所有服务
	@echo "启动Docker服务..."
	docker-compose up -d --build

docker-down: ## 停止Docker服务
	@echo "停止Docker服务..."
	docker-compose down

docker-logs: ## 查看Docker日志
	docker-compose logs -f