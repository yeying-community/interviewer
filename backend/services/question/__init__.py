"""
面试题生成服务
提供问题生成、答案处理等功能的统一入口
"""

from backend.services.question.question_generator import QuestionGenerator
from backend.services.question.answer_handler import AnswerHandler


class QuestionGenerationService:
    """面试题生成服务（Facade模式）"""

    def __init__(self):
        self.generator = QuestionGenerator()
        self.answer_handler = AnswerHandler()

    def generate_questions(self, session_id: str):
        """生成面试题"""
        return self.generator.generate_questions(session_id)

    def get_current_question(self, round_id: str):
        """获取当前问题"""
        return self.answer_handler.get_current_question(round_id)

    def save_answer(self, qa_id: str, answer_text: str):
        """保存用户回答"""
        return self.answer_handler.save_answer(qa_id, answer_text)


# 全局服务实例
_question_generation_service = None


def get_question_generation_service() -> QuestionGenerationService:
    """
    获取问题生成服务实例（单例模式）

    Returns:
        QuestionGenerationService实例
    """
    global _question_generation_service
    if _question_generation_service is None:
        _question_generation_service = QuestionGenerationService()
    return _question_generation_service


__all__ = ['get_question_generation_service', 'QuestionGenerationService']
