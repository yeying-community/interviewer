"""
面试问题生成服务
负责根据简历生成面试题
"""

import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.services.interview_service import RoundService
from backend.models.models import QuestionAnswer
from backend.clients.minio_client import upload_questions_data, download_resume_data
from backend.clients.llm.qwen_client import QwenClient
from backend.clients.rag.rag_client import get_rag_client
from backend.common.logger import get_logger

logger = get_logger(__name__)


class QuestionGenerator:
    """面试题生成器"""

    def __init__(self):
        self.qwen_client = QwenClient()
        self.use_rag = True  # 是否使用 RAG 服务

    def generate_questions(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        为指定会话生成面试题

        Args:
            session_id: 会话ID

        Returns:
            生成结果，包含问题列表等信息
        """
        try:
            # 0. 获取session信息
            from backend.services.interview_service import SessionService
            session = SessionService.get_session(session_id)
            if not session:
                return {
                    'success': False,
                    'error': '会话不存在'
                }

            room_id = session.room.id
            room = session.room

            # 1. 加载简历数据（使用room_id）
            from backend.clients.minio_client import download_resume_data
            resume_data = download_resume_data(room_id)
            if not resume_data:
                return {
                    'success': False,
                    'error': '该面试间还未上传简历，请先上传简历'
                }

            # 2. 使用 RAG 生成问题
            if self.use_rag:
                try:
                    questions_result = self._generate_questions_via_rag(
                        memory_id=room.memory_id,
                        resume_data=resume_data,
                        room_id=room_id,
                        jd_id=room.jd_id  # 使用面试间的 JD ID
                    )
                    all_questions = questions_result['questions']
                    # RAG 返回的问题可能没有分类，统一归类为 "RAG生成"
                    categorized_questions = {"RAG生成": all_questions}
                except Exception as e:
                    logger.error(f"Failed to generate questions via RAG: {e}")
                    logger.info("Fallback to Qwen client")
                    # 降级到 Qwen
                    resume_content = self._format_resume_for_llm(resume_data)
                    categorized_questions = self.qwen_client.generate_questions(resume_content)
                    all_questions = self._merge_questions(categorized_questions)
            else:
                # 使用原有的 Qwen 方式
                resume_content = self._format_resume_for_llm(resume_data)
                categorized_questions = self.qwen_client.generate_questions(resume_content)
                all_questions = self._merge_questions(categorized_questions)

            if not all_questions:
                raise ValueError("未能生成面试题")

            # 5. 创建轮次记录
            round_obj = RoundService.create_round(session_id, all_questions)
            if not round_obj:
                raise ValueError("创建轮次失败")

            # 6. 创建问答记录
            self._create_question_answer_records(round_obj, categorized_questions)

            # 7. 保存问题到MinIO（使用新的路径结构）
            success = self._save_questions_to_minio(
                all_questions,
                round_obj,
                room_id,
                session_id,
                categorized_questions
            )

            if not success:
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

    def _generate_questions_via_rag(
        self,
        memory_id: str,
        resume_data: Dict[str, Any],
        room_id: str,
        jd_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        通过 RAG 服务生成问题

        Args:
            memory_id: 记忆体ID
            resume_data: 简历数据（用于提取 company 和 position）
            room_id: 面试间ID（用于构造 resume_url）
            jd_id: 面试间上传的 JD ID（可选，优先使用）

        Returns:
            包含 questions 列表的字典
        """
        rag_client = get_rag_client()

        # 构造简历在 MinIO 中的路径
        resume_url = f"rooms/{room_id}/resume.json"

        result = rag_client.generate_questions(
            memory_id=memory_id,
            resume_url=resume_url,
            company=resume_data.get('company'),
            target_position=resume_data.get('position'),
            jd_id=jd_id,  # 使用面试间的 JD ID
            jd_top_k=3,
            memory_top_k=3,
            max_chars=4000
        )

        logger.info(f"Generated {len(result['questions'])} questions via RAG for memory {memory_id}")
        return result

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

    def _merge_questions(self, categorized_questions: Dict[str, List[str]]) -> List[str]:
        """合并分类问题为单一列表"""
        all_questions = []
        for category, questions in categorized_questions.items():
            for question in questions:
                all_questions.append(f"【{category}】{question}")
        return all_questions

    def _create_question_answer_records(self, round_obj, categorized_questions: Dict[str, List[str]]):
        """为轮次创建问答记录"""
        question_index = 0

        for category, questions in categorized_questions.items():
            for question in questions:
                QuestionAnswer.create(
                    id=str(uuid.uuid4()),
                    round=round_obj,
                    question_index=question_index,
                    question_text=question,
                    question_category=category,
                    is_answered=False
                )
                question_index += 1

    def _save_questions_to_minio(
        self,
        all_questions: List[str],
        round_obj,
        room_id: str,
        session_id: str,
        categorized_questions: Dict[str, List[str]]
    ) -> bool:
        """保存问题到MinIO（使用新的目录结构）"""
        from backend.clients.minio_client import upload_questions_data

        qa_data = {
            'questions': all_questions,
            'round_id': round_obj.id,
            'session_id': session_id,
            'room_id': room_id,
            'round_index': round_obj.round_index,
            'total_count': len(all_questions),
            'generated_at': datetime.now().isoformat(),
            'categorized_questions': categorized_questions
        }

        return upload_questions_data(qa_data, room_id, session_id, round_obj.round_index)
