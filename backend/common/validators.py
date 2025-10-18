"""
数据验证装饰器
提供基本的JSON验证功能和输入验证
"""

import uuid
from functools import wraps
from typing import Callable, Any
from flask import request
from pydantic import BaseModel, ValidationError
from backend.common.response import ApiResponse
from backend.common.logger import get_logger

logger = get_logger(__name__)


def validate_json(schema: BaseModel):
    """
    验证JSON请求体

    Usage:
        @api_bp.route('/xxx', methods=['POST'])
        @validate_json(CreateXXXSchema)
        def create_xxx(validated_data):
            # validated_data 已验证
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = request.get_json()
                if data is None:
                    return ApiResponse.bad_request('请求体不能为空')

                # 验证数据
                validated = schema(**data)
                return func(*args, validated_data=validated.model_dump(), **kwargs)

            except ValidationError as e:
                # 提取错误信息
                errors = [f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}"
                         for err in e.errors()]
                return ApiResponse.bad_request('; '.join(errors))

            except Exception as e:
                logger.error(f"Validation error: {e}", exc_info=True)
                return ApiResponse.internal_error()

        return wrapper
    return decorator


def is_valid_uuid(value: str) -> bool:
    """
    验证字符串是否为有效的UUID

    Args:
        value: 待验证的字符串

    Returns:
        是否为有效的UUID
    """
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def validate_uuid_param(*param_names: str) -> Callable:
    """
    验证URL参数是否为有效的UUID格式

    Args:
        *param_names: 需要验证的参数名列表

    Usage:
        @api_bp.route('/room/<room_id>')
        @validate_uuid_param('room_id')
        def get_room(room_id):
            # room_id 已验证为有效UUID
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for param_name in param_names:
                param_value = kwargs.get(param_name)
                if param_value and not is_valid_uuid(param_value):
                    logger.warning(f"Invalid UUID format for parameter '{param_name}': {param_value}")
                    return ApiResponse.bad_request(f"无效的{param_name}格式")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_required_params(*param_names: str) -> Callable:
    """
    验证必需的请求参数是否存在

    Args:
        *param_names: 必需的参数名列表

    Usage:
        @api_bp.route('/api/search')
        @validate_required_params('keyword', 'page')
        def search(keyword, page):
            # keyword 和 page 参数已验证存在
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 检查查询参数
            missing = []
            for param_name in param_names:
                if param_name not in request.args:
                    missing.append(param_name)

            if missing:
                logger.warning(f"Missing required parameters: {missing}")
                return ApiResponse.bad_request(f"缺少必需参数: {', '.join(missing)}")

            return func(*args, **kwargs)
        return wrapper
    return decorator
