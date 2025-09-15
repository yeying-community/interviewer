#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API接口测试
"""

import unittest
import json
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 设置测试数据库
os.environ['DATABASE_PATH'] = ':memory:'

from app import create_app, init_app


class TestAPIRoutes(unittest.TestCase):
    """API路由测试"""
    
    def setUp(self):
        """每个测试前的设置"""
        init_app()
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """每个测试后的清理"""
        self.app_context.pop()
    
    def test_index_page(self):
        """测试首页"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_create_room(self):
        """测试创建房间"""
        response = self.client.get('/create_room')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('room', data)
        self.assertIn('redirect_url', data)
    
    def test_api_rooms(self):
        """测试获取房间列表API"""
        response = self.client.get('/api/rooms')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        # 应该至少有一个默认房间
        self.assertGreater(len(data), 0)
    
    def test_api_minio_test(self):
        """测试MinIO连接API"""
        response = self.client.get('/api/minio/test')
        # MinIO可能连接失败，但API应该返回结果
        self.assertIn(response.status_code, [200, 500])


if __name__ == '__main__':
    print("Running API tests...")
    unittest.main()