import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from loguru import logger
import asyncio


class Message(BaseModel):
    """消息模型"""
    role: str  # "user" 或 "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationHistory(BaseModel):
    """对话历史模型"""
    conversation_id: str
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    document_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationManager:
    """对话管理器"""

    def __init__(self, max_history: int = 10, ttl_hours: int = 1):
        self.max_history = max_history
        self.ttl_hours = ttl_hours
        self.conversations: Dict[str, ConversationHistory] = {}
        self._cleanup_task = None

        # 启动定期清理任务
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """启动过期对话清理任务"""
        async def cleanup():
            while True:
                await asyncio.sleep(3600)  # 每小时清理一次
                await self._cleanup_expired_conversations()

        # 仅在asyncio事件循环中启动
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._cleanup_task = asyncio.create_task(cleanup())
        except:
            # 没有事件循环，不启动清理任务
            pass

    async def _cleanup_expired_conversations(self):
        """清理过期对话"""
        expired_count = 0
        now = datetime.now()
        expired_ids = []

        for conv_id, conversation in self.conversations.items():
            if now - conversation.updated_at > timedelta(hours=self.ttl_hours):
                expired_ids.append(conv_id)

        for conv_id in expired_ids:
            del self.conversations[conv_id]
            expired_count += 1

        if expired_count > 0:
            logger.info(f"清理了 {expired_count} 个过期对话")

    def create_conversation(self, document_ids: Optional[List[str]] = None,
                           conversation_id: Optional[str] = None) -> str:
        """创建新对话

        Args:
            document_ids: 关联的文档ID列表
            conversation_id: 可选的对话ID，如果不提供则生成新的UUID

        Returns:
            对话ID
        """
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        # 检查对话是否已存在
        if conversation_id in self.conversations:
            logger.debug(f"对话已存在: {conversation_id}")
            return conversation_id

        conversation = ConversationHistory(
            conversation_id=conversation_id,
            document_ids=document_ids or [],
            metadata={
                "max_history": self.max_history,
                "created_at": datetime.now().isoformat()
            }
        )

        self.conversations[conversation_id] = conversation
        logger.info(f"创建新对话: {conversation_id}")

        return conversation_id

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """添加消息到对话"""
        if conversation_id not in self.conversations:
            logger.warning(f"对话不存在: {conversation_id}")
            return False

        conversation = self.conversations[conversation_id]

        # 创建消息
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )

        # 添加到对话
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()

        # 限制历史消息数量
        if len(conversation.messages) > self.max_history:
            # 保留最新的 max_history 条消息
            conversation.messages = conversation.messages[-self.max_history:]

        logger.debug(f"添加消息到对话 {conversation_id}: {role} - {content[:50]}...")
        return True

    async def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """获取对话历史"""
        if conversation_id not in self.conversations:
            return None

        conversation = self.conversations[conversation_id]

        # 更新最后访问时间
        conversation.updated_at = datetime.now()

        return conversation

    async def get_conversation_messages(self, conversation_id: str) -> List[Message]:
        """获取对话消息列表"""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return []

        return conversation.messages

    async def get_latest_messages(
        self,
        conversation_id: str,
        limit: int = 5
    ) -> List[Message]:
        """获取最新的N条消息"""
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return []

        return conversation.messages[-limit:]

    async def get_conversation_context(
        self,
        conversation_id: str,
        max_tokens: int = 2000
    ) -> str:
        """获取对话上下文（用于模型输入）"""
        messages = await self.get_conversation_messages(conversation_id)
        if not messages:
            return ""

        # 构建上下文文本
        context_parts = []
        current_tokens = 0

        # 从最新消息开始，直到达到token限制
        for message in reversed(messages):
            message_text = f"{message.role}: {message.content}"
            message_tokens = len(message_text.split())  # 简单估算

            if current_tokens + message_tokens > max_tokens:
                break

            context_parts.insert(0, message_text)
            current_tokens += message_tokens

        return "\n".join(context_parts)

    async def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话"""
        if conversation_id not in self.conversations:
            return False

        del self.conversations[conversation_id]
        logger.info(f"删除对话: {conversation_id}")
        return True

    async def update_conversation_metadata(
        self,
        conversation_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """更新对话元数据"""
        if conversation_id not in self.conversations:
            return False

        conversation = self.conversations[conversation_id]
        conversation.metadata.update(metadata)
        conversation.updated_at = datetime.now()

        return True

    async def add_document_to_conversation(
        self,
        conversation_id: str,
        document_id: str
    ) -> bool:
        """添加文档到对话"""
        if conversation_id not in self.conversations:
            return False

        conversation = self.conversations[conversation_id]

        if document_id not in conversation.document_ids:
            conversation.document_ids.append(document_id)
            conversation.updated_at = datetime.now()

        return True

    async def get_all_conversations(self) -> List[ConversationHistory]:
        """获取所有对话"""
        return list(self.conversations.values())

    async def get_conversation_count(self) -> int:
        """获取对话数量"""
        return len(self.conversations)

    async def cleanup_old_conversations(self, max_age_hours: int = 24):
        """清理超过指定年龄的对话"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_ids = []

        for conv_id, conversation in self.conversations.items():
            if conversation.updated_at < cutoff_time:
                old_ids.append(conv_id)

        for conv_id in old_ids:
            await self.delete_conversation(conv_id)

        if old_ids:
            logger.info(f"清理了 {len(old_ids)} 个超过 {max_age_hours} 小时的旧对话")


# 工厂函数
def create_conversation_manager() -> ConversationManager:
    """创建对话管理器实例"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    max_history = int(os.getenv("CONVERSATION_MAX_HISTORY", "10"))
    ttl_hours = int(os.getenv("CONVERSATION_TTL_HOURS", "1"))

    return ConversationManager(
        max_history=max_history,
        ttl_hours=ttl_hours
    )