"""
MinIO客户端工具模块
"""

import json
import os
from io import StringIO
from typing import Dict, Any, Optional
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

load_dotenv()


class MinIOClient:
    """MinIO对象存储客户端"""
    
    def __init__(self):
        """初始化MinIO客户端"""
        self.endpoint = "test-minio.yeying.pub"
        self.access_key = "zi3QOwIWYlu9JIpOeF0O"
        self.secret_key = "W4mAFU5tRU4FSvQKrY2up5XcJpAck2xkrqBt2giL"
        self.bucket_name = "yeying-interviewer"
        
        # 初始化MinIO客户端
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=True  # 使用HTTPS
        )
        
        # 确保bucket存在
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保bucket存在，不存在则创建"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            print(f"Error creating bucket: {e}")
            raise
    
    def upload_json(self, object_name: str, data: Dict[str, Any]) -> bool:
        """上传JSON数据到MinIO"""
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            json_bytes = json_data.encode('utf-8')
            
            # 使用BytesIO而不是StringIO
            from io import BytesIO
            data_stream = BytesIO(json_bytes)
            
            # 上传文件
            self.client.put_object(
                self.bucket_name,
                object_name,
                data=data_stream,
                length=len(json_bytes),
                content_type='application/json'
            )
            print(f"Successfully uploaded {object_name}")
            return True
            
        except S3Error as e:
            print(f"Error uploading {object_name}: {e}")
            return False
    
    def download_json(self, object_name: str) -> Optional[Dict[str, Any]]:
        """从MinIO下载JSON数据"""
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = json.loads(response.data.decode('utf-8'))
            return data
            
        except S3Error as e:
            print(f"Error downloading {object_name}: {e}")
            return None
        finally:
            if 'response' in locals():
                response.close()
                response.release_conn()
    
    def upload_file(self, object_name: str, file_path: str) -> bool:
        """上传本地文件到MinIO"""
        try:
            self.client.fput_object(self.bucket_name, object_name, file_path)
            print(f"Successfully uploaded {file_path} as {object_name}")
            return True
            
        except S3Error as e:
            print(f"Error uploading {file_path}: {e}")
            return False
    
    def download_file(self, object_name: str, file_path: str) -> bool:
        """从MinIO下载文件到本地"""
        try:
            self.client.fget_object(self.bucket_name, object_name, file_path)
            print(f"Successfully downloaded {object_name} to {file_path}")
            return True
            
        except S3Error as e:
            print(f"Error downloading {object_name}: {e}")
            return False
    
    def list_objects(self, prefix: str = "") -> list:
        """列出MinIO中的对象"""
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
            
        except S3Error as e:
            print(f"Error listing objects: {e}")
            return []
    
    def delete_object(self, object_name: str) -> bool:
        """删除MinIO中的对象"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            print(f"Successfully deleted {object_name}")
            return True
            
        except S3Error as e:
            print(f"Error deleting {object_name}: {e}")
            return False


# 全局MinIO客户端实例
minio_client = MinIOClient()


def upload_resume_data(resume_data: Dict[str, Any]) -> bool:
    """上传简历数据到MinIO"""
    return minio_client.upload_json("data/resume.json", resume_data)


def download_resume_data() -> Optional[Dict[str, Any]]:
    """从MinIO下载简历数据"""
    return minio_client.download_json("data/resume.json")


def upload_questions_data(questions_data: Dict[str, Any], round_index: int) -> bool:
    """上传问题数据到MinIO"""
    object_name = f"data/questions_round_{round_index}.json"
    return minio_client.upload_json(object_name, questions_data)


def download_questions_data(round_index: int) -> Optional[Dict[str, Any]]:
    """从MinIO下载问题数据"""
    object_name = f"data/questions_round_{round_index}.json"
    return minio_client.download_json(object_name)