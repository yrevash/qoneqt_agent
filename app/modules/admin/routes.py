"""
Admin Panel API Routes
Full control over system configuration, monitoring, and management
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.modules.identity.models import User, Connection, AgentTrace
from app.modules.admin.models import (
    SystemConfig, AlertHistory, AuditLog, SystemHealth, NotificationLog,
    ConfigScope, ConfigType
)
from app.core.logging import get_audit_logger
from app.core.notifications import get_notification_service, NotificationChannel, NotificationPriority

admin_router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)
audit_logger = get_audit_logger()

# --- Schemas ---

class SystemConfigSchema(BaseModel):
    key: str
    value: Any
    value_type: ConfigType
    scope: ConfigScope = ConfigScope.SYSTEM
    description: Optional[str] = None
    requires_restart: bool = False
    is_editable: bool = True
    validation_rules: Optional[Dict[str, Any]] = None


class SystemConfigUpdate(BaseModel):
    value: Any
    description: Optional[str] = None


class AlertWebhook(BaseModel):
    """Webhook payload from Alertmanager"""
    version: str
    groupKey: str
    status: str
    receiver: str
    alerts: List[Dict[str, Any]]


class AlertAcknowledge(BaseModel):
    notes: Optional[str] = None


class SystemHealthResponse(BaseModel):
    service_name: str
    status: str
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    disk_usage: Optional[float]
    request_count: Optional[int]
    error_count: Optional[int]
    avg_response_time: Optional[float]
    timestamp: datetime


class AdminStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_connections: int
    pending_connections: int
    total_alerts_24h: int
    critical_alerts_active: int
    system_health: str
    services_status: Dict[str, str]


# --- Configuration Management ---

@admin_router.get("/config", response_model=List[SystemConfigSchema])
async def list_configs(
    scope: Optional[ConfigScope] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all system configurations"""
    query = select(SystemConfig)
    
    if scope:
        query = query.where(SystemConfig.scope == scope)
    
    query = query.order_by(SystemConfig.key)
    result = await db.execute(query)
    configs = result.scalars().all()
    
    audit_logger.log_action(
        action="list_configs",
        user_id=str(current_user.id),
        resource_type="system_config",
        details={"scope": scope.value if scope else "all"}
    )
    
    return configs


@admin_router.get("/config/{key}", response_model=SystemConfigSchema)
async def get_config(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get specific configuration"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalars().first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return config


@admin_router.post("/config", response_model=SystemConfigSchema)
async def create_config(
    config: SystemConfigSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create new system configuration"""
    # Check if exists
    existing = await db.execute(
        select(SystemConfig).where(SystemConfig.key == config.key)
    )
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Configuration already exists")
    
    new_config = SystemConfig(
        key=config.key,
        value={"data": config.value},
        value_type=config.value_type,
        scope=config.scope,
        description=config.description,
        requires_restart=config.requires_restart,
        is_editable=config.is_editable,
        validation_rules=config.validation_rules,
        last_modified_by=str(current_user.id)
    )
    
    db.add(new_config)
    await db.commit()
    await db.refresh(new_config)
    
    audit_logger.log_action(
        action="create_config",
        user_id=str(current_user.id),
        resource_type="system_config",
        resource_id=config.key,
        details={"config": config.dict()}
    )
    
    return new_config


@admin_router.put("/config/{key}", response_model=SystemConfigSchema)
async def update_config(
    key: str,
    update: SystemConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update system configuration - NO CODE CHANGES NEEDED!"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalars().first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    if not config.is_editable:
        raise HTTPException(status_code=403, detail="Configuration is not editable")
    
    # Store old value for audit
    old_value = config.value
    
    # Update config
    config.value = {"data": update.value}
    if update.description:
        config.description = update.description
    config.last_modified_by = str(current_user.id)
    config.last_modified_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(config)
    
    audit_logger.log_action(
        action="update_config",
        user_id=str(current_user.id),
        resource_type="system_config",
        resource_id=key,
        details={
            "old_value": old_value,
            "new_value": config.value,
            "requires_restart": config.requires_restart
        }
    )
    
    # Send notification if critical config changed
    if config.requires_restart or config.scope == ConfigScope.SYSTEM:
        notification_service = get_notification_service()
        await notification_service.send_notification(
            title=f"Configuration Updated: {key}",
            message=f"Admin {current_user.email} updated {key} to {update.value}. Restart required: {config.requires_restart}",
            channels=[NotificationChannel.SLACK, NotificationChannel.EMAIL],
            priority=NotificationPriority.HIGH,
            recipients={"email": ["admin@example.com"]}
        )
    
    return config


@admin_router.delete("/config/{key}")
async def delete_config(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete configuration"""
    result = await db.execute(
        select(SystemConfig).where(SystemConfig.key == key)
    )
    config = result.scalars().first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    await db.delete(config)
    await db.commit()
    
    audit_logger.log_action(
        action="delete_config",
        user_id=str(current_user.id),
        resource_type="system_config",
        resource_id=key
    )
    
    return {"status": "deleted"}


# --- Alert Management ---

@admin_router.post("/alerts/webhook")
async def alert_webhook(
    payload: AlertWebhook,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Webhook endpoint for Alertmanager
    Receives and stores all alerts
    """
    logger.info(f"Received alert webhook: {payload.status}")
    
    notification_service = get_notification_service()
    
    for alert in payload.alerts:
        # Extract alert details
        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        
        alert_name = labels.get("alertname", "Unknown")
        severity = labels.get("severity", "warning")
        
        # Create alert record
        alert_record = AlertHistory(
            alert_name=alert_name,
            severity=severity,
            status=alert.get("status", "firing"),
            summary=annotations.get("summary", ""),
            description=annotations.get("description", ""),
            labels=labels,
            annotations=annotations,
            starts_at=datetime.fromisoformat(alert.get("startsAt", "").replace("Z", "+00:00")),
            ends_at=datetime.fromisoformat(alert.get("endsAt", "").replace("Z", "+00:00")) if alert.get("endsAt") else None,
        )
        
        db.add(alert_record)
        
        # Send immediate notification for critical alerts
        if severity == "critical" and alert.get("status") == "firing":
            priority = NotificationPriority.CRITICAL
            channels = [NotificationChannel.EMAIL, NotificationChannel.SLACK]
            
            result = await notification_service.send_notification(
                title=f"🚨 CRITICAL ALERT: {alert_name}",
                message=annotations.get("description", "No description provided"),
                channels=channels,
                priority=priority,
                metadata={
                    "alert_name": alert_name,
                    "severity": severity,
                    "labels": labels
                },
                recipients={"email": ["admin@example.com"]}
            )
            
            alert_record.notification_sent = True
            alert_record.notification_channels = result
    
    await db.commit()
    
    return {"status": "ok", "alerts_processed": len(payload.alerts)}


@admin_router.get("/alerts", response_model=List[Dict[str, Any]])
async def list_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recent alerts"""
    query = select(AlertHistory).order_by(desc(AlertHistory.created_at)).limit(limit)
    
    if severity:
        query = query.where(AlertHistory.severity == severity)
    if status:
        query = query.where(AlertHistory.status == status)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [
        {
            "id": str(alert.id),
            "alert_name": alert.alert_name,
            "severity": alert.severity,
            "status": alert.status,
            "summary": alert.summary,
            "description": alert.description,
            "starts_at": alert.starts_at.isoformat(),
            "ends_at": alert.ends_at.isoformat() if alert.ends_at else None,
            "acknowledged": alert.acknowledged,
            "created_at": alert.created_at.isoformat(),
        }
        for alert in alerts
    ]


@admin_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    ack: AlertAcknowledge,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge an alert"""
    result = await db.execute(
        select(AlertHistory).where(AlertHistory.id == uuid.UUID(alert_id))
    )
    alert = result.scalars().first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.acknowledged = True
    alert.acknowledged_by = str(current_user.id)
    alert.acknowledged_at = datetime.utcnow()
    alert.resolution_notes = ack.notes
    
    await db.commit()
    
    audit_logger.log_action(
        action="acknowledge_alert",
        user_id=str(current_user.id),
        resource_type="alert",
        resource_id=alert_id,
        details={"notes": ack.notes}
    )
    
    return {"status": "acknowledged"}


# --- System Health & Monitoring ---

@admin_router.get("/health", response_model=List[SystemHealthResponse])
async def get_system_health(
    hours: int = 1,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get system health metrics"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Get latest health record for each service
    subquery = (
        select(
            SystemHealth.service_name,
            func.max(SystemHealth.timestamp).label('max_timestamp')
        )
        .where(SystemHealth.timestamp >= cutoff)
        .group_by(SystemHealth.service_name)
        .subquery()
    )
    
    query = (
        select(SystemHealth)
        .join(
            subquery,
            and_(
                SystemHealth.service_name == subquery.c.service_name,
                SystemHealth.timestamp == subquery.c.max_timestamp
            )
        )
    )
    
    result = await db.execute(query)
    health_records = result.scalars().all()
    
    return health_records


@admin_router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get admin dashboard statistics"""
    
    # User stats
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0
    
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar() or 0
    
    # Connection stats
    total_connections_result = await db.execute(select(func.count(Connection.id)))
    total_connections = total_connections_result.scalar() or 0
    
    pending_connections_result = await db.execute(
        select(func.count(Connection.id)).where(Connection.status == "PENDING")
    )
    pending_connections = pending_connections_result.scalar() or 0
    
    # Alert stats (last 24h)
    cutoff_24h = datetime.utcnow() - timedelta(hours=24)
    alerts_24h_result = await db.execute(
        select(func.count(AlertHistory.id)).where(AlertHistory.created_at >= cutoff_24h)
    )
    total_alerts_24h = alerts_24h_result.scalar() or 0
    
    critical_alerts_result = await db.execute(
        select(func.count(AlertHistory.id)).where(
            and_(
                AlertHistory.severity == "critical",
                AlertHistory.status == "firing",
                AlertHistory.acknowledged == False
            )
        )
    )
    critical_alerts_active = critical_alerts_result.scalar() or 0
    
    # System health status
    system_health = "healthy" if critical_alerts_active == 0 else "degraded"
    
    return AdminStatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_connections=total_connections,
        pending_connections=pending_connections,
        total_alerts_24h=total_alerts_24h,
        critical_alerts_active=critical_alerts_active,
        system_health=system_health,
        services_status={
            "api": "healthy",
            "worker": "healthy",
            "database": "healthy",
            "redis": "healthy",
        }
    )


# --- Audit Logs ---

@admin_router.get("/audit-logs")
async def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get audit logs"""
    query = select(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit)
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [
        {
            "id": str(log.id),
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "success": log.success,
            "timestamp": log.timestamp.isoformat(),
            "details": log.details,
        }
        for log in logs
    ]


# --- User Management (Admin Override) ---

@admin_router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate/deactivate a user"""
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_status = user.is_active
    user.is_active = not user.is_active
    
    await db.commit()
    
    audit_logger.log_action(
        action="toggle_user_active",
        user_id=str(current_user.id),
        resource_type="user",
        resource_id=user_id,
        details={"old_status": old_status, "new_status": user.is_active}
    )
    
    return {"user_id": user_id, "is_active": user.is_active}


@admin_router.put("/users/{user_id}/update")
async def admin_update_user(
    user_id: str,
    update_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admin can update any user field"""
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store old state
    old_state = {
        "email": user.email,
        "full_name": user.full_name,
        "bio": user.bio,
        "location": user.location,
        "role": user.role,
    }
    
    # Update allowed fields
    for key, value in update_data.items():
        if hasattr(user, key) and key not in ['id', 'created_at']:
            setattr(user, key, value)
    
    await db.commit()
    
    audit_logger.log_action(
        action="admin_update_user",
        user_id=str(current_user.id),
        resource_type="user",
        resource_id=user_id,
        details={
            "updated_fields": list(update_data.keys()),
            "before_state": old_state,
            "after_state": update_data
        }
    )
    
    return {"status": "updated", "user_id": user_id}
