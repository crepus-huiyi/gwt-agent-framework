from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    """Agent核心状态，仅保留MVP必需字段"""
    # 对话与上下文
    messages: List[str]  # 全量临时对话历史
    # 目标相关
    root_goal: str  # 不可篡改的根目标
    current_milestone: str  # 当前里程碑子目标
    milestones_completed: List[str]  # 已完成的里程碑
    # 核心数据
    self_cognition_str: str  # 自我认知的字符串表示（只读）
    context_continuum: List[str]  # 上下文连续体（追加写）
    # 执行状态
    current_decision: Optional[str] = None  # 当前待校验决策
    alignment_score: Optional[int] = None  # 最新对齐度得分
    execution_result: Optional[str] = None  # 最新执行结果
    # 控制状态
    loop_count: int = 0  # 循环次数（防死循环）
    is_finished: bool = False  # 是否完成