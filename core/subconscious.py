from typing import TypedDict, Optional, List
import json

from core.infrastructure import BaseLLMClient, LLMInput
from utils.logger import get_logger

logger = get_logger(__name__)

class SubconsciousInput(TypedDict):
    """潜意识输入数据类型。"""
    full_context: List[str]  # 全量临时上下文
    root_goal: str           # 根目标（用于关联度判断）
    filter_threshold: int = 7  # 过滤阈值（0-10）

class FilteredInfo(TypedDict):
    """过滤后的信息数据类型。"""
    content: str  # 核心信息内容
    priority: int  # 优先级打分（0-10）
    relevance: float  # 与根目标的关联度

class SubconsciousOutput(TypedDict):
    """潜意识输出数据类型。"""
    success: bool
    filtered_info: Optional[List[FilteredInfo]] = None
    error_msg: Optional[str] = None

class SubconsciousProcessor:
    """潜意识处理器。"""
    def __init__(self, llm_client: BaseLLMClient):
        """初始化 SubconsciousProcessor。

        Args:
            llm_client: LLM 客户端实例，用于提取核心信息和优先级打分
        """
        self.llm_client = llm_client

    def process(self, input_data: SubconsciousInput) -> SubconsciousOutput:
        """执行并行过滤、提取、打分，返回筛选后的核心信息"""
        try:
            logger.info("潜意识层开始处理")
            # 1. 冗余剔除
            clean_context = self._remove_redundancy(input_data["full_context"])
            # 2. 核心信息提取
            core_info = self._extract_core_info(clean_context, input_data["root_goal"])
            # 3. 优先级打分
            ranked_info = self._rank_priority(core_info, input_data["root_goal"])
            # 4. 阈值过滤
            filtered = [info for info in ranked_info if info["priority"] >= input_data["filter_threshold"]]
            
            if not filtered:
                logger.warning("过滤后无有效信息，放宽阈值重试")
                filtered = [info for info in ranked_info if info["priority"] >= 5]
            
            logger.info(f"潜意识层处理完成，筛选出{len(filtered)}条核心信息")
            return {"success": True, "filtered_info": filtered, "error_msg": None}
        except Exception as e:
            logger.error(f"潜意识层处理失败: {str(e)}")
            return {"success": False, "filtered_info": None, "error_msg": str(e)}

    def _remove_redundancy(self, context: List[str]) -> List[str]:
        """私有方法：剔除冗余内容"""
        # 简单的冗余剔除逻辑，实际项目中可以更复杂
        seen = set()
        clean_context = []
        for item in context:
            # 去除空白字符
            item = item.strip()
            # 跳过空字符串
            if not item:
                continue
            # 跳过重复内容
            if item not in seen:
                seen.add(item)
                clean_context.append(item)
        logger.debug(f"冗余剔除前: {len(context)}条，剔除后: {len(clean_context)}条")
        return clean_context

    def _extract_core_info(self, context: List[str], goal: str) -> List[str]:
        """私有方法：基于 LLM 提取核心信息"""
        try:
            # 将上下文合并为一个字符串
            context_str = "\n".join(context)
            
            # 构建系统提示词
            system_prompt = """你是一个信息提取助手，需要从对话上下文中提取与目标强相关的核心信息。

            提取规则：
            1. 只提取与目标直接相关的信息
            2. 去除无关的寒暄、重复内容
            3. 提取的信息要简洁明了，突出关键点
            4. 每个核心信息单独一行

            请将提取的核心信息以列表形式返回。"""
            
            # 构建用户提示词
            user_prompt = f"目标：{goal}\n\n对话上下文：\n{context_str}"
            
            # 调用 LLM
            llm_output = self.llm_client.call(LLMInput(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.1
            ))
            
            if not llm_output["success"]:
                raise Exception(llm_output["error_msg"])
            
            # 解析 LLM 输出
            core_info = [line.strip() for line in llm_output["content"].split("\n") if line.strip()]
            logger.debug(f"提取核心信息: {core_info}")
            return core_info
        except Exception as e:
            logger.error(f"提取核心信息失败: {str(e)}")
            # 失败时返回原始上下文
            return context

    def _rank_priority(self, info_list: List[str], goal: str) -> List[FilteredInfo]:
        """私有方法：优先级打分"""
        try:
            ranked_info = []
            for info in info_list:
                # 构建系统提示词
                system_prompt = """你是一个优先级评估助手，需要评估信息与目标的关联度，并给出优先级打分。

                评估规则：
                1. 关联度：信息与目标的相关程度，0-10分
                2. 优先级：基于关联度，0-10分，与关联度一致

                请以 JSON 格式返回评估结果：
                {"priority": 打分, "relevance": 关联度}"""
                
                # 构建用户提示词
                user_prompt = f"目标：{goal}\n\n信息：{info}"
                
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
                priority = result.get("priority", 0)
                relevance = result.get("relevance", 0.0)
                
                ranked_info.append({
                    "content": info,
                    "priority": priority,
                    "relevance": relevance
                })
            
            # 按优先级排序
            ranked_info.sort(key=lambda x: x["priority"], reverse=True)
            logger.debug(f"优先级排序结果: {ranked_info}")
            return ranked_info
        except Exception as e:
            logger.error(f"优先级打分失败: {str(e)}")
            # 失败时返回默认优先级
            return [{
                "content": info,
                "priority": 5,
                "relevance": 0.5
            } for info in info_list]