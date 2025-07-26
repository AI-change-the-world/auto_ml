import logging
import os
from logging.handlers import RotatingFileHandler

# 创建 logs 目录
if not os.path.exists("logs"):
    os.mkdir("logs")

# 配置日志系统
log_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

log_file = "logs/app.log"

# 设置滚动日志：最大 5MB，最多保留 5 个文件
file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handler.setFormatter(log_formatter)

# 获取 FastAPI 的 logger 或创建你自己的 logger
logger = logging.getLogger("ai_platform")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.propagate = False  # 避免重复日志

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)
