from dataclasses import dataclass
from typing import TypedDict, Optional, List
import os

from utils.logger import get_logger
from utils.storage import read_json_file, write_json_file

logger = get_logger(__name__)

@dataclass
class SelfCognition:
    """自我认知数据类。"""
    role: str          # 角色定位
    core_abilities: str  # 核心能力
    behavior_rules: str  # 行为准则
    prohibitions: str   # 禁止项

class SelfCognitionInput(TypedDict):
    """自我认知输入数据类型。"""
    cognition_data: SelfCognition  # 初始化/更新的认知数据

class SelfCognitionOutput(TypedDict):
    """自我认知输出数据类型。"""
    success: bool
    cognition: Optional[SelfCognition] = None
    error_msg: Optional[str] = None

class SelfCognitionManager:
    """自我认知管理器。"""
    def __init__(self, storage_path: str = "data/self_cognition.json"):
        """初始化 SelfCognitionManager。

        Args:
            storage_path: 自我认知数据的存储路径
        """
        self.storage_path = storage_path
        self._cognition: Optional[SelfCognition] = None  # 内部私有变量，只读
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

    def load(self) -> SelfCognitionOutput:
        """从本地文件加载自我认知，仅启动时调用一次"""
        try:
            data = read_json_file(self.storage_path)
            if data:
                self._cognition = SelfCognition(**data)
            else:
                # 默认认知模板
                self._cognition = SelfCognition(
                    role="专注于长任务稳定执行的AI助手",
                    core_abilities="文本处理、基础代码执行",
                    behavior_rules="严格遵循目标，不做无关操作",
                    prohibitions="不编造信息，不执行高危命令"
                )
                self._save(self._cognition)
            logger.info("自我认知加载成功")
            return {"success": True, "cognition": self._cognition, "error_msg": None}
        except Exception as e:
            logger.error(f"自我认知加载失败: {str(e)}")
            return {"success": False, "cognition": None, "error_msg": str(e)}

    def get(self) -> SelfCognition:
        """获取当前自我认知，只读接口，无修改权限"""
        if self._cognition is None:
            raise ValueError("自我认知未初始化，请先调用load()")
        return self._cognition

    def _save(self, cognition: SelfCognition) -> SelfCognitionOutput:
        """私有方法：保存认知数据，仅初始化/用户明确更新时调用"""
        try:
            data = {
                "role": cognition.role,
                "core_abilities": cognition.core_abilities,
                "behavior_rules": cognition.behavior_rules,
                "prohibitions": cognition.prohibitions
            }
            success = write_json_file(self.storage_path, data)
            if success:
                logger.info("自我认知保存成功")
                return {"success": True, "cognition": cognition, "error_msg": None}
            else:
                logger.error("自我认知保存失败")
                return {"success": False, "cognition": None, "error_msg": "保存失败"}
        except Exception as e:
            logger.error(f"自我认知保存失败: {str(e)}")
            return {"success": False, "cognition": None, "error_msg": str(e)}

class ContextContinuumManager:
    """上下文连续体管理器。"""
    def __init__(self, storage_path: str = "data/context_continuum.json"):
        """初始化 ContextContinuumManager。

        Args:
            storage_path: 上下文连续体的存储路径
        """
        self.storage_path = storage_path
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)

    def load(self) -> List[str]:
        """加载上下文连续体。"""
        try:
            data = read_json_file(self.storage_path)
            if data:
                logger.info("上下文连续体加载成功")
                return data
            else:
                # 初始化空列表
                logger.info("上下文连续体初始化空列表")
                return []
        except Exception as e:
            logger.error(f"上下文连续体加载失败: {str(e)}")
            return []

    def append(self, content: str) -> bool:
        """追加写入上下文连续体。"""
        try:
            # 先加载现有数据
            data = self.load()
            # 追加新内容
            data.append(content)
            # 保存更新后的数据
            success = write_json_file(self.storage_path, data)
            if success:
                logger.info("上下文连续体追加成功")
                return True
            else:
                logger.error("上下文连续体追加失败")
                return False
        except Exception as e:
            logger.error(f"上下文连续体追加失败: {str(e)}")
            return False