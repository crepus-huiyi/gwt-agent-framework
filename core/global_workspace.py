from typing import TypedDict, Optional, List

from core.infrastructure import BaseLLMClient, LLMInput
from core.persistence import SelfCognition
from utils.logger import get_logger

logger = get_logger(__name__)

class GlobalWorkspaceInput(TypedDict):
    """全局工作空间输入数据类型。"""
    filtered_info: List[dict]  # 筛选后的核心信息
    root_goal: str           # 根目标
    current_milestone: str   # 当前里程碑
    self_cognition: SelfCognition  # 自我认知

class GlobalWorkspaceOutput(TypedDict):
    """全局工作空间输出数据类型。"""
    success: bool
    decision: Optional[str] = None  # 生成的决策
    error_msg: Optional[str] = None

class GlobalWorkspace:
    """全局工作空间。"""
    def __init__(self, llm_client: BaseLLMClient):
        """初始化 GlobalWorkspace。

        Args:
            llm_client: LLM 客户端实例，用于生成决策
        """
        self.llm_client = llm_client

    def generate_decision(self, input_data: GlobalWorkspaceInput) -> GlobalWorkspaceOutput:
        """基于筛选后的核心信息生成全局决策"""
        try:
            logger.info("意识层开始生成决策")
            
            # 构建核心信息字符串
            core_info_str = "\n".join([info["content"] for info in input_data["filtered_info"]])
            
            # 构建系统提示词
            system_prompt = f"""你是一个基于全局工作空间理论的意识决策中心，需要基于核心信息生成与根目标对齐的决策。

            自我认知：
            - 角色：{input_data["self_cognition"].role}
            - 核心能力：{input_data["self_cognition"].core_abilities}
            - 行为准则：{input_data["self_cognition"].behavior_rules}
            - 禁止项：{input_data["self_cognition"].prohibitions}

            决策生成规则：
            1. 严格基于提供的核心信息，不编造事实
            2. 决策必须与根目标和当前里程碑对齐
            3. 决策要具体、可执行，明确下一步动作
            4. 避免无效动作，专注于任务目标

            请生成一个清晰、具体的决策，描述下一步应该采取的行动。"""
            
            # 构建用户提示词
            user_prompt = f"根目标：{input_data['root_goal']}\n当前里程碑：{input_data['current_milestone']}\n\n核心信息：\n{core_info_str}"
            
            # 调用 LLM
            llm_output = self.llm_client.call(LLMInput(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            ))
            
            if not llm_output["success"]:
                raise Exception(llm_output["error_msg"])
            
            decision = llm_output["content"].strip()
            logger.info("意识层决策生成成功")
            return {"success": True, "decision": decision, "error_msg": None}
        except Exception as e:
            logger.error(f"意识层决策生成失败: {str(e)}")
            return {"success": False, "decision": None, "error_msg": str(e)}