"""
PDF图表和可视化组件
负责生成PDF中的表格、图表等可视化元素
"""

from typing import Dict, Any
from reportlab.lib.units import cm
from reportlab.lib.colors import lightblue, darkblue, black
from reportlab.platypus import Table, TableStyle
from backend.common.logger import get_logger

logger = get_logger(__name__)


class PDFChartGenerator:
    """PDF图表生成器"""

    def __init__(self, default_font: str = 'Helvetica'):
        self.default_font = default_font

    def create_score_table(self, analysis: Dict[str, Any]) -> Table:
        """
        创建评分表格（雷达图的替代方案）

        Args:
            analysis: 分析数据字典

        Returns:
            Table对象
        """
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

    def create_info_table(self, header: Dict[str, Any]) -> Table:
        """
        创建报告信息表格

        Args:
            header: 报告头部信息

        Returns:
            Table对象
        """
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

        return info_table

    def create_level_table(self, item_name: str, level: str) -> Table:
        """
        创建等级指示表格

        Args:
            item_name: 评估项名称
            level: 等级（低/中/高）

        Returns:
            Table对象
        """
        level_data = [['', '低', '中', '高'], [item_name, '', '', '']]

        # 根据等级设置标记
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

        return level_table
