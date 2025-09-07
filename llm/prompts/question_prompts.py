"""
面试题生成提示词模块
"""


def get_interview_question_prompt(resume_content: str, num_questions: int = 10) -> str:
    """生成基于简历内容的面试题提示词"""
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


def get_categorized_interview_prompt(resume_content: str, category: str, num_questions: int = 3) -> str:
    """生成分类面试题提示词"""
    
    category_instructions = {
        "基础题": "重点考查基础技术知识、语言特性、数据结构和算法等基础概念",
        "项目题": "重点考查项目经验、架构设计、技术选型、团队协作等项目相关问题", 
        "场景题": "重点考查问题解决能力、技术决策、性能优化等实际工作场景问题"
    }
    
    instruction = category_instructions.get(category, "生成相关技术问题")
    
    prompt = f"""你是一位专业的技术面试官，请根据以下候选人简历生成{num_questions}道{category}。

候选人简历：
{resume_content}

{category}要求：
{instruction}

生成要求：
1. 问题应该针对候选人的技术栈和项目经验
2. 问题应该具有一定的区分度
3. 每个问题都以问号结尾
4. 请只输出问题，不要包含其他内容
5. 每行一个问题，使用数字编号

请生成{num_questions}道{category}："""
    
    return prompt