"""
简历Controller
负责简历上传、解析、获取相关的路由处理
"""

import tempfile
import os
from flask import Blueprint, request
from werkzeug.utils import secure_filename
from backend.common.response import ApiResponse
from backend.clients.minio_client import download_resume_data, upload_resume_data
from backend.common.logger import get_logger

logger = get_logger(__name__)

# 创建蓝图
resume_bp = Blueprint('resume', __name__)


@resume_bp.route('/upload_resume/<room_id>', methods=['POST'])
def upload_resume(room_id: str):
    """上传简历PDF并解析为结构化数据，绑定到指定的room"""
    logger.debug(f"Uploading resume for room: {room_id}")

    try:
        # 验证room是否存在
        from backend.services.interview_service import RoomService
        room = RoomService.get_room(room_id)
        if not room:
            return ApiResponse.not_found("面试间")

        # 验证文件上传
        if 'resume' not in request.files:
            return ApiResponse.bad_request('没有上传文件')

        file = request.files['resume']

        if file.filename == '':
            return ApiResponse.bad_request('没有选择文件')

        if not file.filename.lower().endswith('.pdf'):
            return ApiResponse.bad_request('只支持PDF格式')

        # 获取公司信息（可选）
        company = request.form.get('company', '').strip() or None

        # 保存临时文件
        temp_path = _save_temp_file(file)

        try:
            # 解析PDF
            markdown_content = _parse_pdf(temp_path)

            if not markdown_content:
                return ApiResponse.internal_error('PDF解析失败，请稍后重试')

            # 提取结构化数据
            resume_data = _extract_resume_data(markdown_content)

            if not resume_data:
                return ApiResponse.internal_error('简历数据提取失败')

            # 添加公司信息
            if company:
                resume_data['company'] = company
                logger.info(f"Added company to resume: {company}")

            # 保存到MinIO（绑定到指定room）
            success = upload_resume_data(resume_data, room_id)

            if not success:
                return ApiResponse.internal_error('简历保存失败')

            return ApiResponse.success(
                data={'resume_data': resume_data},
                message='简历上传成功'
            )

        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Failed to upload resume: {e}", exc_info=True)
        return ApiResponse.internal_error(f'上传失败: {str(e)}')


@resume_bp.route('/api/resume/<room_id>')
def get_resume_by_room(room_id: str):
    """获取指定room的简历数据"""
    logger.debug(f"Getting resume for room: {room_id}")

    try:
        resume_data = download_resume_data(room_id)

        if resume_data:
            return ApiResponse.success(data={'resume': resume_data})
        else:
            return ApiResponse.success(data={'resume': None}, message='该面试间还未上传简历')

    except Exception as e:
        logger.error(f"Failed to get resume: {e}", exc_info=True)
        return ApiResponse.internal_error(f'获取简历失败: {str(e)}')


# ==================== 私有辅助函数 ====================

def _save_temp_file(file):
    """保存上传文件到临时目录"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_path = temp_file.name
        file.save(temp_path)
    return temp_path


def _parse_pdf(file_path):
    """调用MinerU服务解析PDF"""
    from backend.clients.mineru_client import get_mineru_client
    mineru_service = get_mineru_client()
    return mineru_service.parse_pdf(file_path)


def _extract_resume_data(markdown_content):
    """使用LLM从Markdown提取结构化数据"""
    from backend.services.resume_parser import get_resume_parser
    resume_parser = get_resume_parser()
    return resume_parser.extract_resume_data(markdown_content)
