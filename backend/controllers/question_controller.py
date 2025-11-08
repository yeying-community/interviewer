"""
问题Controller
负责面试问题生成、获取、回答相关的路由处理
"""

import os
from datetime import datetime
from flask import Blueprint, request, jsonify
from backend.services.interview_service import SessionService
from backend.clients.digitalhub_client import start_llm
from backend.clients.minio_client import minio_client
from backend.common.response import ApiResponse
from backend.common.logger import get_logger
from backend.models.models import Round, database

logger = get_logger(__name__)

# 创建蓝图
question_bp = Blueprint('question', __name__)


@question_bp.route('/generate_questions/<session_id>', methods=['POST'])
def generate_questions(session_id):
    """生成面试题 + 启动 LLM Round Server"""
    logger.debug(f"Generating questions for session: {session_id}")

    session = SessionService.get_session(session_id)
    if not session:
        return ApiResponse.not_found("面试会话")

    try:
        # 生成问题
        from backend.services.question import get_question_generation_service
        service = get_question_generation_service()
        result = service.generate_questions(session_id)

        if not result['success']:
            return ApiResponse.error(result['error'])

        # 启动LLM
        #_start_llm_server(session_id, result, result.get('round_index', 0))
        _start_llm_server(session_id, session.room.id, result, result.get('round_index', 0))
        return ApiResponse.success(data=result)

    except Exception as e:
        logger.error(f"Failed to generate questions: {e}", exc_info=True)
        return ApiResponse.internal_error(f'生成面试题失败: {str(e)}')


@question_bp.route('/upload_jd/<room_id>', methods=['POST'])
def upload_jd(room_id: str):
    """为面试间上传自定义 JD"""
    logger.debug(f"Uploading JD for room: {room_id}")

    try:
        # 验证 room 是否存在
        from backend.services.interview_service import RoomService
        room = RoomService.get_room(room_id)
        if not room:
            return ApiResponse.not_found("面试间")

        data = request.get_json()
        company = data.get('company')
        position = data.get('position')
        content = data.get('content')

        if not content:
            return ApiResponse.bad_request('JD 内容不能为空')

        from backend.clients.rag.rag_client import get_rag_client
        rag_client = get_rag_client()

        # 调用 RAG 上传 JD
        jd_id = rag_client.upload_jd(
            memory_id=room.memory_id,
            company=company,
            position=position,
            content=content
        )

        # 保存 jd_id 到 room
        room.jd_id = jd_id
        room.save()

        logger.info(f"Successfully uploaded JD for room {room_id}: {jd_id}")
        return ApiResponse.success(data={'jd_id': jd_id}, message='JD上传成功')

    except Exception as e:
        logger.error(f"Failed to upload JD: {e}", exc_info=True)
        return ApiResponse.internal_error(f'上传JD失败: {str(e)}')


@question_bp.route('/get_current_question/<round_id>')
def get_current_question(round_id):
    """获取当前问题"""
    logger.debug(f"Getting current question for round: {round_id}")

    try:
        from backend.services.question import get_question_generation_service
        service = get_question_generation_service()
        question_data = service.get_current_question(round_id)

        if question_data:
            return ApiResponse.success(data={'question_data': question_data})
        else:
            return ApiResponse.success(data=None, message='没有更多问题了')

    except Exception as e:
        logger.error(f"Failed to get question: {e}", exc_info=True)
        return ApiResponse.internal_error(f'获取问题失败: {str(e)}')


@question_bp.route('/save_answer', methods=['POST'])
def save_answer():
    """保存用户回答"""
    logger.debug("Saving answer")

    try:
        data = request.get_json()
        qa_id = data.get('qa_id')
        answer_text = data.get('answer_text')

        if not qa_id or not answer_text:
            return ApiResponse.bad_request('缺少必要参数')

        from backend.services.question import get_question_generation_service
        service = get_question_generation_service()
        result = service.save_answer(qa_id, answer_text.strip())

        return jsonify(result)

    except Exception as e:
        logger.error(f"Failed to save answer: {e}", exc_info=True)
        return ApiResponse.internal_error(f'保存回答失败: {str(e)}')


@question_bp.route('/get_qa_analysis/<session_id>/<int:round_index>')
def get_qa_analysis(session_id, round_index):
    """获取指定轮次的QA分析数据"""
    logger.debug(f"Getting QA analysis for session: {session_id}, round: {round_index}")

    try:
        from backend.clients.minio_client import minio_client

        analysis_filename = f"analysis/qa_complete_{round_index}_{session_id}.json"
        analysis_data = minio_client.download_json(analysis_filename)

        if analysis_data:
            return ApiResponse.success(data={
                'analysis_data': analysis_data,
                'file_path': analysis_filename
            })
        else:
            return ApiResponse.not_found("分析数据")

    except Exception as e:
        logger.error(f"Failed to get QA analysis: {e}", exc_info=True)
        return ApiResponse.internal_error(f'获取分析数据失败: {str(e)}')


@question_bp.route('/qa_completion/<session_id>/<int:round_index>', methods=['POST'])
def confirm_qa_completion(session_id, round_index):
    """确认指定轮次的QA数据已生成"""
    logger.debug(
        "Confirming QA completion for session %s round %s", session_id, round_index
    )

    payload = request.get_json(silent=True) or {}
    idempotency_key = (
        request.headers.get('Idempotency-Key')
        or payload.get('idempotency_key')
    )
    event_time = datetime.now().isoformat()

    session_obj = SessionService.get_session(session_id)
    if not session_obj:
        logger.warning(
            "Session not found when confirming QA completion: session=%s",
            session_id,
        )
        return ApiResponse.not_found("面试会话")

    try:
        round_obj = Round.get(
            (Round.session == session_obj) & (Round.round_index == round_index)
        )
    except Round.DoesNotExist:
        logger.warning(
            "Round not found when confirming QA completion: session=%s round=%s",
            session_id,
            round_index,
        )
        return ApiResponse.not_found("轮次")

    room_id = session_obj.room.id
    qa_object_path = (
        f"rooms/{room_id}/sessions/{session_id}/analysis/qa_complete_{round_index}.json"
    )

    if not minio_client.object_exists(qa_object_path):
        logger.warning(
            "QA object missing for session %s round %s at %s (idempotency_key=%s)",
            session_id,
            round_index,
            qa_object_path,
            idempotency_key,
        )
        return jsonify({"error": "qa object missing"}), 409

    try:
        with database.atomic():
            round_obj = Round.get_by_id(round_obj.id)
            if round_obj.status != 'completed':
                round_obj.status = 'completed'
                round_obj.save()

                has_active_rounds = Round.select().where(
                    (Round.session == session_obj) & (Round.status != 'completed')
                ).exists()

                if not has_active_rounds and session_obj.status != 'completed':
                    session_obj.status = 'completed'
                    session_obj.save()
    except Exception as exc:
        logger.error(
            "Failed to update completion status for session %s round %s: %s",
            session_id,
            round_index,
            exc,
            exc_info=True,
        )
        return ApiResponse.internal_error("更新轮次状态失败")

    logger.info(
        "QA completion confirmed for session %s round %s: path=%s, idempotency_key=%s, timestamp=%s",
        session_id,
        round_index,
        qa_object_path,
        idempotency_key,
        event_time,
    )

    return jsonify({
        "is_completed": True,
        "qa_object_path": qa_object_path,
    })


# ==================== 私有辅助函数 ====================
def _start_llm_server(session_id: str, room_id: str, result: dict, round_index: int):
#def _start_llm_server(session_id, result, round_index):
    """启动LLM Round Server"""
    try:
        llm_info = start_llm(
            room_id=room_id,
            session_id=session_id,
            round_index=int(round_index),
            port=int(os.getenv("LLM_PORT", "8011")),
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "test-minio.yeying.pub"),
            minio_access_key=os.getenv("MINIO_ACCESS_KEY", ""),
            minio_secret_key=os.getenv("MINIO_SECRET_KEY", ""),
            minio_bucket=os.getenv("MINIO_BUCKET", "yeying-interviewer"),
            minio_secure=os.getenv("MINIO_SECURE", "true").lower() == "true",
        )
        result['llm'] = llm_info.get('data', llm_info)
    except Exception as e:
        logger.warning(f"Failed to start LLM server: {e}")
        result['llm_error'] = str(e)































