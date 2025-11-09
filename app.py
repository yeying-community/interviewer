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
# 启动方式：使用 uvicorn 兼容的方式
import uvicorn
import connexion
from backend.utils import encoder

logger = get_logger(__name__)


def create_app() -> connexion.App:
    """创建Flask应用实例，并集成Connexion"""
    # 创建 Connexion App（它内部会创建一个 Flask app）
    specification_dir = str(project_root / 'backend/openapi')
    connex_app = connexion.App(__name__, specification_dir=specification_dir)

    # 设置 JSON 编码器
    connex_app.app.json.default = encoder.custom_json_default

    # 添加 API（这会自动注册 /ui, /openapi.json 等）
    connex_app.add_api(
        'openapi.yaml',
        arguments={'title': 'Yeying API'},
        pythonic_params=True,
        strict_validation=True,
        validate_responses=False
    )

    # 配置 Flask
    connex_app.app.secret_key = config.SECRET_KEY
    connex_app.app.template_folder = 'frontend/templates'
    connex_app.app.static_folder = 'frontend/static'

    # 注册你的蓝图
    connex_app.app.register_blueprint(room_bp)
    connex_app.app.register_blueprint(session_bp)
    connex_app.app.register_blueprint(question_bp)
    connex_app.app.register_blueprint(report_bp)
    connex_app.app.register_blueprint(resume_bp)
    connex_app.app.register_blueprint(api_bp)

    # 注册中间件
    error_handler(connex_app.app)
    request_logger(connex_app.app)

    return connex_app


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
    uvicorn.run(
        app,  # 注意：这里传的是内部的 ASGI app
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=config.FLASK_DEBUG,  # uvicorn 用 reload 代替 debug
        log_level="info"
    )
