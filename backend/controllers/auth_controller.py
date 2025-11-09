# -*- coding:utf-8 -*-
from http.client import HTTPException

import connexion
from typing import Dict, Any, Optional
from backend.models.auth_challenge_request import AuthChallengeRequest  # noqa: E501
from backend.models.auth_verify_request import AuthVerifyRequest  # noqa: E501

from backend.models.auth_challenge_response import AuthChallengeResponse  # noqa: E501
from backend.models.auth_challenge_response_body import AuthChallengeResponseBody  # noqa: E501

from backend.models.auth_verify_response import AuthVerifyResponse
from backend.models.auth_verify_response_body import AuthVerifyResponseBody
from backend.models.common_response_status import CommonResponseStatus, CommonResponseCodeEnum  # noqa: E501
from pydantic import BaseModel
from jose import jwt
from eth_account.messages import encode_defunct
from eth_account import Account
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
import os
import time
import random
import string
from flask import request
from backend.common.response import ApiResponse
from backend.common.middleware import handle_exceptions
# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT 配置
JWT_SECRET = os.getenv("JWT_SECRET", "e802e988a02546cc47415e4bc76346aae7ceece97a0f950319c861a5de38b20d")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 1

# 模拟 Redis：存储 challenge（生产环境请替换为 Redis）
challenges: Dict[str, Dict[str, Any]] = {}

# 工具函数
def generate_random_string(length: int = 8) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def is_challenge_expired(timestamp_ms: int, ttl_minutes: int = 5) -> bool:
    now_ms = int(time.time() * 1000)
    return (now_ms - timestamp_ms) > (ttl_minutes * 60 * 1000)

@handle_exceptions
def auth_challenge(body):  # noqa: E501
    """获取挑战"""
    logger.info(f"authChallenge request.body={body}")
    address = body.get("body", {}).get("address")
    if not address:
        return ApiResponse.bad_request("address 字段不能为空")

    # 生成 challenge
    random_part = generate_random_string()
    challenge = f"请签名以登录 YeYing Wallet\n\n随机数: {random_part}\n时间戳: {int(time.time() * 1000)}"

    addr_key = address.lower()
    challenges[addr_key] = {
        "challenge": challenge,
        "timestamp": int(time.time() * 1000)
    }

    logger.info(f"Generated challenge for {addr_key}: {challenge}")
    return AuthChallengeResponse(body=AuthChallengeResponseBody(
        status=CommonResponseStatus(CommonResponseCodeEnum.OK),
        result=challenge
    ))


def auth_verify(body):  # noqa: E501
    """验证签名"""
    logger.info(f"authVerify request.body={body}")
    address = body.get("body", {}).get("address")
    signature = body.get("body", {}).get("signature")
    if not address or not signature:
        raise Exception(
            "param address or signature is None"
        )

    addr_key = address.lower()
    challenge_data = challenges.get(addr_key)

    if not challenge_data or is_challenge_expired(challenge_data["timestamp"]):
        challenges.pop(addr_key, None)
        raise Exception(
            "Challenge 不存在或已过期"
        )

    try:
        message = encode_defunct(text=challenge_data["challenge"])
        logger.info(f"authVerify message={message}")
        logger.info(f"authVerify signature={signature}")
        recovered_address = Account.recover_message(message, signature=signature)

        if recovered_address.lower() != addr_key:
            raise Exception(
                "签名验证失败"
            )

        challenges.pop(addr_key, None)

        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
        token = jwt.encode(
            {"sub": addr_key, "exp": expire},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )

        logger.info(f"Login successful for {addr_key}")
        return AuthVerifyResponse(body=AuthVerifyResponseBody(
            status=CommonResponseStatus(CommonResponseCodeEnum.OK),
            token=token
        ))

    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        raise Exception(
            f"authVerify failed: {str(e)}"
        )
