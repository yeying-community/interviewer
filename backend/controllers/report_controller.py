"""
报告Controller
负责面试报告生成、获取、下载相关的路由处理
"""

from flask import Blueprint, Response
from backend.services.interview_service import RoundService
from backend.common.response import ApiResponse
from backend.clients.minio_client import minio_client
from backend.common.logger import get_logger

logger = get_logger(__name__)

# 创建蓝图
report_bp = Blueprint('report', __name__, url_prefix='/api')


@report_bp.route('/generate_report/<session_id>/<int:round_index>', methods=['POST'])
def generate_report(session_id, round_index):
    """生成面试评价报告"""
    logger.debug(f"Generating report for session: {session_id}, round: {round_index}")

    try:
        from backend.services.evaluation_service import get_evaluation_service
        from backend.services.pdf import get_pdf_generator

        # 生成评价数据
        evaluation_service = get_evaluation_service()
        eval_result = evaluation_service.generate_evaluation_report(session_id, round_index)

        if not eval_result.get('success'):
            return ApiResponse.error(eval_result.get('error', '生成评价失败'))

        # 生成PDF报告
        pdf_generator = get_pdf_generator()
        pdf_bytes = pdf_generator.generate_report_pdf(eval_result['report_data'])

        if not pdf_bytes:
            return ApiResponse.error('PDF生成失败')

        # 保存PDF到MinIO
        pdf_filename = pdf_generator.save_pdf_to_minio(pdf_bytes, session_id, round_index)

        if not pdf_filename:
            return ApiResponse.error('PDF保存失败')

        return ApiResponse.success(data={
            'evaluation_filename': eval_result['report_filename'],
            'pdf_filename': pdf_filename,
            'report_data': eval_result['report_data']
        })

    except Exception as e:
        logger.error(f"Failed to generate report: {e}", exc_info=True)
        return ApiResponse.internal_error(f'生成报告失败: {str(e)}')


@report_bp.route('/reports/<session_id>/<int:round_index>')
def get_report(session_id, round_index):
    """获取指定会话轮次的报告"""
    logger.debug(f"Getting report for session: {session_id}, round: {round_index}")

    try:
        evaluation_filename = f"reports/evaluation_{round_index}_{session_id}.json"
        evaluation_data = minio_client.download_json(evaluation_filename)

        pdf_filename = f"reports/interview_report_{round_index}_{session_id}.pdf"
        pdf_exists = pdf_filename in minio_client.list_objects(prefix="reports/")

        if evaluation_data:
            return ApiResponse.success(data={
                'evaluation_data': evaluation_data,
                'evaluation_filename': evaluation_filename,
                'pdf_filename': pdf_filename if pdf_exists else None,
                'pdf_exists': pdf_exists
            })
        else:
            return ApiResponse.not_found("报告")

    except Exception as e:
        logger.error(f"Failed to get report: {e}", exc_info=True)
        return ApiResponse.internal_error(f'获取报告失败: {str(e)}')


@report_bp.route('/reports/download/<session_id>/<int:round_index>')
def download_report_pdf(session_id, round_index):
    """下载PDF报告"""
    logger.debug(f"Downloading report PDF for session: {session_id}, round: {round_index}")

    try:
        pdf_filename = f"reports/interview_report_{round_index}_{session_id}.pdf"

        # 从MinIO下载PDF文件
        pdf_object = minio_client.client.get_object(minio_client.bucket_name, pdf_filename)
        pdf_data = pdf_object.data

        return Response(
            pdf_data,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=interview_report_{session_id}_{round_index}.pdf'
            }
        )

    except Exception as e:
        logger.error(f"Failed to download report: {e}", exc_info=True)
        return ApiResponse.not_found("PDF文件")


@report_bp.route('/reports/list/<session_id>')
def list_session_reports(session_id):
    """列出指定会话的所有报告"""
    logger.debug(f"Listing reports for session: {session_id}")

    try:
        rounds = RoundService.get_rounds_by_session(session_id)
        reports = []

        for round_obj in rounds:
            round_index = round_obj.round_index

            # 检查评价报告
            evaluation_filename = f"reports/evaluation_{round_index}_{session_id}.json"
            evaluation_exists = evaluation_filename in minio_client.list_objects(prefix="reports/")

            # 检查PDF报告
            pdf_filename = f"reports/interview_report_{round_index}_{session_id}.pdf"
            pdf_exists = pdf_filename in minio_client.list_objects(prefix="reports/")

            if evaluation_exists or pdf_exists:
                reports.append({
                    'round_index': round_index,
                    'round_id': round_obj.id,
                    'evaluation_exists': evaluation_exists,
                    'pdf_exists': pdf_exists,
                    'evaluation_filename': evaluation_filename if evaluation_exists else None,
                    'pdf_filename': pdf_filename if pdf_exists else None
                })

        return ApiResponse.success(data={
            'session_id': session_id,
            'reports': reports
        })

    except Exception as e:
        logger.error(f"Failed to list reports: {e}", exc_info=True)
        return ApiResponse.internal_error(f'获取报告列表失败: {str(e)}')
