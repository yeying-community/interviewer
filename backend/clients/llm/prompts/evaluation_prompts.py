"""
面试评价相关prompt模板
"""

from typing import Dict, List, Any


def get_interview_evaluation_prompt(qa_data: Dict[str, Any]) -> str:
    """
    生成面试评价的prompt模板
    基于华为面试报告格式进行评价
    """
    qa_pairs = qa_data.get('qa_pairs', [])
    session_info = qa_data.get('session_info', {})

    qa_content = ""
    for i, qa in enumerate(qa_pairs, 1):
        qa_content += f"""
问题{i}：{qa.get('question', '')}
分类：{qa.get('category', '')}
回答：{qa.get('answer', '')}
"""

    prompt = f"""
请你作为专业的技术面试官，对以下面试QA进行全面评价。

面试信息：
- 会话名称：{session_info.get('session_name', '')}
- 总题数：{len(qa_pairs)}

面试QA内容：
{qa_content}

请按照以下JSON格式返回评价结果：

{{
    "interviewer_comment": {{
        "summary": "面试官总体评价（100-200字）",
        "suggestions": "改进建议（100-200字）"
    }},
    "comprehensive_analysis": {{
        "content_completeness": {{
            "score": 8,
            "comment": "内容完整度评价"
        }},
        "highlight_prominence": {{
            "score": 7,
            "comment": "亮点突出度评价"
        }},
        "logical_clarity": {{
            "score": 7,
            "comment": "逻辑清晰度评价"
        }},
        "expression_ability": {{
            "score": 8,
            "comment": "表达能力评价"
        }},
        "position_matching": {{
            "score": 8,
            "comment": "岗位契合度评价"
        }}
    }},
    "key_points_analysis": {{
        "project_depth": {{
            "level": "中",
            "description": "项目深度分析",
            "can_strengthen": true
        }},
        "personality_potential": {{
            "level": "高",
            "description": "个性潜质分析",
            "can_strengthen": false
        }},
        "professional_knowledge": {{
            "level": "中",
            "description": "专业知识点分析",
            "can_strengthen": true
        }},
        "soft_skills": {{
            "level": "高",
            "description": "软素质分析",
            "can_strengthen": false
        }}
    }},
    "question_analysis": [
        {{
            "question_number": 1,
            "question": "问题内容",
            "category": "问题分类",
            "key_points": "本题考点",
            "improvement_suggestions": "改进建议",
            "reference_answer": "参考回答"
        }}
    ]
}}

评价要求：
1. 分数范围1-10分，要客观公正
2. 评价要具体，避免空泛
3. 改进建议要有针对性和可操作性
4. 参考回答要专业且简洁
5. 保持专业的面试官语气
6. 针对每个问题都要给出具体的分析和改进建议
7. 考点分析要准确，体现问题的技术深度
"""
    return prompt


def get_single_question_evaluation_prompt(question: str, answer: str, category: str) -> str:
    """
    单个问题的详细评价prompt
    用于生成更细致的单题分析
    """
    prompt = f"""
请对以下单个面试问题进行详细评价：

问题：{question}
分类：{category}
回答：{answer}

请按照以下JSON格式返回评价结果：

{{
    "question_score": 7,
    "key_points": "本题主要考察的技术点",
    "answer_analysis": {{
        "strengths": ["回答的优点1", "回答的优点2"],
        "weaknesses": ["不足之处1", "不足之处2"],
        "missing_points": ["遗漏的关键点1", "遗漏的关键点2"]
    }},
    "improvement_suggestions": "具体的改进建议",
    "reference_answer": "标准参考答案（简洁版）",
    "difficulty_level": "简单/中等/困难"
}}

评价要求：
1. 分析要客观具体
2. 优缺点要有依据
3. 改进建议要可操作
4. 参考答案要专业准确
"""
    return prompt


def get_report_summary_prompt(evaluation_data: Dict[str, Any]) -> str:
    """
    生成报告总结的prompt
    用于生成最终的面试官评语
    """
    scores = evaluation_data.get('comprehensive_analysis', {})

    prompt = f"""
基于以下评价数据，生成专业的面试官总结评语：

综合分析得分：
- 内容完整度：{scores.get('content_completeness', {}).get('score', 0)}分
- 亮点突出度：{scores.get('highlight_prominence', {}).get('score', 0)}分
- 逻辑清晰度：{scores.get('logical_clarity', {}).get('score', 0)}分
- 表达能力：{scores.get('expression_ability', {}).get('score', 0)}分
- 岗位契合度：{scores.get('position_matching', {}).get('score', 0)}分

请生成：
1. 面试官总体评价（100-200字，客观专业）
2. 改进建议（100-200字，具体可操作）
3. 面试结果建议（通过/待定/不通过，并说明理由）

要求：
- 语气专业客观
- 评价具体有据
- 建议实用可行
"""
    return prompt