"""
通义千问(Qwen)API客户端
"""

import os
import re
from openai import OpenAI
from typing import List, Dict, Optional


class QwenClient:
    """通义千问API客户端类"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model_name: Optional[str] = None):
        """初始化Qwen客户端"""
        self.api_key = api_key or os.getenv('API_KEY')
        self.base_url = base_url or os.getenv('BASE_URL')
        self.model_name = model_name or os.getenv('MODEL_NAME', 'qwen-turbo')
        
        if not self.api_key:
            raise ValueError("API_KEY is required")
        if not self.base_url:
            raise ValueError("BASE_URL is required")
            
        # 初始化OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       model: Optional[str] = None, 
                       temperature: float = 0.7,
                       max_tokens: int = 2000) -> str:
        """发送聊天请求到Qwen模型"""
        try:
            response = self.client.chat.completions.create(
                model=model or self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
                
        except Exception as e:
            raise Exception(f"调用Qwen API失败: {str(e)}")
    
    def generate_questions(self, resume_content: str, question_types: Dict[str, int] = None) -> Dict[str, List[str]]:
        """基于简历内容生成面试题"""
        if question_types is None:
            question_types = {
                "基础题": 3,
                "项目题": 3, 
                "场景题": 3
            }
        
        try:
            from llm.prompts.question_prompts import interview_prompt
        except ImportError:
            raise ImportError("无法导入提示词模块")
        
        result = {}
        
        for category, num in question_types.items():
            try:
                prompt = interview_prompt(resume_content, category, num)
                messages = [{"role": "user", "content": prompt}]
                response = self.chat_completion(messages, temperature=0.7)
                questions = self._parse_questions_from_response(response)
                result[category] = questions[:num] if len(questions) > num else questions
                
            except Exception as e:
                print(f"生成{category}时出错: {e}")
                result[category] = []
        
        return result
    
    def _parse_questions_from_response(self, response: str) -> List[str]:
        """从LLM响应中解析面试题列表"""
        if not response or not response.strip():
            return []
        
        questions = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 移除编号格式
            line = re.sub(r'^\d+[.\、\)]\s*', '', line)
            line = re.sub(r'^[-*•]\s*', '', line)
            
            # 过滤有效问题
            if (len(line) > 10 and 
                any(keyword in line for keyword in ['?', '？', '如何', '什么', '为什么', '请描述', '请解释'])):
                questions.append(line)
        
        # 去重
        seen = set()
        unique_questions = []
        for q in questions:
            if q not in seen:
                seen.add(q)
                unique_questions.append(q)
        
        return unique_questions