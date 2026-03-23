import logging
import os
from logging.handlers import RotatingFileHandler

if not os.path.exists("logs"):
    os.mkdir("logs")

log_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

log_file = "logs/trainer.log"

file_handler = RotatingFileHandler(
    log_file, maxBytes=5 * 1024 * 1024, backupCount=5)
file_handler.setFormatter(log_formatter)

logger = logging.getLogger("model_trainer")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.propagate = False

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)
