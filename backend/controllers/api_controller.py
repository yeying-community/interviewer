"""
API控制器
提供RESTful API接口（GET/DELETE等）
"""

from flask import Blueprint, request
from typing import Tuple
from backend.services.interview_service import RoomService, SessionService, RoundService
from backend.common.response import ApiResponse
from backend.common.validators import validate_uuid_param
from backend.clients.minio_client import minio_client, download_resume_data
from backend.common.logger import get_logger

logger = get_logger(__name__)

# 创建API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')


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
