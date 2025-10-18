"""
统一响应格式模块
提供标准化的API响应格式
"""

from typing import Any, Optional, Tuple
from flask import jsonify
from datetime import datetime


class ResponseCode:
    """响应状态码枚举"""
    SUCCESS = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500


class ApiResponse:
    """统一API响应格式"""

    @staticmethod
    def success(data: Any = None, message: str = "操作成功", code: int = ResponseCode.SUCCESS) -> Tuple[dict, int]:
        """
        成功响应

        Args:
            data: 响应数据
            message: 响应消息
            code: HTTP状态码

        Returns:
            Flask JSON响应
        """
        response = {
            'success': True,
            'code': code,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(response), code

    @staticmethod
    def error(message: str, code: int = ResponseCode.BAD_REQUEST, data: Any = None) -> Tuple[dict, int]:
        """
        错误响应

        Args:
            message: 错误消息
            code: HTTP状态码
            data: 附加数据

        Returns:
            Flask JSON响应
        """
        response = {
            'success': False,
            'code': code,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(response), code

    @staticmethod
    def not_found(resource: str = "资源") -> Tuple[dict, int]:
        """404响应"""
        return ApiResponse.error(
            message=f"{resource}不存在",
            code=ResponseCode.NOT_FOUND
        )

    @staticmethod
    def bad_request(message: str = "请求参数错误") -> Tuple[dict, int]:
        """400响应"""
        return ApiResponse.error(
            message=message,
            code=ResponseCode.BAD_REQUEST
        )

    @staticmethod
    def internal_error(message: str = "服务器内部错误") -> Tuple[dict, int]:
        """500响应"""
        return ApiResponse.error(
            message=message,
            code=ResponseCode.INTERNAL_ERROR
        )

    @staticmethod
    def created(data: Any = None, message: str = "创建成功") -> Tuple[dict, int]:
        """201响应"""
        return ApiResponse.success(
            data=data,
            message=message,
            code=ResponseCode.CREATED
        )
