#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型和服务测试
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 设置测试数据库
os.environ['DATABASE_PATH'] = ':memory:'  # 使用内存数据库

from backend.models.models import init_database, Room, Session, Round
from backend.services.interview_service import RoomService, SessionService, RoundService


class TestDatabaseModels(unittest.TestCase):
    """数据库模型测试"""
    
    def setUp(self):
        """每个测试前的设置"""
        # 重新连接数据库以确保表存在
        from backend.models.models import database, Room, Session, Round
        if not database.is_closed():
            database.close()
        database.connect()
        database.create_tables([Room, Session, Round], safe=True)
    
    def tearDown(self):
        """每个测试后的清理"""
        from backend.models.models import database, Room, Session, Round
        # 清理数据
        Round.delete().execute()
        Session.delete().execute()
        Room.delete().execute()
        database.close()
    
    def test_room_creation(self):
        """测试房间创建"""
        room = RoomService.create_room("测试房间")
        self.assertIsNotNone(room)
        self.assertEqual(room.name, "测试房间")
        self.assertTrue(room.memory_id.startswith("memory_"))
    
    def test_session_creation(self):
        """测试会话创建"""
        room = RoomService.create_room("测试房间")
        session = SessionService.create_session(room.id, "测试会话")
        
        self.assertIsNotNone(session)
        self.assertEqual(session.name, "测试会话")
        self.assertEqual(session.room.id, room.id)
        self.assertEqual(session.status, "active")
    
    def test_round_creation(self):
        """测试轮次创建"""
        room = RoomService.create_room("测试房间")
        session = SessionService.create_session(room.id, "测试会话")
        questions = ["问题1", "问题2", "问题3"]
        
        round_obj = RoundService.create_round(session.id, questions)
        
        self.assertIsNotNone(round_obj)
        self.assertEqual(round_obj.session.id, session.id)
        self.assertEqual(round_obj.questions_count, 3)
        self.assertEqual(round_obj.round_index, 0)
    
    def test_room_sessions_relationship(self):
        """测试房间和会话的关系"""
        room = RoomService.create_room("测试房间")
        session1 = SessionService.create_session(room.id, "会话1")
        session2 = SessionService.create_session(room.id, "会话2")
        
        sessions = SessionService.get_sessions_by_room(room.id)
        self.assertEqual(len(sessions), 2)
        
        session_names = [s.name for s in sessions]
        self.assertIn("会话1", session_names)
        self.assertIn("会话2", session_names)
    
    def test_session_rounds_relationship(self):
        """测试会话和轮次的关系"""
        room = RoomService.create_room("测试房间")
        session = SessionService.create_session(room.id, "测试会话")
        
        round1 = RoundService.create_round(session.id, ["问题1"])
        round2 = RoundService.create_round(session.id, ["问题2", "问题3"])
        
        rounds = RoundService.get_rounds_by_session(session.id)
        self.assertEqual(len(rounds), 2)
        self.assertEqual(rounds[0].round_index, 0)
        self.assertEqual(rounds[1].round_index, 1)
    
    def test_cascade_deletion(self):
        """测试级联删除"""
        room = RoomService.create_room("测试房间")
        session = SessionService.create_session(room.id, "测试会话")
        round_obj = RoundService.create_round(session.id, ["问题1"])
        
        # 删除房间应该级联删除会话和轮次
        success = RoomService.delete_room(room.id)
        self.assertTrue(success)
        
        # 验证相关数据已删除
        self.assertIsNone(RoomService.get_room(room.id))
        self.assertIsNone(SessionService.get_session(session.id))
        self.assertIsNone(RoundService.get_round(round_obj.id))
    
    def test_data_serialization(self):
        """测试数据序列化"""
        room = RoomService.create_room("测试房间")
        session = SessionService.create_session(room.id, "测试会话")
        round_obj = RoundService.create_round(session.id, ["问题1", "问题2"])
        
        # 测试转换为字典
        room_dict = RoomService.to_dict(room)
        session_dict = SessionService.to_dict(session)
        round_dict = RoundService.to_dict(round_obj)
        
        # 验证必要字段存在
        self.assertIn('id', room_dict)
        self.assertIn('memory_id', room_dict)
        self.assertIn('name', room_dict)
        self.assertIn('created_at', room_dict)
        
        self.assertIn('id', session_dict)
        self.assertIn('name', session_dict)
        self.assertIn('room_id', session_dict)
        self.assertIn('status', session_dict)
        
        self.assertIn('id', round_dict)
        self.assertIn('session_id', round_dict)
        self.assertIn('round_index', round_dict)
        self.assertIn('questions_count', round_dict)


if __name__ == '__main__':
    print("Running database and service tests...")
    unittest.main()