from typing import TypedDict, Optional
import json

from core.infrastructure import BaseLLMClient, LLMInput
from utils.logger import get_logger

logger = get_logger(__name__)

class AlignmentInput(TypedDict):
    """对齐校验输入数据类型。"""
    decision: str           # 意识层生成的决策
    root_goal: str          # 根目标
    current_milestone: str  # 当前里程碑子目标
    alignment_threshold: int = 90  # 对齐阈值（0-100）

class AlignmentOutput(TypedDict):
    """对齐校验输出数据类型。"""
    success: bool
    alignment_score: int  # 对齐度得分
    is_aligned: bool      # 是否通过校验
    correction_hint: Optional[str] = None  # 修正提示（轻度跑偏时）
    error_msg: Optional[str] = None

class AttentionController:
    """注意力控制器。"""
    def __init__(self, llm_client: BaseLLMClient):
        """初始化 AttentionController。

        Args:
            llm_client: LLM 客户端实例，用于对齐度评分
        """
        self.llm_client = llm_client

    def check_alignment(self, input_data: AlignmentInput) -> AlignmentOutput:
        """执行对齐度校验，返回判定结果与修正提示"""
        try:
            logger.info("目标对齐校验开始")
            
            # 构建系统提示词
            system_prompt = """你是目标对齐校验器，需从3个维度评分：
            1. 决策与根目标的关联度（0-100，权重60%）
            2. 决策与当前里程碑的匹配度（0-100，权重30%）
            3. 是否存在无效动作（0-100，权重10%，无无效动作为100）
            综合得分 = 关联度 * 0.6 + 里程碑匹配度 * 0.3 + 无效动作评分 * 0.1
            请输出JSON格式：{"score": 综合得分, "reason": "评分理由"}"""
            
            # 构建用户提示词
            user_prompt = f"根目标：{input_data['root_goal']}\n当前里程碑：{input_data['current_milestone']}\n待校验决策：{input_data['decision']}"
            
            # 调用 LLM
            llm_output = self.llm_client.call(LLMInput(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                json_schema={"type": "object"},
                temperature=0.1
            ))
            
            if not llm_output["success"]:
                raise Exception(llm_output["error_msg"])
            
            # 解析 LLM 输出
            result = json.loads(llm_output["content"])
            score = int(result.get("score", 0))
            alignment_threshold = input_data.get("alignment_threshold", 90)
            is_aligned = score >= alignment_threshold
            correction_hint = None if is_aligned else f"决策对齐度不足（{score}分），请参考：{result.get('reason', '')}"
            
            logger.info(f"目标对齐校验完成，得分：{score}，通过：{is_aligned}")
            return {
                "success": True,
                "alignment_score": score,
                "is_aligned": is_aligned,
                "correction_hint": correction_hint,
                "error_msg": None
            }
        except Exception as e:
            logger.error(f"目标对齐校验失败: {str(e)}")
            return {
                "success": False,
                "alignment_score": 0,
                "is_aligned": False,
                "correction_hint": "请重新生成与目标对齐的决策",
                "error_msg": str(e)
            }