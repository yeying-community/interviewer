"""
面试题生成服务
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.services.interview_service import RoundService
from backend.utils.minio_client import upload_questions_data, download_resume_data
from llm.clients.qwen_client import QwenClient


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
                raise ValueError("无法加载简历数据")
            
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
                print(f"Warning: Failed to save questions to MinIO for round {round_obj.id}")
            
            return {
                'success': True,
                'round_id': round_obj.id,
                'questions': all_questions,
                'round_index': round_obj.round_index,
                'categorized_questions': categorized_questions
            }
            
        except Exception as e:
            print(f"Error generating questions: {e}")
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


# 全局服务实例
question_generation_service = QuestionGenerationService()