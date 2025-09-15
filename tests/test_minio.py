#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MinIO功能测试
"""

import unittest
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.utils.minio_client import minio_client, download_resume_data, upload_questions_data


class TestMinIOIntegration(unittest.TestCase):
    """MinIO集成测试"""
    
    def test_minio_connection(self):
        """测试MinIO连接"""
        # 测试bucket是否存在
        exists = minio_client.client.bucket_exists(minio_client.bucket_name)
        self.assertTrue(exists, "MinIO bucket should exist")
    
    def test_list_objects(self):
        """测试列出对象"""
        objects = minio_client.list_objects(prefix="data/")
        self.assertIsInstance(objects, list, "Should return a list of objects")
        self.assertGreater(len(objects), 0, "Should have at least one object")
    
    def test_download_resume_data(self):
        """测试下载简历数据"""
        resume_data = download_resume_data()
        self.assertIsNotNone(resume_data, "Resume data should not be None")
        self.assertIn('name', resume_data, "Resume should have name field")
        self.assertIn('position', resume_data, "Resume should have position field")
        self.assertEqual(resume_data['name'], '李明', "Name should be 李明")
    
    def test_download_questions_data(self):
        """测试下载问题数据"""
        questions_data = minio_client.download_json("data/questions_round_0.json")
        self.assertIsNotNone(questions_data, "Questions data should not be None")
        self.assertIn('questions', questions_data, "Should have questions field")
        self.assertIn('total_count', questions_data, "Should have total_count field")
        self.assertIn('round_index', questions_data, "Should have round_index field")
        self.assertEqual(questions_data['round_index'], 0, "Round index should be 0")
    
    def test_upload_and_download_cycle(self):
        """测试上传下载循环"""
        test_data = {
            'test': True,
            'message': 'This is a test',
            'round_index': 999,
            'total_count': 1
        }
        
        # 上传测试数据
        success = upload_questions_data(test_data, 999)
        self.assertTrue(success, "Upload should succeed")
        
        # 下载并验证
        downloaded = minio_client.download_json("data/questions_round_999.json")
        self.assertIsNotNone(downloaded, "Downloaded data should not be None")
        self.assertEqual(downloaded['test'], True, "Test field should be True")
        self.assertEqual(downloaded['message'], 'This is a test', "Message should match")
        
        # 清理测试数据
        minio_client.delete_object("data/questions_round_999.json")


if __name__ == '__main__':
    print("Running MinIO integration tests...")
    unittest.main()