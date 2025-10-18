"""
简历解析提示词模块
"""


def get_resume_extraction_prompt(markdown_content: str) -> str:
    """
    从Markdown格式的简历中提取结构化数据的提示词

    Args:
        markdown_content: OCR解析后的Markdown格式简历内容

    Returns:
        LLM提示词
    """
    prompt = f"""你是一位专业的简历分析助手，请从以下Markdown格式的简历中提取结构化信息。

简历内容：
{markdown_content}

请仔细分析简历内容，提取以下关键信息并以JSON格式返回：

1. **姓名（name）**：候选人的姓名
2. **职位（position）**：应聘职位或目标职位，如果没有明确说明，根据技能和经验推断最合适的职位
3. **技能（skills）**：技能列表，包括编程语言、框架、工具等，提取所有提到的技术栈
4. **项目经验（projects）**：项目描述列表，每个项目包含项目名称、技术栈、职责等关键信息

**返回格式要求：**
- 必须返回标准的JSON格式
- 不要包含任何解释或额外的文字，只返回JSON对象
- skills和projects必须是数组
- 如果某个字段无法提取，使用空字符串或空数组

**JSON Schema：**
```json
{{
  "name": "候选人姓名",
  "position": "应聘职位或推断的职位",
  "skills": [
    "技能1",
    "技能2",
    "技能3"
  ],
  "projects": [
    "项目1：项目名称 - 技术栈 - 主要职责和成果",
    "项目2：项目名称 - 技术栈 - 主要职责和成果"
  ]
}}
```

**提取示例：**
如果简历中提到"精通Python、Django框架，熟悉MySQL数据库"，应提取为：
- skills: ["Python", "Django", "MySQL"]

如果简历中有"电商平台后端开发 - 使用Django开发了订单管理系统"，应提取为：
- projects: ["电商平台后端开发 - Django - 开发订单管理系统"]

请严格按照JSON格式返回，不要添加任何markdown代码块标记（如```json）："""

    return prompt


def get_resume_validation_prompt(extracted_data: dict, original_markdown: str) -> str:
    """
    验证和补充简历提取数据的提示词

    Args:
        extracted_data: 已提取的结构化数据
        original_markdown: 原始Markdown内容

    Returns:
        LLM提示词
    """
    prompt = f"""你是一位专业的简历审核助手，请检查以下提取的简历数据是否完整和准确。

原始简历（Markdown）：
{original_markdown}

已提取的数据（JSON）：
{extracted_data}

请执行以下任务：
1. 检查提取的信息是否准确，有无遗漏重要技能或项目
2. 如果有遗漏，补充遗漏的信息
3. 优化项目描述，使其更加清晰和结构化
4. 确保技能列表完整且去重

返回优化后的JSON数据，格式与原数据相同，不要添加解释："""

    return prompt
