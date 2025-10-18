"""
统一配置管理模块
采用单例模式，集中管理所有配置项
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """应用配置类（单例模式）"""

    _instance: Optional['Config'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化配置（仅执行一次）"""
        if self._initialized:
            return

        # Flask配置
        self.SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-please-change-in-production')
        self.FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

        # 数据库配置
        self.DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/yeying_interviewer.db')

        # Qwen API配置
        self.QWEN_BASE_URL = os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.QWEN_API_KEY = os.getenv('QWEN_API_KEY') or os.getenv('API_KEY')
        self.MODEL_NAME = os.getenv('MODEL_NAME', 'qwen-turbo')

        # MinerU API配置
        self.MINERU_API_KEY = os.getenv('MINERU_API_KEY')
        self.MINERU_API_URL = os.getenv('MINERU_API_URL', 'https://mineru.net/api/v4')

        # MinIO配置
        self.MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'test-minio.yeying.pub')
        self.MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
        self.MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
        self.MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'yeying-interviewer')
        self.MINIO_SECURE = os.getenv('MINIO_SECURE', 'true').lower() == 'true'

        # DigitalHub配置
        self.PUBLIC_HOST = os.getenv('PUBLIC_HOST')
        self.LLM_PORT = int(os.getenv('LLM_PORT', '8011'))

        # 应用配置
        self.APP_HOST = os.getenv('APP_HOST', '0.0.0.0')
        self.APP_PORT = int(os.getenv('APP_PORT', '8080'))

        self._initialized = True

    def validate(self) -> tuple[bool, list[str]]:
        """
        验证必需的配置项

        Returns:
            (is_valid, missing_configs): 是否有效，缺失的配置列表
        """
        missing = []

        # 必需的配置项
        required_configs = {
            'QWEN_API_KEY': self.QWEN_API_KEY,
            'MINIO_ACCESS_KEY': self.MINIO_ACCESS_KEY,
            'MINIO_SECRET_KEY': self.MINIO_SECRET_KEY,
        }

        for name, value in required_configs.items():
            if not value:
                missing.append(name)

        return len(missing) == 0, missing

    def get_minio_config(self) -> dict:
        """获取MinIO配置字典"""
        return {
            'endpoint': self.MINIO_ENDPOINT,
            'access_key': self.MINIO_ACCESS_KEY,
            'secret_key': self.MINIO_SECRET_KEY,
            'bucket': self.MINIO_BUCKET,
            'secure': self.MINIO_SECURE,
        }

    def get_qwen_config(self) -> dict:
        """获取Qwen配置字典"""
        return {
            'api_key': self.QWEN_API_KEY,
            'base_url': self.QWEN_BASE_URL,
            'model_name': self.MODEL_NAME,
        }

    def get_database_config(self) -> dict:
        """获取数据库配置字典"""
        return {
            'path': self.DATABASE_PATH,
        }


# 全局配置实例
config = Config()
