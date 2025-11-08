"""
RAG 服务客户端
负责与 Yeying-RAG 服务进行交互
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from backend.common.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


class RAGClient:
    """Yeying-RAG 服务客户端"""

    def __init__(self):
        """初始化 RAG 客户端"""
        self.api_url = os.getenv('RAG_API_URL', 'http://localhost:8000')
        self.timeout = int(os.getenv('RAG_TIMEOUT', '30'))

        if not self.api_url:
            raise ValueError("RAG_API_URL not configured in environment variables")

        logger.info(f"RAG Client initialized with API URL: {self.api_url}")

    def create_memory(self, app: str = "interviewer", params: Optional[Dict[str, Any]] = None) -> str:
        """
        创建新的记忆体

        Args:
            app: 应用名称，默认为 "interviewer"
            params: 可选参数

        Returns:
            memory_id: 记忆体ID
        """
        try:
            url = f"{self.api_url}/memory/create"
            payload = {
                "app": app,
                "params": params or {}
            }

            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()
            memory_id = result.get('memory_id')

            if not memory_id:
                raise ValueError("No memory_id returned from RAG service")

            logger.info(f"Created RAG memory: {memory_id}")
            return memory_id

        except requests.RequestException as e:
            logger.error(f"Error creating RAG memory: {e}", exc_info=True)
            raise Exception(f"Failed to create RAG memory: {e}")

    def generate_questions(
        self,
        memory_id: str,
        resume_url: str,
        company: Optional[str] = None,
        target_position: Optional[str] = None,
        jd_id: Optional[str] = None,
        jd_top_k: int = 3,
        memory_top_k: int = 3,
        max_chars: int = 4000
    ) -> Dict[str, Any]:
        """
        生成面试问题

        Args:
            memory_id: 记忆体ID
            resume_url: 简历在MinIO中的路径（如：rooms/{room_id}/resume.json）
            company: 公司名称（用于JD检索过滤）
            target_position: 目标职位（用于JD语义检索）
            jd_id: 用户上传的自定义JD ID（可选，优先使用）
            jd_top_k: JD检索数量
            memory_top_k: 记忆检索数量
            max_chars: 最大字符数

        Returns:
            生成结果，包含 questions 列表和 context_used
        """
        try:
            url = f"{self.api_url}/query"
            payload = {
                "app": "interviewer",
                "memory_id": memory_id,
                "resume_url": resume_url,
                "company": company,
                "target_position": target_position,
                "jd_id": jd_id,
                "jd_top_k": jd_top_k,
                "memory_top_k": memory_top_k,
                "max_chars": max_chars
            }

            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()
            questions = result.get('questions', [])

            if not questions:
                logger.warning("No questions returned from RAG service")
            else:
                logger.info(f"Generated {len(questions)} questions from RAG")

            return {
                'questions': questions,
                'context_used': result.get('context_used')
            }

        except requests.RequestException as e:
            logger.error(f"Error generating questions from RAG: {e}", exc_info=True)
            raise Exception(f"Failed to generate questions from RAG: {e}")

    def upload_jd(
        self,
        memory_id: str,
        company: Optional[str] = None,
        position: Optional[str] = None,
        content: str = ""
    ) -> str:
        """
        上传自定义 JD

        Args:
            memory_id: 记忆体ID
            company: 公司名称
            position: 职位名称
            content: JD 内容

        Returns:
            jd_id: 上传成功后返回的 JD ID
        """
        try:
            url = f"{self.api_url}/query/uploadJD"
            payload = {
                "app": "interviewer",
                "memory_id": memory_id,
                "company": company,
                "position": position,
                "content": content
            }

            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()
            jd_id = result.get('jd_id')

            if not jd_id:
                raise ValueError("No jd_id returned from RAG service")

            logger.info(f"Uploaded JD successfully: {jd_id}")
            return jd_id

        except requests.RequestException as e:
            logger.error(f"Error uploading JD to RAG: {e}", exc_info=True)
            raise Exception(f"Failed to upload JD to RAG: {e}")

    def push_message(
        self,
        memory_id: str,
        url: str,
        description: Optional[str] = None,
        app: str = "interviewer"
    ) -> Dict[str, Any]:
        """
        推送消息到记忆体

        Args:
            memory_id: 记忆体ID
            url: 消息的唯一标识（MinIO路径）
            description: 消息内容（可选）
            app: 应用名称

        Returns:
            推送结果
        """
        try:
            api_url = f"{self.api_url}/memory/push"
            payload = {
                "memory_id": memory_id,
                "app": app,
                "url": url,
                "description": description
            }

            response = requests.post(api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()
            logger.info(f"Pushed message to RAG memory {memory_id}: {url}")

            return result

        except requests.RequestException as e:
            logger.error(f"Error pushing message to RAG: {e}", exc_info=True)
            raise Exception(f"Failed to push message to RAG: {e}")

    def delete_message(
        self,
        memory_id: str,
        url: str,
        app: str = "interviewer"
    ) -> bool:
        """
        删除记忆中的消息

        Args:
            memory_id: 记忆体ID
            url: 消息的唯一标识
            app: 应用名称

        Returns:
            是否删除成功
        """
        try:
            api_url = f"{self.api_url}/memory/delete"
            payload = {
                "memory_id": memory_id,
                "app": app,
                "url": url
            }

            response = requests.post(api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            logger.info(f"Deleted message from RAG memory {memory_id}: {url}")
            return True

        except requests.RequestException as e:
            logger.error(f"Error deleting message from RAG: {e}", exc_info=True)
            return False

    def clear_memory(
        self,
        memory_id: str,
        app: str = "interviewer"
    ) -> int:
        """
        清空记忆体

        Args:
            memory_id: 记忆体ID
            app: 应用名称

        Returns:
            删除的消息数量
        """
        try:
            api_url = f"{self.api_url}/memory/clear"
            payload = {
                "memory_id": memory_id,
                "app": app
            }

            response = requests.post(api_url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()
            deleted = result.get('deleted', 0)

            logger.info(f"Cleared RAG memory {memory_id}: {deleted} messages deleted")
            return deleted

        except requests.RequestException as e:
            logger.error(f"Error clearing RAG memory: {e}", exc_info=True)
            return 0


# 全局单例
_rag_client = None


def get_rag_client() -> RAGClient:
    """
    获取 RAG 客户端实例（单例模式）

    Returns:
        RAGClient 实例
    """
    global _rag_client
    if _rag_client is None:
        _rag_client = RAGClient()
    return _rag_client
