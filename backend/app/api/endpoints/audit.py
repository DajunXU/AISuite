from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timedelta

from ...core.database import get_db
from ...core.logger import get_logger
from ...models.audit import AuditLog, AuditAction

logger = get_logger("audit_api")
router = APIRouter()


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    method: Optional[str]
    path: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    response_status: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    total: int
    items: List[AuditLogResponse]


@router.get("/logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """获取审计日志列表"""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if username:
        query = query.filter(AuditLog.username.ilike(f"%{username}%"))
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    total = query.count()
    items = query.order_by(AuditLog.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    logger.info(f"查询审计日志: page={page}, page_size={page_size}, total={total}")
    
    return AuditLogListResponse(
        total=total,
        items=[AuditLogResponse.model_validate(item) for item in items]
    )


@router.get("/logs/actions", response_model=List[str])
async def get_audit_actions(
    db: Session = Depends(get_db)
):
    """获取所有审计操作类型"""
    actions = [
        attr for attr in dir(AuditAction) 
        if not attr.startswith('_')
    ]
    return actions


@router.get("/logs/stats")
async def get_audit_stats(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """获取审计统计数据"""
    
    start_date = datetime.now() - timedelta(days=days)
    
    total_requests = db.query(func.count(AuditLog.id))\
        .filter(AuditLog.created_at >= start_date).scalar()
    
    total_users = db.query(func.count(func.distinct(AuditLog.user_id)))\
        .filter(AuditLog.created_at >= start_date).scalar()
    
    action_stats = db.query(
        AuditLog.action,
        func.count(AuditLog.id)
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(AuditLog.action).all()
    
    daily_stats = db.query(
        func.date(AuditLog.created_at).label('date'),
        func.count(AuditLog.id)
    ).filter(
        AuditLog.created_at >= start_date
    ).group_by(func.date(AuditLog.created_at)).all()
    
    return {
        "total_requests": total_requests or 0,
        "total_users": total_users or 0,
        "action_stats": {action: count for action, count in action_stats},
        "daily_stats": [{"date": str(date), "count": count} for date, count in daily_stats]
    }
