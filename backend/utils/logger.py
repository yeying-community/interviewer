"""
日志配置模块 - 提供统一的日志记录功能，支持rotation
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path


def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """
    配置并返回logger实例

    Args:
        name: logger名称，通常使用模块名 __name__
        log_file: 日志文件路径，如果为None则使用默认路径
        level: 日志级别，默认为INFO（生产环境推荐）

    Returns:
        配置好的logger实例
    """
    # 创建logger
    logger = logging.getLogger(name)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 创建日志目录
    if log_file is None:
        log_dir = Path(__file__).parent.parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / 'interviewer.log'
    else:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件处理器 - 带rotation
    # maxBytes=10MB, backupCount=5 表示最多保留5个备份文件
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # 控制台只显示INFO及以上级别
    console_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str):
    """
    获取logger实例的便捷方法

    Args:
        name: logger名称，建议使用 __name__

    Returns:
        logger实例
    """
    return setup_logger(name)
