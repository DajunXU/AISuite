import logging
import sys
import os
from typing import Any

from app.core.config import settings

LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

log_level = LOG_LEVEL_MAP.get(settings.LOG_LEVEL.upper(), logging.INFO)

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app.log")

logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8")
    ]
)

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)

class LoggerMixin:
    """日志 Mixin 类，方便在类中使用日志"""
    
    @property
    def logger(self) -> logging.Logger:
        name = f"{self.__class__.__module__}.{self.__class__.__name__}"
        return logging.getLogger(name)


def log_api_request(logger: logging.Logger, method: str, path: str, user: Any = None):
    """记录 API 请求"""
    user_info = f"user={user.username}" if user else "anonymous"
    logger.info(f"API Request: {method} {path} ({user_info})")

def log_error(logger: logging.Logger, error: Exception, context: str = ""):
    """记录错误日志"""
    context_msg = f" [{context}]" if context else ""
    logger.exception(f"Error{context_msg}: {type(error).__name__}: {str(error)}")

def log_llm_call(logger: logging.Logger, prompt: str, model: str):
    """记录 LLM 调用"""
    prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
    logger.info(f"LLM Call [{model}]: {prompt_preview}")
