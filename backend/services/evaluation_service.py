"""
面试QA评价服务
基于华为面试报告模板，使用大模型对面试QA进行综合评价
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from backend.clients.minio_client import minio_client
from backend.clients.llm.qwen_client import QwenClient
from backend.clients.llm.prompts.evaluation_prompts import (
    get_interview_evaluation_prompt,
    get_single_question_evaluation_prompt,
    get_report_summary_prompt
)
from backend.common.logger import get_logger

logger = get_logger(__name__)


class InterviewEvaluationService:
    """面试评价服务"""

    def __init__(self):
        self.qwen_client = QwenClient()

    def generate_evaluation_report(self, session_id: str, round_index: int) -> Optional[Dict[str, Any]]:
        """生成面试评价报告"""
        try:
            # 1. 加载QA数据
            qa_data = self._load_qa_data(session_id, round_index)
            if not qa_data:
                raise ValueError("无法加载QA数据")

            # 2. 调用大模型进行评价
            evaluation_result = self._evaluate_with_llm(qa_data)

            # 3. 构建完整的评价报告
            report_data = self._build_evaluation_report(qa_data, evaluation_result, session_id, round_index)

            # 4. 保存评价报告到MinIO
            report_filename = f"reports/evaluation_{round_index}_{session_id}.json"
            success = minio_client.upload_json(report_filename, report_data)

            if success:
                logger.info(f"Evaluation report saved: {report_filename}")
                return {
                    'success': True,
                    'report_data': report_data,
                    'report_filename': report_filename
                }
            else:
                raise Exception("保存评价报告失败")

        except Exception as e:
            logger.error(f"Error generating evaluation report: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _load_qa_data(self, session_id: str, round_index: int) -> Optional[Dict[str, Any]]:
        """加载QA完成数据"""
        # 获取session对应的room_id
        from backend.services.interview_service import SessionService
        session = SessionService.get_session(session_id)
        if not session:
            return None

        room_id = session.room.id

        # 使用新的路径结构
        from backend.clients.minio_client import download_qa_analysis
        return download_qa_analysis(room_id, session_id, round_index)

    def _evaluate_with_llm(self, qa_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用大模型评价QA数据"""
        try:
            # 使用分离的prompt模板
            evaluation_prompt = get_interview_evaluation_prompt(qa_data)

            messages = [{"role": "user", "content": evaluation_prompt}]
            response = self.qwen_client.chat_completion(messages, temperature=0.3, max_tokens=3000)

            # 解析大模型响应
            return self._parse_evaluation_response(response)

        except Exception as e:
            logger.error(f"Error in LLM evaluation: {e}", exc_info=True)
            # 返回默认评价结果
            return self._get_default_evaluation()

    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """解析大模型评价响应"""
        try:
            # 尝试提取JSON部分
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]

            # 解析JSON
            evaluation_data = json.loads(response)
            return evaluation_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}", exc_info=True)
            return self._get_default_evaluation()

    def _get_default_evaluation(self) -> Dict[str, Any]:
        """获取默认评价结果"""
        return {
            "interviewer_comment": {
                "summary": "面试者在技术问题上表现良好，展现了一定的基础知识和实践经验。",
                "suggestions": "建议在回答时更加详细和具体，展现更深入的技术理解。"
            },
            "comprehensive_analysis": {
                "content_completeness": {"score": 7, "comment": "回答内容基本完整"},
                "highlight_prominence": {"score": 6, "comment": "亮点表现一般"},
                "logical_clarity": {"score": 7, "comment": "逻辑结构清晰"},
                "expression_ability": {"score": 7, "comment": "表达能力良好"},
                "position_matching": {"score": 7, "comment": "岗位匹配度中等"}
            },
            "key_points_analysis": {
                "project_depth": {
                    "level": "中",
                    "description": "项目经验有一定深度",
                    "can_strengthen": True
                },
                "personality_potential": {
                    "level": "中",
                    "description": "个性潜质表现一般",
                    "can_strengthen": True
                },
                "professional_knowledge": {
                    "level": "中",
                    "description": "专业知识掌握程度中等",
                    "can_strengthen": True
                },
                "soft_skills": {
                    "level": "中",
                    "description": "软技能表现一般",
                    "can_strengthen": True
                }
            },
            "question_analysis": []
        }

    def _build_evaluation_report(self, qa_data: Dict[str, Any], evaluation_result: Dict[str, Any],
                               session_id: str, round_index: int) -> Dict[str, Any]:
        """构建完整的评价报告"""
        session_info = qa_data.get('session_info', {})
        round_info = qa_data.get('round_info', {})
        qa_pairs = qa_data.get('qa_pairs', [])

        # 计算综合得分
        scores = evaluation_result.get('comprehensive_analysis', {})
        total_score = sum([
            scores.get('content_completeness', {}).get('score', 7),
            scores.get('highlight_prominence', {}).get('score', 6),
            scores.get('logical_clarity', {}).get('score', 7),
            scores.get('expression_ability', {}).get('score', 7),
            scores.get('position_matching', {}).get('score', 7)
        ]) / 5

        # 确定等级
        if total_score >= 9:
            grade = "A+"
        elif total_score >= 8:
            grade = "A"
        elif total_score >= 7:
            grade = "B+"
        elif total_score >= 6:
            grade = "B"
        else:
            grade = "C"

        report_data = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.now().isoformat(),
            "session_info": {
                "session_id": session_id,
                "session_name": session_info.get('session_name', ''),
                "room_id": session_info.get('room_id', ''),
                "round_index": round_index,
                "total_questions": len(qa_pairs)
            },
            "report_header": {
                "company_name": "Yeying面试官系统",
                "report_title": f"{session_info.get('session_name', '面试会话')}-模拟面试报告",
                "generated_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "overall_grade": grade,
                "total_score": round(total_score, 1)
            },
            "interviewer_comment": evaluation_result.get('interviewer_comment', {}),
            "comprehensive_analysis": evaluation_result.get('comprehensive_analysis', {}),
            "key_points_analysis": evaluation_result.get('key_points_analysis', {}),
            "question_analysis": evaluation_result.get('question_analysis', []),
            "original_qa_data": qa_pairs,
            "metadata": {
                "report_type": "interview_evaluation",
                "version": "1.0",
                "template": "huawei_style"
            }
        }

        return report_data

    def evaluate_single_question(self, question: str, answer: str, category: str) -> Optional[Dict[str, Any]]:
        """评价单个问题（可用于实时反馈）"""
        try:
            prompt = get_single_question_evaluation_prompt(question, answer, category)
            messages = [{"role": "user", "content": prompt}]
            response = self.qwen_client.chat_completion(messages, temperature=0.3, max_tokens=1000)

            return self._parse_evaluation_response(response)
        except Exception as e:
            logger.error(f"Error evaluating single question: {e}", exc_info=True)
            return None


# 全局评价服务实例
_evaluation_service = None

def get_evaluation_service():
    """获取评价服务实例（延迟初始化）"""
    global _evaluation_service
    if _evaluation_service is None:
        _evaluation_service = InterviewEvaluationService()
    return _evaluation_service