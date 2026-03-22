"""日志配置"""
import logging
import sys
from typing import Optional


_loggers = {}


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """设置日志记录器"""
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)

    if level is None:
        level = "INFO"

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _loggers[name] = logger
    return logger
