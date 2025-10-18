"""
PDF报告生成服务
提供PDF报告生成功能的统一入口
"""

from backend.services.pdf.pdf_generator import PDFReportGenerator

# 全局PDF生成器实例
_pdf_generator = None


def get_pdf_generator() -> PDFReportGenerator:
    """
    获取PDF生成器实例（单例模式）

    Returns:
        PDFReportGenerator实例
    """
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = PDFReportGenerator()
    return _pdf_generator


__all__ = ['get_pdf_generator', 'PDFReportGenerator']
