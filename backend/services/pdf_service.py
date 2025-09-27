"""
PDF报告生成服务
基于华为面试报告样式生成PDF文件
"""

import os
import io
import math
from typing import Dict, List, Any, Optional
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Circle, Line, String
from reportlab.graphics.charts.spider import SpiderChart
from reportlab.graphics import renderPDF
from backend.utils.minio_client import minio_client


class PDFReportGenerator:
    """PDF报告生成器"""

    def __init__(self):
        self._setup_fonts()
        self.styles = self._create_styles()

    def _setup_fonts(self):
        """设置中文字体支持"""
        self.default_font = 'Helvetica'  # 默认使用Helvetica

        try:
            # 首先尝试注册macOS可用的STHeiti字体
            pdfmetrics.registerFont(TTFont('STHeiti', '/System/Library/Fonts/STHeiti Light.ttc'))
            self.default_font = 'STHeiti'
            print("Successfully registered STHeiti font")
        except Exception as e1:
            print(f"Failed to register STHeiti: {e1}")
            try:
                # 备选：尝试使用系统字体
                pdfmetrics.registerFont(TTFont('SimHei', '/System/Library/Fonts/SimHei.ttf'))
                pdfmetrics.registerFont(TTFont('SimSun', '/System/Library/Fonts/SimSun.ttf'))
                self.default_font = 'SimSun'
                print("Successfully registered SimHei and SimSun fonts")
            except Exception as e2:
                print(f"Failed to register SimHei/SimSun: {e2}")
                try:
                    # 再次备选：PingFang字体
                    pdfmetrics.registerFont(TTFont('PingFang', '/System/Library/Fonts/PingFang.ttc'))
                    self.default_font = 'PingFang'
                    print("Successfully registered PingFang font")
                except Exception as e3:
                    # 如果都不可用，使用默认字体
                    print(f"Failed to register PingFang: {e3}")
                    print("Warning: No Chinese font found, using default font")
                    self.default_font = 'Helvetica'

    def _create_styles(self):
        """创建样式"""
        styles = getSampleStyleSheet()

        # 获取可用的字体名称
        font_name = getattr(self, 'default_font', 'Helvetica')
        print(f"Using font for PDF: {font_name}")

        # 标题样式
        styles.add(ParagraphStyle(
            name='ChineseTitle',
            parent=styles['Title'],
            fontName=font_name,
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20,
        ))

        # 中文正文样式
        styles.add(ParagraphStyle(
            name='ChineseNormal',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            alignment=TA_LEFT,
            leftIndent=0,
            rightIndent=0,
        ))

        # 小标题样式
        styles.add(ParagraphStyle(
            name='ChineseHeading2',
            parent=styles['Heading2'],
            fontName=font_name,
            fontSize=14,
            alignment=TA_CENTER,
            spaceAfter=12,
            spaceBefore=12,
            backColor=HexColor('#E8F4FD'),
        ))

        # 评分样式
        styles.add(ParagraphStyle(
            name='ScoreStyle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=12,
            alignment=TA_LEFT,
            leftIndent=20,
        ))

        return styles

    def generate_report_pdf(self, report_data: Dict[str, Any]) -> Optional[bytes]:
        """生成PDF报告"""
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

            # 添加报告头部
            self._add_header(story, report_data)

            # 添加面试官评价
            self._add_interviewer_comment(story, report_data)

            # 添加综合分析
            self._add_comprehensive_analysis(story, report_data)

            # 添加问答分析
            self._add_question_analysis(story, report_data)

            # 生成PDF
            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            return pdf_bytes

        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None

    def _add_header(self, story: List, report_data: Dict[str, Any]):
        """添加报告头部"""
        header = report_data.get('report_header', {})

        # 公司名称和报告标题
        story.append(Paragraph(header.get('company_name', '夜影面试官系统'), self.styles['ChineseTitle']))
        story.append(Paragraph(header.get('report_title', '面试报告'), self.styles['ChineseTitle']))

        # 生成时间和等级
        info_data = [
            ['报告生成时间:', header.get('generated_time', '')],
            ['综合等级:', header.get('overall_grade', '')],
            ['综合得分:', f"{header.get('total_score', 0)}分"]
        ]

        info_table = Table(info_data, colWidths=[3*cm, 4*cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

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

        # 创建雷达图
        radar_chart = self._create_radar_chart(analysis)
        story.append(radar_chart)
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

    def _create_radar_chart(self, analysis: Dict[str, Any]) -> Drawing:
        """创建雷达图"""
        # 创建绘图区域
        drawing = Drawing(400, 300)

        # 由于SpiderChart的中文字体支持有问题，直接使用简单的分数表格
        from reportlab.lib.colors import lightblue, darkblue

        score_data = [
            ['维度', '得分'],
            ['内容完整度', f"{analysis.get('content_completeness', {}).get('score', 0)}分"],
            ['亮点突出度', f"{analysis.get('highlight_prominence', {}).get('score', 0)}分"],
            ['逻辑清晰度', f"{analysis.get('logical_clarity', {}).get('score', 0)}分"],
            ['表达能力', f"{analysis.get('expression_ability', {}).get('score', 0)}分"],
            ['岗位契合度', f"{analysis.get('position_matching', {}).get('score', 0)}分"]
        ]

        table = Table(score_data, colWidths=[3*cm, 2*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), self.default_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), lightblue),
            ('GRID', (0, 0), (-1, -1), 1, darkblue)
        ]))

        return table

    def _add_key_points_analysis(self, story: List, report_data: Dict[str, Any]):
        """添加考点分析"""
        key_points = report_data.get('key_points_analysis', {})

        story.append(Paragraph('考点分析', self.styles['ChineseHeading2']))

        analysis_items = [
            ('项目深度', key_points.get('project_depth', {})),
            ('个性潜质', key_points.get('personality_potential', {})),
            ('专业知识点', key_points.get('professional_knowledge', {})),
            ('软素质知识点', key_points.get('soft_skills', {}))
        ]

        for item_name, item_data in analysis_items:
            level = item_data.get('level', '中')
            description = item_data.get('description', '')
            can_strengthen = item_data.get('can_strengthen', False)

            strengthen_text = '可强化' if can_strengthen else '无需强化'
            color = '#FF9800' if can_strengthen else '#4CAF50'

            story.append(Paragraph(f'<b>{item_name}:</b>', self.styles['ChineseNormal']))
            story.append(Paragraph(description, self.styles['ChineseNormal']))

            level_data = [['', '低', '中', '高'], [item_name, '', '', '']]
            if level == '低':
                level_data[1][1] = '●'
            elif level == '中':
                level_data[1][2] = '●'
            else:
                level_data[1][3] = '●'

            level_table = Table(level_data, colWidths=[2*cm, 1*cm, 1*cm, 1*cm])
            level_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.default_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (1, 0), (-1, -1), 0.5, black),
            ]))

            story.append(level_table)
            story.append(Paragraph(f'<font color="{color}">{strengthen_text}</font>', self.styles['ChineseNormal']))
            story.append(Spacer(1, 15))

        story.append(Spacer(1, 20))

    def _add_question_analysis(self, story: List, report_data: Dict[str, Any]):
        """添加问答分析"""
        questions = report_data.get('question_analysis', [])

        story.append(Paragraph('问答分析', self.styles['ChineseHeading2']))

        for i, qa in enumerate(questions, 1):
            # 问题标题
            question_title = f"{i} {qa.get('question', '')}"
            story.append(Paragraph(question_title, self.styles['ChineseHeading2']))

            # 问题详情
            story.append(Paragraph(f"<b>题目:</b> {qa.get('question', '')}", self.styles['ChineseNormal']))
            story.append(Paragraph(f"<b>本题考点:</b> {qa.get('key_points', '')}", self.styles['ChineseNormal']))

            # 改进建议
            story.append(Paragraph(f"<b>改进建议:</b> {qa.get('improvement_suggestions', '')}", self.styles['ChineseNormal']))

            # 参考回答
            ref_answer = qa.get('reference_answer', '')
            if ref_answer:
                story.append(Paragraph(f"<b>参考回答:</b> {ref_answer}", self.styles['ChineseNormal']))

            story.append(Spacer(1, 15))

    def save_pdf_to_minio(self, pdf_bytes: bytes, session_id: str, round_index: int) -> Optional[str]:
        """保存PDF到MinIO"""
        try:
            filename = f"reports/interview_report_{round_index}_{session_id}.pdf"

            # 使用BytesIO创建临时文件
            pdf_stream = io.BytesIO(pdf_bytes)

            # 上传到MinIO
            result = minio_client.client.put_object(
                minio_client.bucket_name,
                filename,
                data=pdf_stream,
                length=len(pdf_bytes),
                content_type='application/pdf'
            )

            # put_object成功时返回一个对象，失败时抛出异常
            print(f"PDF report saved to MinIO: {filename}")
            return filename

        except Exception as e:
            print(f"Error saving PDF to MinIO: {e}")
            return None


# 全局PDF生成器实例
_pdf_generator = None

def get_pdf_generator():
    """获取PDF生成器实例（延迟初始化）"""
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = PDFReportGenerator()
    return _pdf_generator