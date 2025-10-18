"""
PDF样式和字体配置
负责PDF文档的样式定义和字体设置
"""

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from backend.common.logger import get_logger

logger = get_logger(__name__)


class PDFStyleManager:
    """PDF样式管理器"""

    def __init__(self):
        self.default_font = self._setup_fonts()
        self.styles = self._create_styles()

    def _setup_fonts(self) -> str:
        """
        设置中文字体支持

        Returns:
            可用的字体名称
        """
        # 默认字体
        default_font = 'Helvetica'

        # 尝试注册中文字体（按优先级）
        font_attempts = [
            ('STHeiti', '/System/Library/Fonts/STHeiti Light.ttc'),
            ('SimSun', '/System/Library/Fonts/SimSun.ttf'),
            ('PingFang', '/System/Library/Fonts/PingFang.ttc'),
        ]

        for font_name, font_path in font_attempts:
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                logger.info(f"Successfully registered {font_name} font")
                return font_name
            except Exception as e:
                logger.debug(f"Failed to register {font_name}: {e}")

        logger.warning("No Chinese font found, using default Helvetica font")
        return default_font

    def _create_styles(self):
        """
        创建PDF样式集合

        Returns:
            样式字典
        """
        styles = getSampleStyleSheet()

        # 标题样式
        styles.add(ParagraphStyle(
            name='ChineseTitle',
            parent=styles['Title'],
            fontName=self.default_font,
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=20,
        ))

        # 中文正文样式
        styles.add(ParagraphStyle(
            name='ChineseNormal',
            parent=styles['Normal'],
            fontName=self.default_font,
            fontSize=10,
            alignment=TA_LEFT,
            leftIndent=0,
            rightIndent=0,
        ))

        # 小标题样式
        styles.add(ParagraphStyle(
            name='ChineseHeading2',
            parent=styles['Heading2'],
            fontName=self.default_font,
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
            fontName=self.default_font,
            fontSize=12,
            alignment=TA_LEFT,
            leftIndent=20,
        ))

        logger.debug(f"PDF styles created with font: {self.default_font}")
        return styles
