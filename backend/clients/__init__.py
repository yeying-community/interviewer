"""
外部服务客户端模块

统一导出所有外部服务客户端
"""

# MinIO对象存储客户端
from .minio_client import minio_client, download_resume_data, upload_resume_data

# DigitalHub数字人服务客户端
from .digitalhub_client import ping_dh, boot_dh, start_llm

# MinerU PDF解析客户端
from .mineru_client import MinerUClient, get_mineru_client

__all__ = [
    # MinIO
    'minio_client',
    'download_resume_data',
    'upload_resume_data',

    # DigitalHub
    'ping_dh',
    'boot_dh',
    'start_llm',

    # MinerU
    'MinerUClient',
    'get_mineru_client',
]
