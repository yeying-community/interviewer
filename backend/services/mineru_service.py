"""
MinerU PDF解析服务
"""

import os
import time
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class MinerUService:
    """MinerU PDF OCR解析服务"""

    def __init__(self):
        self.api_key = os.getenv("MINERU_API_KEY")
        self.base_url = "https://mineru.net/api/v4"

        if not self.api_key:
            raise ValueError("MINERU_API_KEY not found in environment variables")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def parse_pdf(self, pdf_file_path: str) -> Optional[str]:
        """
        解析PDF文件，返回Markdown格式内容

        Args:
            pdf_file_path: PDF文件路径

        Returns:
            Markdown格式的解析内容，失败返回None
        """
        try:
            # 1. 先上传PDF文件到MinIO并获取URL
            pdf_url = self._upload_pdf_to_minio(pdf_file_path)
            if not pdf_url:
                print("Failed to upload PDF to storage")
                return None

            print(f"PDF uploaded to storage: {pdf_url}")

            # 2. 提交解析任务
            task_id = self._submit_parse_task(pdf_url)
            if not task_id:
                print("Failed to submit parse task")
                return None

            print(f"Parse task submitted, task_id: {task_id}")

            # 3. 轮询解析状态并获取结果
            markdown_content = self._poll_parse_result(task_id)

            return markdown_content

        except Exception as e:
            print(f"Error parsing PDF with MinerU: {e}")
            return None

    def _upload_pdf_to_minio(self, pdf_file_path: str) -> Optional[str]:
        """上传PDF文件到MinIO并返回预签名URL"""
        try:
            from backend.utils.minio_client import minio_client

            # 检查文件是否存在
            if not os.path.exists(pdf_file_path):
                print(f"PDF file not found: {pdf_file_path}")
                return None

            # 检查文件大小（200MB限制）
            file_size = os.path.getsize(pdf_file_path)
            if file_size > 200 * 1024 * 1024:
                print(f"PDF file too large: {file_size / (1024*1024):.2f}MB (max 200MB)")
                return None

            # 上传到MinIO
            import uuid
            filename = f"temp/resume_{uuid.uuid4().hex}.pdf"
            success = minio_client.upload_file(filename, pdf_file_path)

            if not success:
                return None

            # 生成预签名URL（24小时有效）
            presigned_url = minio_client.get_presigned_url(filename, expires_hours=24)

            if not presigned_url:
                print("Failed to generate presigned URL")
                return None

            print(f"Generated presigned URL (valid for 24 hours)")
            return presigned_url

        except Exception as e:
            print(f"Error uploading PDF to MinIO: {e}")
            return None

    def _submit_parse_task(self, pdf_url: str) -> Optional[str]:
        """提交PDF解析任务"""
        try:
            url = f"{self.base_url}/extract/task"

            data = {
                "url": pdf_url,
                "is_ocr": True,
                "enable_formula": False,
            }

            response = requests.post(url, headers=self.headers, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                print(f"API Response: {result}")

                # 获取task_id
                task_id = result.get('data', {}).get('task_id') or result.get('data')
                return task_id
            else:
                print(f"Submit task failed: {response.status_code}, {response.text}")
                return None

        except Exception as e:
            print(f"Error submitting parse task: {e}")
            return None

    def _poll_parse_result(self, task_id: str, max_attempts: int = 60, interval: int = 5) -> Optional[str]:
        """
        轮询解析结果

        Args:
            task_id: 任务ID
            max_attempts: 最大尝试次数（默认60次，共5分钟）
            interval: 轮询间隔（秒）

        Returns:
            Markdown内容，失败返回None
        """
        try:
            status_url = f"{self.base_url}/extract/task/{task_id}"

            for attempt in range(max_attempts):
                response = requests.get(status_url, headers=self.headers, timeout=30)

                if response.status_code != 200:
                    print(f"Status check failed: {response.status_code}")
                    time.sleep(interval)
                    continue

                result = response.json()
                data = result.get('data', {})
                state = data.get('state', '')

                # 显示进度
                if state == 'running':
                    progress = data.get('extract_progress', {})
                    extracted = progress.get('extracted_pages', 0)
                    total = progress.get('total_pages', 0)
                    print(f"Parse status: {state} ({extracted}/{total} pages) (attempt {attempt + 1}/{max_attempts})")
                else:
                    print(f"Parse status: {state} (attempt {attempt + 1}/{max_attempts})")

                if state == 'done':
                    # 解析完成，下载ZIP并提取markdown
                    zip_url = data.get('full_zip_url')
                    if not zip_url:
                        print("No ZIP URL in response")
                        return None

                    print(f"Downloading result from: {zip_url}")
                    markdown_content = self._download_and_extract_zip(zip_url)
                    return markdown_content

                elif state == 'failed':
                    err_msg = data.get('err_msg', 'Unknown error')
                    print(f"Parse failed: {err_msg}")
                    return None
                elif state in ['pending', 'running', 'converting']:
                    # 继续等待
                    time.sleep(interval)
                else:
                    print(f"Unknown state: {state}")
                    time.sleep(interval)

            print(f"Parse timeout after {max_attempts * interval} seconds")
            return None

        except Exception as e:
            print(f"Error polling parse result: {e}")
            return None

    def _download_and_extract_zip(self, zip_url: str) -> Optional[str]:
        """下载ZIP文件并提取markdown内容"""
        try:
            import zipfile
            import io

            # 下载ZIP文件
            print("Downloading ZIP file...")
            response = requests.get(zip_url, timeout=60)

            if response.status_code != 200:
                print(f"Failed to download ZIP: {response.status_code}")
                return None

            print(f"ZIP file downloaded ({len(response.content)} bytes)")

            # 解压ZIP文件
            zip_file = zipfile.ZipFile(io.BytesIO(response.content))

            # 查找markdown文件
            markdown_files = [f for f in zip_file.namelist() if f.endswith('.md')]

            if not markdown_files:
                print("No markdown file found in ZIP")
                return None

            # 读取第一个markdown文件
            md_filename = markdown_files[0]
            print(f"Extracting markdown from: {md_filename}")

            markdown_content = zip_file.read(md_filename).decode('utf-8')
            print(f"Markdown extracted ({len(markdown_content)} characters)")

            return markdown_content

        except Exception as e:
            print(f"Error downloading/extracting ZIP: {e}")
            return None


# 全局服务实例
_mineru_service = None

def get_mineru_service() -> MinerUService:
    """获取MinerU服务实例（单例模式）"""
    global _mineru_service
    if _mineru_service is None:
        _mineru_service = MinerUService()
    return _mineru_service
