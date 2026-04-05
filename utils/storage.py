import json
import os
from typing import Any, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

def read_json_file(file_path: str) -> Optional[Any]:
    """从本地 JSON 文件读取数据。

    Args:
        file_path: JSON 文件的路径

    Returns:
        Optional[Any]: 读取的数据，如果文件不存在或读取失败返回 None
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"成功读取文件: {file_path}")
            return data
        else:
            logger.warning(f"文件不存在: {file_path}")
            return None
    except Exception as e:
        logger.error(f"读取文件失败: {file_path}, 错误: {str(e)}")
        return None

def write_json_file(file_path: str, data: Any) -> bool:
    """将数据写入本地 JSON 文件。

    Args:
        file_path: JSON 文件的路径
        data: 要写入的数据

    Returns:
        bool: 写入是否成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"成功写入文件: {file_path}")
        return True
    except Exception as e:
        logger.error(f"写入文件失败: {file_path}, 错误: {str(e)}")
        return False