"""
DigitalHub数字人服务客户端
"""

import os
from typing import Optional, Dict, Any
import requests
from backend.common.logger import get_logger

logger = get_logger(__name__)

DIGITALHUB_BASE = os.getenv("DIGITALHUB_BASE", "http://127.0.0.1:9009")


def ping_dh() -> Dict[str, Any]:
    """Ping数字人服务"""
    try:
        r = requests.get(f"{DIGITALHUB_BASE}/api/v1/dh/ping", timeout=3)
        r.raise_for_status()
        data = r.json()
        logger.info(f"DH ping: {data}")
        return data
    except Exception as e:
        logger.warning(f"DH ping failed: {e}")
        return {"code": 500, "data": {"running": False, "error": str(e)}}


def boot_dh(room_id: str, session_id: str, timeout_sec: int = 90,
            public_host: Optional[str] = None) -> Dict[str, Any]:
    """启动数字人服务"""
    payload = {"room_id": room_id, "session_id": session_id, "timeout_sec": timeout_sec}
    if public_host:
        payload["public_host"] = public_host
    r = requests.post(f"{DIGITALHUB_BASE}/api/v1/dh/boot", json=payload, timeout=timeout_sec + 10)
    r.raise_for_status()
    data = r.json()
    logger.info(f"DH boot: {data}")
    return data


def start_llm(session_id: str, round_index: int, *,
              port: int,
              minio_endpoint: str, minio_access_key: str, minio_secret_key: str,
              minio_bucket: str, minio_secure: bool = True) -> Dict[str, Any]:
    """启动LLM服务"""
    payload = {
        "session_id": session_id,
        "round_index": round_index,
        "port": port,
        "minio_endpoint": minio_endpoint,
        "minio_access_key": minio_access_key,
        "minio_secret_key": minio_secret_key,
        "minio_bucket": minio_bucket,
        "minio_secure": minio_secure,
    }
    r = requests.post(f"{DIGITALHUB_BASE}/api/v1/dh/llm/start", json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    logger.info(f"LLM start: {data}")
    return data
