"""
面试题生成处理器模块
根据简历数据生成面试题并存储到questions.json文件

该模块位于 llm/processors/ 目录下，提供面试题生成的核心功能：
1. 读取 tests/data/resume.json 中的简历数据
2. 调用 QwenClient 生成针对性面试题
3. 将生成的面试题保存到 tests/data/questions.json
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from llm.clients.qwen_client import QwenClient
from dotenv import load_dotenv

def load_resume_data(resume_path: str = "tests/data/resume.json") -> dict:
    """
    加载简历数据
    
    从指定路径的JSON文件中读取简历数据，包含候选人的基本信息、
    技能栈和项目经验等信息。
    
    Args:
        resume_path (str): 简历文件路径，通常为tests/data/resume.json
        
    Returns:
        dict: 包含简历信息的字典，格式包含name、position、skills、projects等字段
        
    Raises:
        FileNotFoundError: 当文件不存在时
        json.JSONDecodeError: 当JSON格式错误时
    """
    try:
        with open(resume_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"简历文件未找到: {resume_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"简历文件JSON格式错误: {e}")

def format_resume_content(resume_data: dict) -> str:
    """
    格式化简历内容为文本
    
    将JSON格式的简历数据转换为结构化的文本格式，便于LLM理解和处理。
    格式化后的文本包含候选人姓名、职位、技能列表和项目经验。
    
    Args:
        resume_data (dict): 简历数据字典，包含基本信息和详细内容
        
    Returns:
        str: 格式化后的简历文本，包含完整的候选人信息
    """
    content = f"""
姓名：{resume_data.get('name', '')}
职位：{resume_data.get('position', '')}

技能：
"""
    
    # 格式化技能列表
    skills = resume_data.get('skills', [])
    for i, skill in enumerate(skills, 1):
        content += f"{i}. {skill}\n"
    
    content += "\n项目经验：\n"
    # 格式化项目经验
    projects = resume_data.get('projects', [])
    for i, project in enumerate(projects, 1):
        content += f"{i}. {project}\n"
    
    return content.strip()

def save_questions_to_file(questions: list, output_path: str = "tests/data/questions.json", **metadata):
    """
    保存面试题到文件
    
    将生成的面试题列表保存为JSON格式文件，包含题目列表、
    题目数量和生成时间等元信息。
    
    Args:
        questions (list): 面试题列表，每个元素为一道面试题的字符串
        output_path (str): 输出文件路径，通常为tests/data/questions.json
        **metadata: 额外的元数据，如round_index等
        
    Raises:
        IOError: 当文件保存失败时
    """
    qa_data = {
        'questions': questions,
        'total_count': len(questions),
        'generated_at': datetime.now().isoformat(),
        **metadata
    }
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(qa_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise IOError(f"保存文件失败: {e}")

def generate_interview_questions(resume_path: str = "tests/data/resume.json", 
                                num_questions: int = 10,
                                output_path: str = "tests/data/questions.json") -> dict:
    """
    生成面试题的主要处理函数
    
    这是模块的核心功能函数，负责完整的面试题生成流程：
    1. 加载环境变量配置
    2. 读取简历数据
    3. 初始化Qwen客户端
    4. 调用LLM生成面试题
    5. 保存生成结果到文件
    
    Args:
        resume_path (str): 简历文件路径
        num_questions (int): 生成问题数量，默认10道
        output_path (str): 输出文件路径
        
    Returns:
        dict: 包含生成结果的字典，包含questions、success等字段
        
    Raises:
        Exception: 当生成过程中出现任何错误时
    """
    # 加载环境变量配置（包括API密钥等）
    load_dotenv()
    
    try:
        # 第一步：加载简历数据
        resume_data = load_resume_data(resume_path)
        
        # 第二步：格式化简历内容为LLM可处理的文本格式
        resume_content = format_resume_content(resume_data)
        
        # 第三步：初始化Qwen客户端
        client = QwenClient()
        
        # 第四步：生成面试题
        questions = client.generate_questions(resume_content, num_questions=num_questions)
        
        if not questions:
            raise ValueError("未能生成任何面试题")
        
        # 第五步：保存面试题到文件
        save_questions_to_file(questions, output_path, candidate_name=resume_data.get('name', '未知'))
        
        return {
            'success': True,
            'questions': questions,
            'total_count': len(questions),
            'candidate_name': resume_data.get('name', '未知'),
            'message': f'成功生成 {len(questions)} 道面试题'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'questions': [],
            'total_count': 0,
            'message': f'生成面试题失败: {str(e)}'
        }

def batch_generate_questions(resume_path: str = "tests/data/resume.json",
                           output_dir: str = "tests/data/",
                           batch_configs: list = None) -> list:
    """
    批量生成不同类型的面试题
    
    支持批量生成多种类型的面试题，如基础题、项目题、场景题等。
    
    Args:
        resume_path (str): 简历文件路径
        output_dir (str): 输出目录
        batch_configs (list): 批量配置列表，包含不同类型的生成参数
        
    Returns:
        list: 包含所有生成结果的列表
    """
    if batch_configs is None:
        batch_configs = [
            {'type': 'basic', 'num_questions': 5, 'filename': 'basic_questions.json'},
            {'type': 'project', 'num_questions': 5, 'filename': 'project_questions.json'},
            {'type': 'scenario', 'num_questions': 5, 'filename': 'scenario_questions.json'}
        ]
    
    results = []
    
    for config in batch_configs:
        output_path = os.path.join(output_dir, config['filename'])
        result = generate_interview_questions(
            resume_path=resume_path,
            num_questions=config['num_questions'],
            output_path=output_path
        )
        result['type'] = config['type']
        results.append(result)
    
    return results

