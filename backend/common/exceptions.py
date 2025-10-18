"""
自定义异常类
提供业务层级的异常定义
"""


class BusinessBaseException(Exception):
    """业务基础异常类"""

    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(BusinessBaseException):
    """参数验证异常"""

    def __init__(self, message: str = "参数验证失败"):
        super().__init__(message, code=400)


class ResourceNotFoundError(BaseException):
    """资源不存在异常"""

    def __init__(self, resource: str = "资源"):
        super().__init__(f"{resource}不存在", code=404)


class BusinessError(BusinessBaseException):
    """业务逻辑异常"""

    def __init__(self, message: str):
        super().__init__(message, code=400)


class ExternalServiceError(BusinessBaseException):
    """外部服务调用异常"""

    def __init__(self, service: str, message: str = ""):
        msg = f"{service}调用失败" + (f": {message}" if message else "")
        super().__init__(msg, code=500)


class ConfigurationError(BusinessBaseException):
    """配置错误异常"""

    def __init__(self, message: str):
        super().__init__(f"配置错误: {message}", code=500)


class DatabaseError(BusinessBaseException):
    """数据库操作异常"""

    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(message, code=500)
