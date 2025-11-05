"""
API控制器
提供RESTful API接口（GET/DELETE等）
"""

import hashlib
import hmac
import os
from datetime import datetime
from flask import Blueprint, request
from typing import Tuple
from backend.services.interview_service import (
    RoomService,
    SessionService,
    RoundService,
    RoundCompletionService
)
from backend.common.response import ApiResponse, ResponseCode
from backend.common.validators import validate_uuid_param
from backend.clients.minio_client import minio_client, download_resume_data
from backend.common.logger import get_logger

logger = get_logger(__name__)

# 创建API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')


def verify_signature(req) -> bool:
    """验证请求签名"""
    secret = os.getenv("WEBHOOK_SECRET")
    if not secret:
        logger.error("WEBHOOK_SECRET 未配置，无法验证签名")
        return False

    signature = req.headers.get('X-DH-Signature')
    if not signature:
        logger.warning("缺少 X-DH-Signature 请求头")
        return False

    body_bytes = req.get_data(cache=True)
    try:
        body_text = body_bytes.decode('utf-8')
    except UnicodeDecodeError:
        body_text = body_bytes.decode('utf-8', errors='replace')

    message = f"{req.method.upper()}{req.path}{body_text}".encode('utf-8')
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        logger.warning("签名验证失败: expected=%s, received=%s", expected_signature, signature)
        return False

    return True


# ==================== Room API ====================

@api_bp.route('/rooms', methods=['GET'])
def get_rooms() -> Tuple[dict, int]:
    """获取所有面试间"""
    try:
        rooms = RoomService.get_all_rooms()
        return ApiResponse.success(data=[RoomService.to_dict(r) for r in rooms])
    except Exception as e:
        logger.error(f"Failed to get rooms: {e}", exc_info=True)
        return ApiResponse.internal_error()


@api_bp.route('/rooms/<room_id>', methods=['DELETE'])
@validate_uuid_param('room_id')
def delete_room(room_id: str) -> Tuple[dict, int]:
    """删除面试间"""
    try:
        success = RoomService.delete_room(room_id)
        if success:
            return ApiResponse.success(message='面试间删除成功')
        return ApiResponse.not_found("面试间")
    except Exception as e:
        logger.error(f"Failed to delete room: {e}", exc_info=True)
        return ApiResponse.internal_error()


# ==================== Session API ====================

@api_bp.route('/sessions/<room_id>', methods=['GET'])
@validate_uuid_param('room_id')
def get_sessions(room_id: str) -> Tuple[dict, int]:
    """获取指定面试间的所有会话"""
    try:
        sessions = SessionService.get_sessions_by_room(room_id)
        return ApiResponse.success(data=[SessionService.to_dict(s) for s in sessions])
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}", exc_info=True)
        return ApiResponse.internal_error()


@api_bp.route('/sessions/<session_id>', methods=['DELETE'])
@validate_uuid_param('session_id')
def delete_session(session_id: str) -> Tuple[dict, int]:
    """删除面试会话"""
    try:
        success = SessionService.delete_session(session_id)
        if success:
            return ApiResponse.success(message='面试会话删除成功')
        return ApiResponse.not_found("面试会话")
    except Exception as e:
        logger.error(f"Failed to delete session: {e}", exc_info=True)
        return ApiResponse.internal_error()


# ==================== Round API ====================

@api_bp.route('/rounds/<session_id>', methods=['GET'])
@validate_uuid_param('session_id')
def get_rounds(session_id: str) -> Tuple[dict, int]:
    """获取指定会话的所有轮次"""
    try:
        rounds = RoundService.get_rounds_by_session(session_id)
        return ApiResponse.success(data=[RoundService.to_dict(r) for r in rounds])
    except Exception as e:
        logger.error(f"Failed to get rounds: {e}", exc_info=True)
        return ApiResponse.internal_error()


@api_bp.post('/rounds/complete')
def complete_round_webhook() -> Tuple[dict, int]:
    """处理数字人轮次完成的回调"""
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return ApiResponse.bad_request('请求体必须为JSON对象')

    required_fields = ['room_id', 'session_id', 'round_index', 'qa_object', 'occurred_at', 'idempotency_key']
    missing_fields = [field for field in required_fields if payload.get(field) is None]
    if missing_fields:
        return ApiResponse.bad_request(f"缺少必要字段: {', '.join(missing_fields)}")

    if not verify_signature(request):
        return ApiResponse.error('签名验证失败', code=ResponseCode.UNAUTHORIZED)

    room_id = str(payload['room_id'])
    session_id = str(payload['session_id'])
    round_index_raw = payload['round_index']
    qa_object = payload['qa_object']
    occurred_at_raw = payload['occurred_at']
    idempotency_key = payload['idempotency_key']

    try:
        round_index = int(round_index_raw)
    except (TypeError, ValueError):
        return ApiResponse.bad_request('round_index 必须为整数')

    if not isinstance(qa_object, (dict, list)):
        return ApiResponse.bad_request('qa_object 必须为 JSON 对象')

    if not isinstance(idempotency_key, str) or not idempotency_key.strip():
        return ApiResponse.bad_request('idempotency_key 无效')

    if not isinstance(occurred_at_raw, str):
        return ApiResponse.bad_request('occurred_at 格式不正确')

    try:
        occurred_at = datetime.fromisoformat(occurred_at_raw.replace('Z', '+00:00'))
    except ValueError:
        return ApiResponse.bad_request('occurred_at 格式不正确')

    session = SessionService.get_session(session_id)
    if not session:
        return ApiResponse.not_found('面试会话')

    if str(session.room.id) != room_id:
        return ApiResponse.bad_request('room_id 与 session_id 不匹配')

    round_obj = RoundService.get_round_by_session_and_index(session_id, round_index)
    if not round_obj:
        return ApiResponse.not_found('面试轮次')

    existing_completion = RoundCompletionService.get_by_idempotency(idempotency_key)
    if existing_completion:
        return ApiResponse.success(
            data={'completion_id': existing_completion.id},
            message='轮次完成事件已处理'
        )

    existing_completion = RoundCompletionService.get_by_session_and_index(session, round_index)
    if existing_completion:
        return ApiResponse.success(
            data={'completion_id': existing_completion.id},
            message='轮次完成事件已处理'
        )

    try:
        completion = RoundCompletionService.record_completion(
            session=session,
            round_index=round_index,
            qa_object=qa_object,
            occurred_at=occurred_at,
            idempotency_key=idempotency_key,
            round_obj=round_obj
        )
        return ApiResponse.success(
            data={'completion_id': completion.id},
            message='轮次完成记录已创建'
        )
    except Exception as exc:
        logger.error(f"Failed to record round completion: {exc}", exc_info=True)
        return ApiResponse.internal_error('处理轮次完成事件失败')


# ==================== 测试 API ====================

@api_bp.route('/minio/test', methods=['GET'])
def test_minio() -> Tuple[dict, int]:
    """测试MinIO连接"""
    try:
        objects = minio_client.list_objects(prefix="data/")
        resume_data = download_resume_data()
        return ApiResponse.success(data={
            'minio_objects': objects,
            'resume_loaded': resume_data is not None,
            'candidate_name': resume_data.get('name') if resume_data else None
        })
    except Exception as e:
        logger.error(f"MinIO test failed: {e}", exc_info=True)
        return ApiResponse.internal_error(str(e))
