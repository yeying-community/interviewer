import os
import logging
import requests

DIGITALHUB_BASE = os.getenv("DIGITALHUB_BASE", "http://127.0.0.1:9009")
log = logging.getLogger(__name__)

def ping_dh() -> dict:
    try:
        r = requests.get(f"{DIGITALHUB_BASE}/api/v1/dh/ping", timeout=3)
        r.raise_for_status()
        data = r.json()
        log.info("DH ping: %s", data)
        return data
    except Exception as e:
        log.warning("DH ping failed: %s", e)
        return {"code": 500, "data": {"running": False, "error": str(e)}}

def boot_dh(room_id: str, session_id: str, timeout_sec: int = 90, public_host: str | None = None) -> dict:
    payload = {"room_id": room_id, "session_id": session_id, "timeout_sec": timeout_sec}
    if public_host:
        payload["public_host"] = public_host
    r = requests.post(f"{DIGITALHUB_BASE}/api/v1/dh/boot", json=payload, timeout=timeout_sec + 10)
    r.raise_for_status()
    data = r.json()
    log.info("DH boot: %s", data)
    return data

def start_llm(session_id: str, round_index: int, *,
              port: int,
              minio_endpoint: str, minio_access_key: str, minio_secret_key: str,
              minio_bucket: str, minio_secure: bool = True) -> dict:
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
    log.info("LLM start: %s", data)
    return data
