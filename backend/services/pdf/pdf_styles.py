"""
PDF样式和字体配置
负责PDF文档的样式定义和字体设置
"""

import os
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
        使用项目内置的思源黑体字体,确保跨平台一致性

        Returns:
            可用的字体名称
        """
        # 获取字体文件目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        fonts_dir = os.path.join(current_dir, 'fonts')

        # 注册常规字体
        regular_font_path = os.path.join(fonts_dir, 'NotoSansSC-Regular.ttf')
        bold_font_path = os.path.join(fonts_dir, 'NotoSansSC-Bold.ttf')

        try:
            # 注册常规字体
            if os.path.exists(regular_font_path):
                pdfmetrics.registerFont(TTFont('NotoSansSC', regular_font_path))
                logger.info(f"Successfully registered NotoSansSC font from {regular_font_path}")
            else:
                raise FileNotFoundError(f"Font file not found: {regular_font_path}")

            # 注册粗体字体
            if os.path.exists(bold_font_path):
                pdfmetrics.registerFont(TTFont('NotoSansSC-Bold', bold_font_path))
                logger.info(f"Successfully registered NotoSansSC-Bold font from {bold_font_path}")
            else:
                logger.warning(f"Bold font file not found: {bold_font_path}")

            return 'NotoSansSC'

        except Exception as e:
            logger.error(f"Failed to register bundled fonts: {e}", exc_info=True)
            logger.warning("Falling back to default Helvetica font (Chinese characters may not display correctly)")
            return 'Helvetica'

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
