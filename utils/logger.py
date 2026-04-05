import logging
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 日志格式：[时间] [级别] [模块名] 消息
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"

# 从环境变量获取日志级别，默认为 INFO
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# 配置根日志记录器
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S"
)

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器。

    Args:
        name: 日志记录器的名称，通常使用 __name__

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    return logging.getLogger(name)