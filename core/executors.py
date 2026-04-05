from abc import ABC, abstractmethod
from typing import TypedDict, Optional
import subprocess
import sys

from core.infrastructure import BaseLLMClient, LLMInput
from utils.logger import get_logger

logger = get_logger(__name__)

class ExecutionInput(TypedDict):
    """执行输入数据类型。"""
    action_type: str  # "text_process" 或 "code_execute"
    action_content: str  # 具体动作内容

class ExecutionOutput(TypedDict):
    """执行输出数据类型。"""
    success: bool
    result: Optional[str] = None
    error_msg: Optional[str] = None

class BaseExecutor(ABC):
    """执行器抽象基类"""
    @abstractmethod
    def execute(self, content: str) -> ExecutionOutput:
        """执行具体动作"""
        pass

class TextProcessor(BaseExecutor):
    """文本处理器。"""
    def __init__(self, llm_client: BaseLLMClient):
        """初始化 TextProcessor。

        Args:
            llm_client: LLM 客户端实例，用于文本处理
        """
        self.llm_client = llm_client

    def execute(self, content: str) -> ExecutionOutput:
        """执行文本处理"""
        try:
            logger.info("文本处理开始")
            
            # 构建系统提示词
            system_prompt = """你是一个文本处理助手，需要根据用户的请求处理文本内容。

            处理规则：
            1. 严格按照用户的请求进行处理
            2. 保持文本的准确性和完整性
            3. 处理结果要清晰、简洁

            请根据用户的请求处理文本内容。"""
            
            # 构建用户提示词
            user_prompt = content
            
            # 调用 LLM
            llm_output = self.llm_client.call(LLMInput(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            ))
            
            if not llm_output["success"]:
                raise Exception(llm_output["error_msg"])
            
            result = llm_output["content"].strip()
            logger.info("文本处理完成")
            return {"success": True, "result": result, "error_msg": None}
        except Exception as e:
            logger.error(f"文本处理失败: {str(e)}")
            return {"success": False, "result": None, "error_msg": str(e)}

class CodeExecutor(BaseExecutor):
    """代码执行器。"""
    def execute(self, content: str) -> ExecutionOutput:
        """执行代码"""
        try:
            logger.info("代码执行开始")
            
            # 简单的高危命令拦截
            dangerous_keywords = ["os.system", "subprocess", "shutil", "eval", "exec"]
            for kw in dangerous_keywords:
                if kw in content:
                    logger.warning(f"禁止执行高危命令：{kw}")
                    return {"success": False, "result": None, "error_msg": f"禁止执行高危命令：{kw}"}
            
            # 本地沙箱执行（简化版，生产环境需更严格隔离）
            result = subprocess.run(
                [sys.executable, "-c", content],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = result.stdout + result.stderr
            logger.info("代码执行成功")
            return {"success": True, "result": output, "error_msg": None}
        except Exception as e:
            logger.error(f"代码执行失败: {str(e)}")
            return {"success": False, "result": None, "error_msg": str(e)}

class ExecutionManager:
    """执行管理器。"""
    def __init__(self, text_processor: TextProcessor, code_executor: CodeExecutor):
        """初始化 ExecutionManager。

        Args:
            text_processor: 文本处理器实例
            code_executor: 代码执行器实例
        """
        self.executors = {
            "text_process": text_processor,
            "code_execute": code_executor
        }

    def run(self, input_data: ExecutionInput) -> ExecutionOutput:
        """执行具体动作"""
        try:
            action_type = input_data["action_type"]
            action_content = input_data["action_content"]
            
            if action_type not in self.executors:
                raise ValueError(f"不支持的动作类型: {action_type}")
            
            executor = self.executors[action_type]
            result = executor.execute(action_content)
            
            logger.info(f"执行完成，动作类型: {action_type}")
            return result
        except Exception as e:
            logger.error(f"执行失败: {str(e)}")
            return {"success": False, "result": None, "error_msg": str(e)}