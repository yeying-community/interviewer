#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yeying面试官系统 - Flask应用主入口

采用企业级架构，模块化设计
"""

import os
import sys
import shutil
from pathlib import Path
from flask import Flask
from typing import Tuple, List

# 添加项目路径以支持模块导入
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 导入配置和中间件
from backend.common.config import config
from backend.common.middleware import error_handler, request_logger
from backend.models.models import init_database
from backend.common.logger import get_logger

# 导入所有控制器
from backend.controllers.room_controller import room_bp
from backend.controllers.session_controller import session_bp
from backend.controllers.question_controller import question_bp
from backend.controllers.report_controller import report_bp
from backend.controllers.resume_controller import resume_bp
from backend.controllers.api_controller import api_bp

logger = get_logger(__name__)


def create_app() -> Flask:
    """创建Flask应用实例"""
    app = Flask(__name__,
                template_folder='frontend/templates',
                static_folder='frontend/static')

    # 使用统一配置
    app.secret_key = config.SECRET_KEY

    # 注册蓝图（简单直接）
    app.register_blueprint(room_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(question_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(resume_bp)
    app.register_blueprint(api_bp)

    # 注册中间件
    error_handler(app)
    request_logger(app)

    return app


def init_app() -> None:
    """初始化应用和数据库"""
    # 验证配置
    is_valid, missing_configs = config.validate()
    if not is_valid:
        logger.error(f"Missing required configurations: {', '.join(missing_configs)}")
        logger.error("Please check your .env file and set all required environment variables")
        sys.exit(1)

    # 初始化数据库
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


if __name__ == '__main__':
    # 确保日志目录存在
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)

    # 初始化应用
    logger.info("Starting Yeying Interviewer System...")
    init_app()

    # 创建Flask应用
    app = create_app()

    # 配置Flask/Werkzeug的日志也输出到文件
    import logging
    from logging.handlers import RotatingFileHandler

    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_handler = RotatingFileHandler(
        logs_dir / 'interviewer.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    werkzeug_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    werkzeug_handler.setFormatter(werkzeug_formatter)
    werkzeug_logger.addHandler(werkzeug_handler)

    # 启动应用
    logger.info(f"Server running on http://{config.APP_HOST}:{config.APP_PORT}")
    logger.info(f"Debug mode: {config.FLASK_DEBUG}")
    app.run(
        host=config.APP_HOST,
        port=config.APP_PORT,
        debug=config.FLASK_DEBUG
    )
