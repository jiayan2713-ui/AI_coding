import httpx
import json
from typing import Dict, List, Any, Optional
from loguru import logger
from pydantic import BaseModel, Field
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
import certifi


class DeepSeekConfig(BaseModel):
    """DeepSeek配置模型"""
    api_key: str
    base_url: str = "https://api.deepseek.com"
    chat_model: str = "deepseek-chat"
    timeout: int = 30
    max_retries: int = 3




class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str
    total_tokens: int


class ScopeCheckResponse(BaseModel):
    """范围检查响应模型"""
    is_in_scope: bool
    confidence: float
    reasoning: Optional[str] = None


class DeepSeekClient:
    """DeepSeek API客户端"""

    def __init__(self, config: DeepSeekConfig):
        self.config = config
        self.chat_headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }


    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> ChatResponse:
        """聊天补全"""
        url = f"{self.config.base_url}/v1/chat/completions"

        payload = {
            "model": self.config.chat_model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "top_p": kwargs.get("top_p", 0.9)
        }

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout, verify=certifi.where()) as client:
                response = await client.post(
                    url,
                    headers=self.chat_headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()

                return ChatResponse(
                    response=data["choices"][0]["message"]["content"],
                    total_tokens=data.get("usage", {}).get("total_tokens", 0)
                )

        except httpx.HTTPError as e:
            logger.error(f"聊天补全失败: {e}")
            raise
        except Exception as e:
            logger.error(f"处理聊天响应时发生错误: {e}")
            raise

    async def check_scope(self, question: str, context: str) -> ScopeCheckResponse:
        """检查问题是否在文档范围内"""
        prompt = f"""请判断以下问题是否可以根据提供的文档内容回答。

问题: {question}

相关文档内容:
{context}

请严格按照以下格式回答:
1. 如果问题可以根据文档内容回答，回答: IN_SCOPE
2. 如果问题无法根据文档内容回答，回答: OUT_OF_SCOPE
3. 给出置信度分数(0.0-1.0): CONFIDENCE: [分数]

只输出上述格式的内容，不要添加其他解释。"""

        messages = [
            {"role": "system", "content": "你是一个专业的文档范围判断助手。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.chat_completion(
                messages,
                temperature=0.1,
                max_tokens=100
            )

            # 解析响应
            lines = response.response.strip().split('\n')
            is_in_scope = False
            confidence = 0.0

            for line in lines:
                line = line.strip()
                if line.startswith("IN_SCOPE"):
                    is_in_scope = True
                elif line.startswith("OUT_OF_SCOPE"):
                    is_in_scope = False
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":")[1].strip())
                    except (ValueError, IndexError):
                        confidence = 0.0

            return ScopeCheckResponse(
                is_in_scope=is_in_scope,
                confidence=confidence,
                reasoning=response.response
            )

        except Exception as e:
            logger.error(f"范围检查失败: {e}")
            # 默认返回不在范围内
            return ScopeCheckResponse(
                is_in_scope=False,
                confidence=0.0,
                reasoning=f"范围检查失败: {str(e)}"
            )

    async def generate_out_of_scope_response(self, question: str) -> str:
        """生成超出范围的响应"""
        prompt = f"""用户提出了以下问题，但该问题不在已上传文档的范围内:
问题: {question}

请以友好、专业的方式告诉用户，这个问题无法基于当前文档回答。
建议用户可以:
1. 上传相关文档
2. 重新提问与文档相关的问题
3. 联系管理员获取帮助

请用中文回复，语气要友好、有帮助。"""

        messages = [
            {"role": "system", "content": "你是一个友好的文档问答助手。"},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.chat_completion(
                messages,
                temperature=0.3,
                max_tokens=300
            )
            return response.response
        except Exception as e:
            logger.error(f"生成超出范围响应失败: {e}")
            return "抱歉，这个问题不在当前文档的范围内。请上传相关文档或提问与文档相关的问题。"


# 工厂函数
def create_deepseek_client() -> DeepSeekClient:
    """创建DeepSeek客户端"""
    import os
    from dotenv import load_dotenv

    load_dotenv()

    config = DeepSeekConfig(
        api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        chat_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        timeout=int(os.getenv("DEEPSEEK_TIMEOUT", "30")),
        max_retries=int(os.getenv("DEEPSEEK_MAX_RETRIES", "3"))
    )

    return DeepSeekClient(config)