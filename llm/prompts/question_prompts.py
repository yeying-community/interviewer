"""
面试题生成提示词模块
提供各种类型的面试题生成提示词，支持基于简历、技能、项目经验等生成针对性面试题
"""


def get_interview_question_prompt(resume_content: str, num_questions: int = 10) -> str:
    """
    生成基于简历内容的面试题提示词
    
    根据候选人的简历内容，生成针对性的技术面试题。会综合考虑候选人的技能栈、
    项目经验和职位要求，生成具有区分度的面试题目。
    
    Args:
        resume_content (str): 候选人简历内容，包括技能、项目经验等信息
        num_questions (int): 需要生成的面试题数量，默认10道
        
    Returns:
        str: 完整的面试题生成提示词，可直接用于大模型调用
    """
    prompt = f"""你是一位专业的技术面试官，请根据以下候选人简历生成{num_questions}道面试题。

候选人简历：
{resume_content}

请根据简历内容生成相应的面试题，要求：
1. 问题应该针对候选人的技术栈和项目经验
2. 包含基础技术问题、项目经验问题和深度技术问题
3. 问题应该具有一定的区分度，能够评估候选人的真实技术水平
4. 每个问题都以问号结尾
5. 请只输出问题，不要包含其他内容
6. 每行一个问题，使用数字编号（如"1. "开头）

请生成{num_questions}道面试题："""
    
    return prompt


def get_technical_deep_dive_prompt(skill: str, experience_level: str = "中级") -> str:
    """
    生成针对特定技能的深入技术问题提示词
    
    针对某个具体技能领域，生成深度技术问题来评估候选人的专业水平。
    问题会涉及该技能的原理、最佳实践、性能优化等多个维度。
    
    Args:
        skill (str): 技能名称，如"Python"、"React"、"机器学习"等
        experience_level (str): 候选人经验水平，如"初级"、"中级"、"高级"
        
    Returns:
        str: 针对特定技能的深度技术问题提示词
    """
    prompt = f"""作为技术面试官，请针对{skill}技能生成3-5道{experience_level}水平的深度技术问题。

要求：
1. 问题应该考查候选人对{skill}的深度理解
2. 包含原理、最佳实践、性能优化等方面
3. 问题具有实际应用价值
4. 每个问题都以问号结尾

请生成问题："""
    
    return prompt


def get_project_experience_prompt(project_description: str) -> str:
    """
    生成针对项目经验的面试题提示词
    
    基于候选人的具体项目经验，生成相关的面试题来评估其在项目中的
    技术贡献、解决问题的能力和系统设计思维。
    
    Args:
        project_description (str): 项目描述，包括项目背景、技术栈、主要功能等
        
    Returns:
        str: 项目经验相关面试题的提示词
    """
    prompt = f"""基于以下项目经验，生成5道面试问题来评估候选人的项目能力：

项目描述：
{project_description}

请生成问题，要求：
1. 考查项目中的技术难点和解决方案
2. 评估候选人的系统设计能力
3. 了解候选人在项目中的贡献和角色
4. 每个问题都以问号结尾

请生成问题："""
    
    return prompt


def get_scenario_based_prompt(position: str, skills: list) -> str:
    """
    生成场景化面试题提示词
    
    基于职位要求和技能栈，创建实际工作场景中的技术问题，
    评估候选人解决实际问题的能力和技术决策思维。
    
    Args:
        position (str): 目标职位名称，如"高级前端工程师"、"算法工程师"
        skills (list): 相关技能列表，如["Python", "机器学习", "TensorFlow"]
        
    Returns:
        str: 场景化面试题的提示词
    """
    # 取前5个技能，避免提示词过长
    skills_str = "、".join(skills[:5])
    
    prompt = f"""作为{position}的面试官，请基于以下技能栈创建3-5道场景化面试题：

技能栈：{skills_str}

要求：
1. 设计实际工作场景中可能遇到的技术问题
2. 考查候选人解决问题的思路和方法
3. 评估候选人的技术决策能力
4. 每个问题都以问号结尾

请生成场景化面试题："""
    
    return prompt