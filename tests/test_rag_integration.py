#!/usr/bin/env python3
"""
RAG 服务对接测试脚本
测试 Interviewer 与 Yeying-RAG 的集成功能
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from backend.clients.rag.rag_client import get_rag_client
from backend.common.logger import get_logger

logger = get_logger(__name__)


def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_rag_connection():
    """测试 RAG 服务连接"""
    print_section("测试 1: RAG 服务连接")

    try:
        rag_client = get_rag_client()
        print(f"✅ RAG 客户端初始化成功")
        print(f"   API URL: {rag_client.api_url}")
        print(f"   Timeout: {rag_client.timeout}s")
        return True, rag_client
    except Exception as e:
        print(f"❌ RAG 客户端初始化失败: {e}")
        return False, None


def test_create_memory(rag_client):
    """测试创建记忆体"""
    print_section("测试 2: 创建记忆体")

    try:
        memory_id = rag_client.create_memory(app="interviewer")
        print(f"✅ 记忆体创建成功")
        print(f"   Memory ID: {memory_id}")
        return True, memory_id
    except Exception as e:
        print(f"❌ 创建记忆体失败: {e}")
        return False, None


def test_generate_questions(rag_client, memory_id):
    """测试生成问题"""
    print_section("测试 3: 生成面试问题")

    # 模拟简历数据
    resume_data = {
        "name": "张三",
        "position": "Python后端工程师",
        "company": "字节跳动",
        "skills": ["Python", "Django", "FastAPI", "Redis", "PostgreSQL"],
        "projects": [
            "电商平台后端系统 - 负责订单模块开发",
            "数据分析平台 - 使用 FastAPI 构建 RESTful API"
        ]
    }

    print(f"📝 简历数据:")
    print(f"   姓名: {resume_data['name']}")
    print(f"   职位: {resume_data['position']}")
    print(f"   公司: {resume_data['company']}")
    print(f"   技能: {', '.join(resume_data['skills'][:3])} ...")

    try:
        result = rag_client.generate_questions(
            memory_id=memory_id,
            resume_data=resume_data,
            company=resume_data.get('company'),
            target_position=resume_data.get('position')
        )

        questions = result.get('questions', [])
        print(f"\n✅ 问题生成成功，共生成 {len(questions)} 个问题:")
        for i, q in enumerate(questions[:5], 1):  # 只显示前5个
            print(f"   {i}. {q}")

        if len(questions) > 5:
            print(f"   ... 还有 {len(questions) - 5} 个问题")

        return True, questions
    except Exception as e:
        print(f"❌ 生成问题失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_push_message(rag_client, memory_id):
    """测试推送消息到记忆体"""
    print_section("测试 4: 推送问答到记忆体")

    # 模拟完整的问答数据
    qa_data = {
        "round_info": {
            "round_id": "test-round-001",
            "session_id": "test-session-001",
            "room_id": "test-room-001",
            "round_index": 0,
            "total_questions": 3,
            "completed_at": "2024-01-01T12:00:00"
        },
        "qa_pairs": [
            {
                "question_index": 0,
                "category": "技能",
                "question": "请介绍一下Python的GIL（全局解释器锁）",
                "answer": "GIL是Python解释器中的一个互斥锁，确保同一时刻只有一个线程在执行Python字节码。这主要是为了保护对Python对象的访问...",
                "answered_at": "2024-01-01T12:05:00"
            },
            {
                "question_index": 1,
                "category": "项目经验",
                "question": "在电商平台项目中，如何处理高并发订单请求？",
                "answer": "我们使用了Redis作为缓存层，采用分布式锁防止超卖，使用消息队列异步处理订单...",
                "answered_at": "2024-01-01T12:10:00"
            }
        ]
    }

    print(f"📤 推送数据:")
    print(f"   轮次: Round {qa_data['round_info']['round_index']}")
    print(f"   问答对数量: {len(qa_data['qa_pairs'])}")

    try:
        minio_url = f"test/qa_round_0.json"
        description = json.dumps(qa_data, ensure_ascii=False)

        result = rag_client.push_message(
            memory_id=memory_id,
            url=minio_url,
            description=description
        )

        print(f"\n✅ 问答推送成功")
        print(f"   URL: {minio_url}")
        print(f"   状态: {result.get('status', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ 推送问答失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_questions_with_memory(rag_client, memory_id):
    """测试基于记忆生成问题（第二轮）"""
    print_section("测试 5: 基于历史对话生成新问题")

    resume_data = {
        "name": "张三",
        "position": "Python后端工程师",
        "company": "字节跳动",
        "skills": ["Python", "Django", "FastAPI", "Redis", "PostgreSQL"],
        "projects": ["电商平台后端系统", "数据分析平台"]
    }

    print(f"📝 现在 RAG 应该已经有了第一轮的问答记忆")
    print(f"   再次生成问题，应该会考虑历史对话...")

    try:
        result = rag_client.generate_questions(
            memory_id=memory_id,
            resume_data=resume_data,
            company=resume_data.get('company'),
            target_position=resume_data.get('position')
        )

        questions = result.get('questions', [])
        print(f"\n✅ 第二轮问题生成成功，共生成 {len(questions)} 个问题:")
        for i, q in enumerate(questions[:5], 1):
            print(f"   {i}. {q}")

        if len(questions) > 5:
            print(f"   ... 还有 {len(questions) - 5} 个问题")

        return True
    except Exception as e:
        print(f"❌ 生成问题失败: {e}")
        return False


def test_cleanup(rag_client, memory_id):
    """清理测试数据"""
    print_section("测试 6: 清理测试数据")

    try:
        deleted = rag_client.clear_memory(memory_id=memory_id)
        print(f"✅ 记忆体清理成功")
        print(f"   删除了 {deleted} 条记录")
        return True
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return False


def main():
    """主测试流程"""
    print("\n" + "🧪 " * 30)
    print("   Interviewer <-> Yeying-RAG 对接测试")
    print("🧪 " * 30)

    results = []

    # 测试 1: 连接
    success, rag_client = test_rag_connection()
    results.append(("RAG 服务连接", success))
    if not success:
        print("\n❌ RAG 服务不可用，测试终止")
        print("   请确保:")
        print("   1. Yeying-RAG 服务已启动（默认端口 8000）")
        print("   2. .env 文件中 RAG_API_URL 配置正确")
        return

    # 测试 2: 创建记忆体
    success, memory_id = test_create_memory(rag_client)
    results.append(("创建记忆体", success))
    if not success:
        print("\n❌ 无法创建记忆体，后续测试跳过")
        return

    # 测试 3: 生成问题
    success, questions = test_generate_questions(rag_client, memory_id)
    results.append(("生成问题（首轮）", success))

    # 测试 4: 推送消息
    success = test_push_message(rag_client, memory_id)
    results.append(("推送问答到记忆", success))

    # 测试 5: 基于记忆生成问题
    success = test_generate_questions_with_memory(rag_client, memory_id)
    results.append(("生成问题（基于记忆）", success))

    # 测试 6: 清理
    success = test_cleanup(rag_client, memory_id)
    results.append(("清理测试数据", success))

    # 总结
    print_section("测试总结")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"\n测试结果: {passed}/{total} 通过\n")

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}  {test_name}")

    if passed == total:
        print("\n🎉 所有测试通过！RAG 对接工作正常！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查日志")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
