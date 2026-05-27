from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class ErrorCode:
    """统一错误码定义"""
    
    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = (1000, "未知错误")
    INVALID_PARAMETER = (1001, "参数错误")
    RESOURCE_NOT_FOUND = (1002, "资源不存在")
    UNAUTHORIZED = (1003, "未授权")
    FORBIDDEN = (1004, "禁止访问")
    METHOD_NOT_ALLOWED = (1005, "方法不允许")
    DUPLICATE_RESOURCE = (1006, "资源已存在")
    
    # 认证错误 (2000-2999)
    INVALID_TOKEN = (2000, "无效的令牌")
    TOKEN_EXPIRED = (2001, "令牌已过期")
    INVALID_CREDENTIALS = (2002, "用户名或密码错误")
    ACCOUNT_DISABLED = (2003, "账户已被禁用")
    ACCOUNT_LOCKED = (2004, "账户已被锁定")
    
    # 知识库错误 (3000-3999)
    KB_NOT_FOUND = (3000, "知识库不存在")
    KB_CREATE_FAILED = (3001, "创建知识库失败")
    KB_UPDATE_FAILED = (3002, "更新知识库失败")
    KB_DELETE_FAILED = (3003, "删除知识库失败")
    KB_ACCESS_DENIED = (3004, "无权访问该知识库")
    FILE_UPLOAD_FAILED = (3005, "文件上传失败")
    FILE_PROCESS_FAILED = (3006, "文件处理失败")
    FILE_NOT_FOUND = (3007, "文件不存在")
    DB_CONNECTION_FAILED = (3008, "数据库连接失败")
    
    # 对话错误 (4000-4999)
    CONVERSATION_NOT_FOUND = (4000, "对话不存在")
    CONVERSATION_CREATE_FAILED = (4001, "创建对话失败")
    MESSAGE_SEND_FAILED = (4002, "发送消息失败")
    
    # LLM 错误 (5000-5999)
    LLM_NOT_FOUND = (5000, "大模型不存在")
    LLM_API_ERROR = (5001, "大模型API调用失败")
    LLM_RESPONSE_EMPTY = (5002, "大模型返回为空")
    EMBEDDING_FAILED = (5003, "向量化失败")
    
    # 权限错误 (6000-6999)
    PERMISSION_DENIED = (6000, "权限不足")
    ROLE_NOT_FOUND = (6001, "角色不存在")
    MENU_NOT_FOUND = (6002, "菜单不存在")


class APIException(HTTPException):
    """自定义 API 异常"""
    
    def __init__(
        self,
        status_code: int,
        error_code: int,
        message: str,
        detail: Optional[Any] = None
    ):
        self.error_code = error_code
        self.message = message
        self.detail = detail
        
        super().__init__(
            status_code=status_code,
            detail={
                "error_code": error_code,
                "message": message,
                "detail": detail
            }
        )


def create_error_response(
    error_code: int,
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    detail: Optional[Any] = None
) -> Dict[str, Any]:
    """创建标准错误响应"""
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "detail": detail
        }
    }


# 便捷方法
def raise_not_found(resource: str):
    """抛出资源不存在异常"""
    raise APIException(
        status_code=status.HTTP_404_NOT_FOUND,
        error_code=ErrorCode.RESOURCE_NOT_FOUND[0],
        message=f"{resource}不存在"
    )


def raise_forbidden(message: str = "无权访问"):
    """抛出禁止访问异常"""
    raise APIException(
        status_code=status.HTTP_403_FORBIDDEN,
        error_code=ErrorCode.FORBIDDEN[0],
        message=message
    )


def raise_unauthorized(message: str = "请先登录"):
    """抛出未授权异常"""
    raise APIException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code=ErrorCode.UNAUTHORIZED[0],
        message=message
    )


def raise_bad_request(message: str):
    """抛出请求错误异常"""
    raise APIException(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code=ErrorCode.INVALID_PARAMETER[0],
        message=message
    )
