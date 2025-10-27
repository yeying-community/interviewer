"""
问题Controller
负责面试问题生成、获取、回答相关的路由处理
"""

import os
from flask import Blueprint, request, jsonify
from backend.services.interview_service import SessionService
from backend.clients.digitalhub_client import start_llm
from backend.common.response import ApiResponse
from backend.common.logger import get_logger

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































