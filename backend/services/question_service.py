"""
面试题生成服务
"""

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.services.interview_service import RoundService
from backend.models.models import QuestionAnswer
from backend.utils.minio_client import upload_questions_data, download_resume_data
from llm.clients.qwen_client import QwenClient
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class QuestionGenerationService:
    """面试题生成服务"""
    
    def __init__(self):
        self.qwen_client = QwenClient()
    
    def generate_questions(self, session_id: str) -> Optional[Dict[str, Any]]:
        """为指定会话生成面试题"""
        try:
            # 加载简历数据
            resume_data = download_resume_data()
            if not resume_data:
                return {
                    'success': False,
                    'error': '未找到简历数据，请先上传简历'
                }
            
            # 格式化简历内容
            resume_content = self._format_resume_for_llm(resume_data)
            
            # 生成分类问题
            categorized_questions = self.qwen_client.generate_questions(resume_content)
            
            # 合并所有问题
            all_questions = []
            for category, questions in categorized_questions.items():
                for question in questions:
                    all_questions.append(f"【{category}】{question}")
            
            if not all_questions:
                raise ValueError("未能生成面试题")
            
            # 创建轮次记录
            round_obj = RoundService.create_round(session_id, all_questions)
            if not round_obj:
                raise ValueError("创建轮次失败")

            # 创建问答记录
            self._create_question_answer_records(round_obj, categorized_questions)
            
            # 保存问题到MinIO
            qa_data = {
                'questions': all_questions,
                'round_id': round_obj.id,
                'session_id': session_id,
                'round_index': round_obj.round_index,
                'total_count': len(all_questions),
                'generated_at': datetime.now().isoformat(),
                'categorized_questions': categorized_questions
            }
            
            success = upload_questions_data(qa_data, f"{round_obj.round_index}_{session_id}")
            if not success:
                # 如果MinIO失败，仍然返回数据，但记录错误
                logger.warning(f"Failed to save questions to MinIO for round {round_obj.id}")
            
            return {
                'success': True,
                'round_id': round_obj.id,
                'questions': all_questions,
                'round_index': round_obj.round_index,
                'categorized_questions': categorized_questions
            }
            
        except Exception as e:
            logger.error(f"Error generating questions: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_resume_for_llm(self, resume_data: Dict[str, Any]) -> str:
        """格式化简历数据供LLM使用"""
        if not resume_data:
            return ""
        
        content = f"""
姓名：{resume_data.get('name', '')}
职位：{resume_data.get('position', '')}

技能：
"""
        skills = resume_data.get('skills', [])
        for i, skill in enumerate(skills, 1):
            content += f"{i}. {skill}\n"
        
        content += "\n项目经验：\n"
        projects = resume_data.get('projects', [])
        for i, project in enumerate(projects, 1):
            content += f"{i}. {project}\n"
        
        return content.strip()

    def _create_question_answer_records(self, round_obj, categorized_questions: Dict[str, List[str]]):
        """为轮次创建问答记录"""
        question_index = 0

        for category, questions in categorized_questions.items():
            for question in questions:
                qa_record = QuestionAnswer.create(
                    id=str(uuid.uuid4()),
                    round=round_obj,
                    question_index=question_index,
                    question_text=question,
                    question_category=category,
                    is_answered=False
                )
                question_index += 1

    def get_current_question(self, round_id: str) -> Optional[Dict[str, Any]]:
        """获取当前轮次的当前问题"""
        try:
            round_obj = RoundService.get_round(round_id)
            if not round_obj:
                return None

            # 获取当前问题索引
            current_index = round_obj.current_question_index

            # 查找未回答的问题
            qa_record = QuestionAnswer.select().where(
                (QuestionAnswer.round == round_obj) &
                (QuestionAnswer.question_index == current_index) &
                (QuestionAnswer.is_answered == False)
            ).first()

            if not qa_record:
                # 如果当前索引的问题已回答，查找下一个未回答的问题
                qa_record = QuestionAnswer.select().where(
                    (QuestionAnswer.round == round_obj) &
                    (QuestionAnswer.is_answered == False)
                ).order_by(QuestionAnswer.question_index).first()

            if qa_record:
                total_questions = QuestionAnswer.select().where(
                    QuestionAnswer.round == round_obj
                ).count()

                return {
                    'qa_id': qa_record.id,
                    'question': qa_record.question_text,
                    'category': qa_record.question_category,
                    'question_number': qa_record.question_index + 1,
                    'total_questions': total_questions,
                    'round_id': round_id
                }
            return None

        except Exception as e:
            logger.error(f"Error getting current question: {e}", exc_info=True)
            return None

    def save_answer(self, qa_id: str, answer_text: str) -> Dict[str, Any]:
        """保存用户回答"""
        try:
            qa_record = QuestionAnswer.get_by_id(qa_id)
            qa_record.answer_text = answer_text
            qa_record.is_answered = True
            qa_record.save()

            # 更新轮次的当前问题索引
            round_obj = qa_record.round
            round_obj.current_question_index = qa_record.question_index + 1
            round_obj.save()

            # 检查是否所有问题都已回答
            remaining_questions = QuestionAnswer.select().where(
                (QuestionAnswer.round == round_obj) &
                (QuestionAnswer.is_answered == False)
            ).count()

            if remaining_questions == 0:
                round_obj.status = 'completed'
                round_obj.save()

                # 🆕 生成完整的QA记录JSON文件供LLM分析
                self._save_completed_qa_json(round_obj)

            return {
                'success': True,
                'is_round_completed': remaining_questions == 0,
                'remaining_questions': remaining_questions
            }

        except Exception as e:
            logger.error(f"Error saving answer: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _save_completed_qa_json(self, round_obj):
        """生成完整的QA记录JSON文件供大模型分析"""
        try:
            # 获取所有QA记录
            qa_records = QuestionAnswer.select().where(
                QuestionAnswer.round == round_obj
            ).order_by(QuestionAnswer.question_index)

            # 构建完整的QA数据
            qa_data = {
                "round_info": {
                    "round_id": round_obj.id,
                    "session_id": round_obj.session.id,
                    "round_index": round_obj.round_index,
                    "total_questions": qa_records.count(),
                    "completed_at": datetime.now().isoformat(),
                    "round_type": round_obj.round_type
                },
                "session_info": {
                    "session_name": round_obj.session.name,
                    "room_id": round_obj.session.room.id
                },
                "qa_pairs": [],
                "analysis_ready": True,
                "metadata": {
                    "generated_for": "llm_analysis",
                    "version": "1.0",
                    "file_type": "qa_complete"
                }
            }

            # 添加所有QA对
            for qa in qa_records:
                qa_data["qa_pairs"].append({
                    "question_index": qa.question_index,
                    "category": qa.question_category,
                    "question": qa.question_text,
                    "answer": qa.answer_text,
                    "answered_at": qa.updated_at.isoformat(),
                    "answer_length": len(qa.answer_text) if qa.answer_text else 0,
                    "qa_id": qa.id
                })

            # 保存到MinIO，使用专门的分析文件名
            analysis_filename = f"analysis/qa_complete_{round_obj.round_index}_{round_obj.session.id}.json"

            from backend.utils.minio_client import minio_client
            success = minio_client.upload_json(analysis_filename, qa_data)

            if success:
                logger.info(f"Complete QA data saved for LLM analysis: {analysis_filename}")
            else:
                logger.warning(f"Failed to save QA analysis data: {analysis_filename}")

        except Exception as e:
            logger.error(f"Error saving completed QA JSON: {e}", exc_info=True)


# 延迟初始化全局服务实例
_question_generation_service = None

def get_question_generation_service():
    """获取问题生成服务实例（延迟初始化）"""
    global _question_generation_service
    if _question_generation_service is None:
        _question_generation_service = QuestionGenerationService()
    return _question_generation_service