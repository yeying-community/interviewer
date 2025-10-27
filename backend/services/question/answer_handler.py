"""
面试答案处理服务
负责管理问题回答、获取当前问题等
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional
from backend.services.interview_service import RoundService
from backend.models.models import QuestionAnswer
from backend.common.logger import get_logger

logger = get_logger(__name__)


class AnswerHandler:
    """答案处理器"""

    def get_current_question(self, round_id: str) -> Optional[Dict[str, Any]]:
        """
        获取当前轮次的当前问题

        Args:
            round_id: 轮次ID

        Returns:
            问题数据，如果没有更多问题返回None
        """
        try:
            round_obj = RoundService.get_round(round_id)
            if not round_obj:
                return None

            # 获取当前问题索引
            current_index = round_obj.current_question_index

            # 查找未回答的问题
            qa_record = self._find_unanswered_question(round_obj, current_index)

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
        """
        保存用户回答

        Args:
            qa_id: 问答记录ID
            answer_text: 回答文本

        Returns:
            保存结果
        """
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
            remaining_questions = self._count_remaining_questions(round_obj)

            if remaining_questions == 0:
                round_obj.status = 'completed'
                round_obj.save()

                # 生成完整的QA记录JSON文件供LLM分析
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

    def _find_unanswered_question(self, round_obj, current_index: int) -> Optional[QuestionAnswer]:
        """查找未回答的问题"""
        # 首先尝试获取当前索引的问题
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

        return qa_record

    def _count_remaining_questions(self, round_obj) -> int:
        """统计剩余未回答的问题数"""
        return QuestionAnswer.select().where(
            (QuestionAnswer.round == round_obj) &
            (QuestionAnswer.is_answered == False)
        ).count()

    def _save_completed_qa_json(self, round_obj):
        """生成完整的QA记录JSON文件供大模型分析"""
        try:
            # 获取所有QA记录
            qa_records = QuestionAnswer.select().where(
                QuestionAnswer.round == round_obj
            ).order_by(QuestionAnswer.question_index)

            # 获取room_id和session_id
            session = round_obj.session
            room_id = session.room.id
            session_id = session.id

            # 构建完整的QA数据
            qa_data = {
                "round_info": {
                    "round_id": round_obj.id,
                    "session_id": session_id,
                    "room_id": room_id,
                    "round_index": round_obj.round_index,
                    "total_questions": qa_records.count(),
                    "completed_at": datetime.now().isoformat(),
                    "round_type": round_obj.round_type
                },
                "session_info": {
                    "session_name": session.name,
                    "room_id": room_id
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

            # 保存到MinIO（使用新的路径结构）
            from backend.clients.minio_client import upload_qa_analysis
            success = upload_qa_analysis(qa_data, room_id, session_id, round_obj.round_index)

            if success:
                logger.info(f"Complete QA data saved for LLM analysis: room={room_id}, session={session_id}, round={round_obj.round_index}")

                # 推送到 RAG 记忆体
                try:
                    self._push_to_rag_memory(room_id, session_id, round_obj, qa_data)
                except Exception as e:
                    logger.error(f"Failed to push QA data to RAG memory: {e}", exc_info=True)
            else:
                logger.warning(f"Failed to save QA analysis data")

        except Exception as e:
            logger.error(f"Error saving completed QA JSON: {e}", exc_info=True)

    def _push_to_rag_memory(
        self,
        room_id: str,
        session_id: str,
        round_obj,
        qa_data: Dict[str, Any]
    ):
        """
        推送问答数据到 RAG 记忆体

        Args:
            room_id: 面试间ID
            session_id: 会话ID
            round_obj: 轮次对象
            qa_data: 完整的问答数据
        """
        from backend.clients.rag.rag_client import get_rag_client

        try:
            room = round_obj.session.room
            memory_id = room.memory_id

            # 构建 MinIO 路径作为 URL
            minio_url = f"rooms/{room_id}/sessions/{session_id}/analysis/round_{round_obj.round_index}.json"

            # 将 qa_data 转换为 JSON 字符串作为 description
            description = json.dumps(qa_data, ensure_ascii=False)

            # 推送到 RAG
            rag_client = get_rag_client()
            result = rag_client.push_message(
                memory_id=memory_id,
                url=minio_url,
                description=description,
                app="interviewer"
            )

            logger.info(f"Successfully pushed QA data to RAG memory {memory_id}: {minio_url}")

        except Exception as e:
            logger.error(f"Error pushing to RAG memory: {e}", exc_info=True)
            raise
