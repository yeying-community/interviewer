"""
简历解析服务
"""

import json
import re
from typing import Dict, Any, Optional
from backend.clients.llm.qwen_client import QwenClient
from backend.clients.llm.prompts.resume_prompts import get_resume_extraction_prompt
from backend.common.logger import get_logger

logger = get_logger(__name__)


class ResumeParser:
    """简历内容解析器，从Markdown提取结构化数据"""

    def __init__(self):
        self.qwen_client = QwenClient()

    def extract_resume_data(self, markdown_content: str) -> Optional[Dict[str, Any]]:
        """
        从Markdown内容中提取结构化简历数据

        Args:
            markdown_content: OCR解析后的Markdown格式内容

        Returns:
            结构化简历数据字典，格式：
            {
                "name": "姓名",
                "position": "职位",
                "skills": ["技能1", "技能2"],
                "projects": ["项目1", "项目2"]
            }
        """
        try:
            if not markdown_content or not markdown_content.strip():
                logger.error("Empty markdown content")
                return None

            # 生成提取提示词
            prompt = get_resume_extraction_prompt(markdown_content)

            # 调用LLM提取结构化数据
            messages = [{"role": "user", "content": prompt}]
            response = self.qwen_client.chat_completion(messages, temperature=0.3, max_tokens=2000)

            if not response:
                logger.error("No response from LLM")
                return None

            # 解析JSON响应
            resume_data = self._parse_json_response(response)

            if not resume_data:
                logger.error("Failed to parse JSON from LLM response")
                return None

            # 验证数据完整性
            validated_data = self._validate_resume_data(resume_data)

            return validated_data

        except Exception as e:
            logger.error(f"Error extracting resume data: {e}", exc_info=True)
            return None

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析LLM返回的JSON响应"""
        try:
            # 清理响应内容，移除可能的markdown代码块标记
            cleaned_response = response.strip()

            # 移除```json 和 ```标记
            if cleaned_response.startswith('```'):
                # 找到第一个{和最后一个}
                start_idx = cleaned_response.find('{')
                end_idx = cleaned_response.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    cleaned_response = cleaned_response[start_idx:end_idx + 1]

            # 尝试解析JSON
            resume_data = json.loads(cleaned_response)
            return resume_data

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.debug(f"Response content: {response[:500]}")

            # 尝试使用正则表达式提取JSON对象
            try:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    resume_data = json.loads(json_match.group(0))
                    return resume_data
            except Exception as ex:
                logger.error(f"Regex extraction also failed: {ex}")

            return None

        except Exception as e:
            logger.error(f"Error parsing JSON response: {e}", exc_info=True)
            return None

    def _validate_resume_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证和规范化简历数据"""
        validated = {
            "name": "",
            "position": "",
            "skills": [],
            "projects": []
        }

        # 验证姓名
        if "name" in data and data["name"]:
            validated["name"] = str(data["name"]).strip()

        # 验证职位
        if "position" in data and data["position"]:
            validated["position"] = str(data["position"]).strip()

        # 验证技能列表
        if "skills" in data and isinstance(data["skills"], list):
            # 去重并清理
            skills_set = set()
            for skill in data["skills"]:
                if skill and isinstance(skill, str):
                    cleaned_skill = skill.strip()
                    if cleaned_skill:
                        skills_set.add(cleaned_skill)
            validated["skills"] = sorted(list(skills_set))

        # 验证项目列表
        if "projects" in data and isinstance(data["projects"], list):
            projects = []
            for project in data["projects"]:
                if project and isinstance(project, str):
                    cleaned_project = project.strip()
                    if cleaned_project:
                        projects.append(cleaned_project)
            validated["projects"] = projects

        return validated


# 全局服务实例
_resume_parser = None


def get_resume_parser() -> ResumeParser:
    """获取简历解析器实例（单例模式）"""
    global _resume_parser
    if _resume_parser is None:
        _resume_parser = ResumeParser()
    return _resume_parser
