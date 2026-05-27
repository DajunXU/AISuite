from typing import Dict, Optional
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
from threading import Lock


class RateLimiter:
    """简单的内存限流器"""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
    
    def check(
        self, 
        key: str, 
        limit: int, 
        window: int
    ) -> bool:
        """
        检查请求是否超过限制
        
        Args:
            key: 限流key (如用户ID、IP等)
            limit: 限制次数
            window: 时间窗口(秒)
        
        Returns:
            bool: 是否允许请求
        """
        now = time.time()
        window_start = now - window
        
        with self.lock:
            # 清理过期的请求记录
            self.requests[key] = [
                t for t in self.requests[key] 
                if t > window_start
            ]
            
            # 检查是否超过限制
            if len(self.requests[key]) >= limit:
                return False
            
            # 记录本次请求
            self.requests[key].append(now)
            return True
    
    def get_remaining(self, key: str, limit: int, window: int) -> int:
        """获取剩余请求次数"""
        now = time.time()
        window_start = now - window
        
        with self.lock:
            self.requests[key] = [
                t for t in self.requests[key] 
                if t > window_start
            ]
            return max(0, limit - len(self.requests[key]))
    
    def reset(self, key: str):
        """重置指定key的限流"""
        with self.lock:
            if key in self.requests:
                del self.requests[key]


# 全局限流器实例
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中间件"""
    
    def __init__(self, app, default_limit: int = 100, default_window: int = 60):
        super().__init__(app)
        self.default_limit = default_limit
        self.default_window = default_window
    
    async def dispatch(self, request: Request, call_next):
        # 跳过限流的路径
        if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 检查限流
        if not rate_limiter.check(
            client_ip, 
            self.default_limit, 
            self.default_window
        ):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": {
                        "code": 429,
                        "message": "请求过于频繁，请稍后再试",
                        "detail": f"限制: {self.default_limit}次/{self.default_window}秒"
                    }
                }
            )
        
        response = await call_next(request)
        
        # 添加限流响应头
        remaining = rate_limiter.get_remaining(
            client_ip, 
            self.default_limit, 
            self.default_window
        )
        response.headers["X-RateLimit-Limit"] = str(self.default_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response


def rate_limit(limit: int = 10, window: int = 60):
    """
    限流装饰器
    
    Args:
        limit: 限制次数
        window: 时间窗口(秒)
    
    Example:
        @rate_limit(limit=10, window=60)
        async def chat():
            ...
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # 获取用户ID或IP作为限流key
            user = getattr(request.state, "user", None)
            key = str(user.id) if user else request.client.host
            
            if not rate_limiter.check(key, limit, window):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "code": 429,
                        "message": "请求过于频繁，请稍后再试",
                        "detail": f"限制: {limit}次/{window}秒"
                    }
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
