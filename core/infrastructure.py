from abc import ABC, abstractmethod
from typing import TypedDict, Optional
import os
import requests
from dotenv import load_dotenv

from utils.logger import get_logger

# 加载环境变量
load_dotenv()

logger = get_logger(__name__)

class LLMInput(TypedDict):
    """大模型输入数据类型。"""
    system_prompt: str  # 系统提示词
    user_prompt: str     # 用户输入
    json_schema: Optional[dict] = None  # 可选：强制输出的JSON Schema
    temperature: float = 0.7  # 温度参数

class LLMOutput(TypedDict):
    """大模型输出数据类型。"""
    success: bool  # 是否调用成功
    content: str   # 模型输出内容
    error_msg: Optional[str] = None  # 错误信息

class BaseLLMClient(ABC):
    """大模型客户端抽象基类，支持后续扩展不同模型"""
    @abstractmethod
    def call(self, input_data: LLMInput) -> LLMOutput:
        """调用大模型，返回统一格式结果"""
        pass

class OpenAIClient(BaseLLMClient):
    """OpenAI API兼容客户端（支持国内开源模型）"""
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model_name: Optional[str] = None):
        """初始化 OpenAIClient。

        Args:
            api_key: API 密钥，如果为 None 则从环境变量读取
            base_url: API 基础 URL，如果为 None 则从环境变量读取
            model_name: 模型名称，如果为 None 则从环境变量读取
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model_name = model_name or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

    def call(self, input_data: LLMInput) -> LLMOutput:
        """实现 OpenAI 格式的 API 调用，含重试逻辑"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": input_data["system_prompt"]},
                {"role": "user", "content": input_data["user_prompt"]}
            ],
            "temperature": input_data.get("temperature", 0.7)
        }
        
        # 如果指定了 json_schema，使用 JSON 模式
        if input_data.get("json_schema"):
            payload["response_format"] = {"type": "json_object"}

        for attempt in range(2):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                logger.info(f"LLM 调用成功，第{attempt+1}次尝试")
                return {"success": True, "content": content, "error_msg": None}
            except Exception as e:
                logger.warning(f"LLM 调用失败，第{attempt+1}次尝试，错误: {str(e)}")
                if attempt == 1:
                    return {"success": False, "content": "", "error_msg": str(e)}

# 工厂函数，用于创建 LLM 客户端
def create_llm_client() -> BaseLLMClient:
    """创建 LLM 客户端实例。

    Returns:
        BaseLLMClient: LLM 客户端实例
    """
    return OpenAIClient()