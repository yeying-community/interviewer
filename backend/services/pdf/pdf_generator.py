"""
PDF报告生成器
基于华为面试报告样式生成PDF文件
"""

import io
from typing import Dict, List, Any, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from backend.services.pdf.pdf_styles import PDFStyleManager
from backend.services.pdf.pdf_charts import PDFChartGenerator
from backend.clients.minio_client import minio_client
from backend.common.logger import get_logger

logger = get_logger(__name__)


class PDFReportGenerator:
    """PDF报告生成器"""

    def __init__(self):
        self.style_manager = PDFStyleManager()
        self.chart_generator = PDFChartGenerator(self.style_manager.default_font)
        self.styles = self.style_manager.styles

    def generate_report_pdf(self, report_data: Dict[str, Any]) -> Optional[bytes]:
        """
        生成PDF报告

        Args:
            report_data: 报告数据

        Returns:
            PDF字节流，失败返回None
        """
        try:
            # 创建PDF文档
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                topMargin=2*cm,
                bottomMargin=2*cm,
                leftMargin=2*cm,
                rightMargin=2*cm
            )

            # 构建PDF内容
            story = []
            self._add_header(story, report_data)
            self._add_interviewer_comment(story, report_data)
            self._add_comprehensive_analysis(story, report_data)
            self._add_question_analysis(story, report_data)

            # 生成PDF
            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info("PDF report generated successfully")
            return pdf_bytes

        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            return None

    def _add_header(self, story: List, report_data: Dict[str, Any]):
        """添加报告头部"""
        header = report_data.get('report_header', {})

        # 公司名称和报告标题
        story.append(Paragraph(
            header.get('company_name', '夜影面试官系统'),
            self.styles['ChineseTitle']
        ))
        story.append(Paragraph(
            header.get('report_title', '面试报告'),
            self.styles['ChineseTitle']
        ))

        # 报告信息表格
        info_table = self.chart_generator.create_info_table(header)
        story.append(info_table)
        story.append(Spacer(1, 20))

    def _add_interviewer_comment(self, story: List, report_data: Dict[str, Any]):
        """添加面试官评价"""
        comment = report_data.get('interviewer_comment', {})

        # 标题
        story.append(Paragraph('面试官点评', self.styles['ChineseHeading2']))

        # 总体评价
        summary = comment.get('summary', '')
        story.append(Paragraph(summary, self.styles['ChineseNormal']))
        story.append(Spacer(1, 10))

        # 建议
        story.append(Paragraph('<b>建议：</b>', self.styles['ChineseNormal']))
        suggestions = comment.get('suggestions', '')
        story.append(Paragraph(suggestions, self.styles['ChineseNormal']))
        story.append(Spacer(1, 20))

    def _add_comprehensive_analysis(self, story: List, report_data: Dict[str, Any]):
        """添加综合分析"""
        analysis = report_data.get('comprehensive_analysis', {})

        story.append(Paragraph('综合分析', self.styles['ChineseHeading2']))

        # 创建评分表格
        score_table = self.chart_generator.create_score_table(analysis)
        story.append(score_table)
        story.append(Spacer(1, 10))

        # 各项评分详情
        score_items = [
            ('内容完整度', analysis.get('content_completeness', {})),
            ('亮点突出度', analysis.get('highlight_prominence', {})),
            ('逻辑清晰度', analysis.get('logical_clarity', {})),
            ('表达能力', analysis.get('expression_ability', {})),
            ('岗位契合度', analysis.get('position_matching', {}))
        ]

        for item_name, item_data in score_items:
            score = item_data.get('score', 0)
            comment = item_data.get('comment', '')

            score_text = f'<font color="#4CAF50">{item_name}: {score}分</font>'
            story.append(Paragraph(score_text, self.styles['ScoreStyle']))
            story.append(Paragraph(comment, self.styles['ChineseNormal']))
            story.append(Spacer(1, 8))

        story.append(Spacer(1, 20))

    def _add_question_analysis(self, story: List, report_data: Dict[str, Any]):
        """添加问答分析"""
        questions = report_data.get('question_analysis', [])

        story.append(Paragraph('问答分析', self.styles['ChineseHeading2']))

        for i, qa in enumerate(questions, 1):
            # 问题标题
            question_title = f"{i}. {qa.get('question', '')}"
            story.append(Paragraph(question_title, self.styles['ChineseHeading2']))

            # 问题详情
            story.append(Paragraph(
                f"<b>题目:</b> {qa.get('question', '')}",
                self.styles['ChineseNormal']
            ))
            story.append(Paragraph(
                f"<b>本题考点:</b> {qa.get('key_points', '')}",
                self.styles['ChineseNormal']
            ))

            # 改进建议
            story.append(Paragraph(
                f"<b>改进建议:</b> {qa.get('improvement_suggestions', '')}",
                self.styles['ChineseNormal']
            ))

            # 参考回答
            ref_answer = qa.get('reference_answer', '')
            if ref_answer:
                story.append(Paragraph(
                    f"<b>参考回答:</b> {ref_answer}",
                    self.styles['ChineseNormal']
                ))

            story.append(Spacer(1, 15))

    def save_pdf_to_minio(self, pdf_bytes: bytes, session_id: str, round_index: int) -> Optional[str]:
        """
        保存PDF到MinIO

        Args:
            pdf_bytes: PDF字节流
            session_id: 会话ID
            round_index: 轮次索引

        Returns:
            保存的文件名，失败返回None
        """
        try:
            filename = f"reports/interview_report_{round_index}_{session_id}.pdf"
            pdf_stream = io.BytesIO(pdf_bytes)

            # 上传到MinIO
            minio_client.client.put_object(
                minio_client.bucket_name,
                filename,
                data=pdf_stream,
                length=len(pdf_bytes),
                content_type='application/pdf'
            )

            logger.info(f"PDF report saved to MinIO: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error saving PDF to MinIO: {e}", exc_info=True)
            return None
