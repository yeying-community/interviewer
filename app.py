#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yeying面试官系统 - Flask应用主入口

简洁的应用启动文件，所有业务逻辑已迁移到backend模块
"""

import os
import sys
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

# 添加项目路径以支持模块导入
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# 加载环境变量
load_dotenv()

# 导入后端模块
from backend.models.models import init_database
from backend.api.routes import main_bp, api_bp


def create_app():
    """创建Flask应用实例"""
    app = Flask(__name__, 
                template_folder='frontend/templates',
                static_folder='frontend/static')
    
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    return app


def init_app():
    """初始化应用和数据库"""
    # 初始化数据库
    init_database()
    print("✅ Database initialized")
    
    # 创建默认数据（如果需要）
    try:
        from backend.services.interview_service import RoomService
        rooms = RoomService.get_all_rooms()
        if not rooms:
            default_room = RoomService.create_room("默认面试间")
            print(f"✅ Created default room: {default_room.id}")
    except Exception as e:
        print(f"⚠️  Error creating default room: {e}")


if __name__ == '__main__':
    # 初始化应用
    init_app()
    
    # 创建Flask应用
    app = create_app()
    
    # 启动应用
    print("🚀 Starting Yeying Interviewer System...")
    app.run(host='0.0.0.0', port=8080, debug=True)