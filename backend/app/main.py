from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
from loguru import logger
import sys

from backend.app.api.endpoints import router as api_router
from backend.app.core.config import settings


# 配置日志
def setup_logging():
    """配置日志"""
    logger.remove()  # 移除默认处理器

    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )

    # 添加文件处理器
    logger.add(
        settings.LOG_FILE if hasattr(settings, 'LOG_FILE') else "data/logs/app.log",
        rotation="10 MB",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        compression="zip"
    )

    logger.info("日志系统已初始化")


# 创建FastAPI应用
def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title=settings.APP_NAME,
        description="基于DeepSeek的RAG智能文档问答系统API",
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None
    )

    # 配置中间件
    setup_middleware(app)

    # 配置路由
    setup_routes(app)

    # 配置事件处理器
    setup_events(app)

    return app


def setup_middleware(app: FastAPI):
    """配置中间件"""
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 可信主机中间件
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if settings.DEBUG else ["localhost", "127.0.0.1"]
    )


def setup_routes(app: FastAPI):
    """配置路由"""
    # API路由
    app.include_router(
        api_router,
        prefix="/api/v1",
        tags=["API"]
    )

    # 根路由
    @app.get("/", tags=["根"])
    async def root():
        return {
            "message": "欢迎使用RAG智能文档问答系统API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/health"
        }

    # 健康检查路由
    @app.get("/health", tags=["健康检查"])
    async def health():
        from backend.app.api.endpoints import health_check
        return await health_check()


def setup_events(app: FastAPI):
    """配置事件处理器"""
    @app.on_event("startup")
    async def startup_event():
        """启动事件"""
        logger.info("=" * 50)
        logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"环境: {'开发' if settings.DEBUG else '生产'}")
        logger.info(f"服务器: {settings.HOST}:{settings.PORT}")
        logger.info(f"日志级别: {settings.LOG_LEVEL}")
        logger.info(f"DeepSeek模型: {settings.DEEPSEEK_MODEL}")
        logger.info(f"向量存储: {settings.CHROMA_PERSIST_DIRECTORY}")
        logger.info("=" * 50)

        # 检查必要的配置
        if not settings.DEEPSEEK_API_KEY:
            logger.warning("DeepSeek API密钥未设置，部分功能可能无法使用")

        # 初始化服务
        try:
            # 这里可以初始化一些服务
            logger.info("服务初始化完成")
        except Exception as e:
            logger.error(f"服务初始化失败: {e}")

    @app.on_event("shutdown")
    async def shutdown_event():
        """关闭事件"""
        logger.info("正在关闭应用...")
        # 清理资源
        logger.info("应用已关闭")


# 创建应用实例
app = create_app()

# 配置日志
setup_logging()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )