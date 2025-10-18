"""
中间件模块
提供统一的异常处理、日志记录、请求验证等中间件
"""

from functools import wraps
from typing import Callable, Any, Tuple
from flask import request, Flask, Response
from backend.common.response import ApiResponse
from backend.common.exceptions import BusinessBaseException
from backend.common.logger import get_logger

logger = get_logger(__name__)


def error_handler(app: Flask) -> None:
    """
    全局异常处理器

    Args:
        app: Flask应用实例
    """

    @app.errorhandler(BusinessBaseException)
    def handle_custom_exception(error):
        """处理自定义异常"""
        logger.warning(f"Business exception: {error.message}", exc_info=True)
        return ApiResponse.error(
            message=error.message,
            code=error.code
        )

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        """处理值错误"""
        logger.warning(f"ValueError: {str(error)}", exc_info=True)
        return ApiResponse.bad_request(str(error))

    @app.errorhandler(404)
    def handle_not_found(error):
        """处理404错误"""
        logger.warning(f"404 Not Found: {request.url}")
        return ApiResponse.not_found("页面或资源")

    @app.errorhandler(500)
    def handle_internal_error(error):
        """处理500错误"""
        logger.error(f"Internal Server Error: {str(error)}", exc_info=True)
        return ApiResponse.internal_error()

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """处理未预期的异常"""
        logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        return ApiResponse.internal_error("服务器发生未知错误")


def request_logger(app: Flask) -> None:
    """
    请求日志中间件

    Args:
        app: Flask应用实例
    """

    @app.before_request
    def log_request():
        """记录请求信息"""
        logger.info(
            f"Request: {request.method} {request.path} "
            f"from {request.remote_addr} "
            f"User-Agent: {request.user_agent}"
        )

    @app.after_request
    def log_response(response: Response) -> Response:
        """记录响应信息"""
        logger.info(
            f"Response: {request.method} {request.path} "
            f"Status: {response.status_code}"
        )
        return response


def validate_request(*required_fields: str) -> Callable:
    """
    请求参数验证装饰器

    Args:
        *required_fields: 必需的字段列表

    Usage:
        @validate_request('name', 'email')
        def create_user():
            data = request.get_json()
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # 获取请求数据
            if request.is_json:
                data = request.get_json() or {}
            else:
                data = request.form.to_dict()

            # 检查必需字段
            missing_fields = []
            for field in required_fields:
                if field not in data or not data[field]:
                    missing_fields.append(field)

            if missing_fields:
                logger.warning(f"Missing required fields: {missing_fields}")
                return ApiResponse.bad_request(
                    f"缺少必需参数: {', '.join(missing_fields)}"
                )

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def handle_exceptions(f: Callable) -> Callable:
    """
    异常处理装饰器 - 用于路由函数

    Usage:
        @app.route('/api/users')
        @handle_exceptions
        def get_users():
            ...
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        try:
            return f(*args, **kwargs)
        except BusinessBaseException as e:
            logger.warning(f"Business exception in {f.__name__}: {e.message}")
            return ApiResponse.error(message=e.message, code=e.code)
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}", exc_info=True)
            return ApiResponse.internal_error(f"操作失败: {str(e)}")
    return decorated_function
