"""
通义千问(Qwen)API客户端
提供与通义千问大模型交互的能力，支持面试题生成等功能
"""

import os
import requests
import json
from typing import List, Dict, Optional


class QwenClient:
    """
    通义千问API客户端类
    
    用于与阿里云通义千问大模型进行交互，支持聊天对话和面试题生成功能
    
    Attributes:
        api_key (str): API密钥
        base_url (str): API基础URL
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化Qwen客户端
        
        Args:
            api_key (Optional[str]): API密钥，如果未提供则从环境变量API_KEY获取
            base_url (Optional[str]): API基础URL，如果未提供则从环境变量BASE_URL获取
            
        Raises:
            ValueError: 当API_KEY或BASE_URL未设置时抛出异常
        """
        self.api_key = api_key or os.getenv('API_KEY')
        self.base_url = base_url or os.getenv('BASE_URL')
        
        if not self.api_key:
            raise ValueError("API_KEY is required")
        if not self.base_url:
            raise ValueError("BASE_URL is required")
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       model: str = "qwen-turbo", 
                       temperature: float = 0.7,
                       max_tokens: int = 2000) -> str:
        """
        发送聊天请求到Qwen模型
        
        Args:
            messages (List[Dict[str, str]]): 消息列表，格式为[{"role": "user", "content": "..."}]
            model (str): 模型名称，默认为"qwen-turbo"
            temperature (float): 温度参数，控制输出的随机性，范围0-1，默认0.7
            max_tokens (int): 最大输出token数，默认2000
            
        Returns:
            str: 模型响应内容
            
        Raises:
            Exception: 当请求失败或响应格式错误时抛出异常
        """
        # 构建请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建请求数据
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            # 发送HTTP POST请求
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            # 解析响应结果
            result = response.json()
            return result['choices'][0]['message']['content']
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
        except KeyError as e:
            raise Exception(f"Invalid response format: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error: {e}")
    
    def generate_questions(self, resume_content: str, num_questions: int = 10) -> List[str]:
        """
        根据简历内容生成面试题
        
        Args:
            resume_content (str): 简历内容文本
            num_questions (int): 生成问题数量，默认10道
            
        Returns:
            List[str]: 面试题列表
            
        Raises:
            Exception: 当生成面试题失败时抛出异常
        """
        # 动态导入避免循环导入问题
        try:
            from llm.prompts.question_prompts import get_interview_question_prompt
        except ImportError:
            # 如果相对导入失败，尝试绝对导入
            from llm.prompts.question_prompts import get_interview_question_prompt
        
        # 生成面试题提示词
        prompt = get_interview_question_prompt(resume_content, num_questions)
        
        # 构建消息格式
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # 调用模型生成内容，使用较高温度以增加多样性
        response = self.chat_completion(messages, temperature=0.8)
        
        # 解析响应，提取问题列表
        questions = self._parse_questions(response)
        return questions
    
    def _parse_questions(self, response: str) -> List[str]:
        """
        解析模型响应，提取问题列表
        
        该方法负责从模型的文本响应中识别并提取出格式化的面试题
        支持多种问题编号格式：数字序号、中文序号、短横线等
        
        Args:
            response (str): 模型响应文本
            
        Returns:
            List[str]: 解析后的问题列表
        """
        questions = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 移除序号和标点符号，提取纯问题内容
            if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.')):
                # 处理数字序号格式：1. 问题内容
                question = line.split('.', 1)[1].strip()
            elif line.startswith(('一、', '二、', '三、', '四、', '五、', '六、', '七、', '八、', '九、', '十、')):
                # 处理中文序号格式：一、问题内容
                question = line.split('、', 1)[1].strip()
            elif line.startswith('- '):
                # 处理短横线格式：- 问题内容
                question = line[2:].strip()
            else:
                # 其他格式直接使用原文
                question = line
                
            # 检查是否是有效问题（包含中英文问号）
            if question and ('?' in question or '？' in question):
                questions.append(question)
        
        return questions