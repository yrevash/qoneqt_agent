"""
Admin Panel Models
- System Configuration (dynamic settings)
- Alert History
- Audit Logs
- System Health Metrics
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Boolean, DateTime, Text, Integer, Float, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import enum


class ConfigScope(str, enum.Enum):
    """Configuration scope levels"""
    SYSTEM = "system"
    SERVICE = "service"
    USER = "user"
    AGENT = "agent"


class ConfigType(str, enum.Enum):
    """Configuration value types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"


class SystemConfig(Base):
    """
    Dynamic system configuration - no code changes needed!
    Admin can update any system parameter from the panel
    """
    __tablename__ = "system_config"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Configuration key (e.g., "OLLAMA_HOST", "MAX_ENERGY", "CONNECTION_COOLDOWN")
    key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    # Configuration value (stored as JSON for flexibility)
    value: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    # Value type for validation
    value_type: Mapped[ConfigType] = mapped_column(SQLEnum(ConfigType), nullable=False)
    
    # Scope (system-wide, per-service, per-user, etc.)
    scope: Mapped[ConfigScope] = mapped_column(SQLEnum(ConfigScope), default=ConfigScope.SYSTEM)
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Default value
    default_value: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Whether this config requires service restart
    requires_restart: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Is this config editable via admin panel?
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Validation rules (min, max, regex, etc.)
    validation_rules: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Change tracking
    last_modified_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_modified_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_config_scope', 'scope'),
        Index('idx_config_key', 'key'),
    )


class AlertHistory(Base):
    """
    Store all alerts received from Alertmanager
    For historical analysis and debugging
    """
    __tablename__ = "alert_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Alert details
    alert_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # firing, resolved
    
    # Alert content
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Labels and annotations from Prometheus
    labels: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    annotations: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Notification status
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_channels: Mapped[Optional[Dict[str, bool]]] = mapped_column(JSONB, nullable=True)
    
    # Timing
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Response tracking
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_alert_severity', 'severity'),
        Index('idx_alert_status', 'status'),
        Index('idx_alert_created', 'created_at'),
    )


class AuditLog(Base):
    """
    Comprehensive audit log for all system actions
    Who did what, when, and what was the result
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who performed the action
    user_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    user_email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # What action was performed
    action: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    action_category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # admin, user, agent, system
    
    # What was affected
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    resource_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Action details
    details: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Before/After state for changes
    before_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Result
    success: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_audit_user', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_category', 'action_category'),
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_success', 'success'),
    )


class SystemHealth(Base):
    """
    System health metrics collected by AI Auditor
    Track performance, errors, and resource usage over time
    """
    __tablename__ = "system_health"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Service identifier
    service_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    
    # Health status
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # healthy, degraded, down
    
    # Metrics
    cpu_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    disk_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # API metrics
    request_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_response_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Queue metrics
    queue_depth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Database metrics
    db_connections: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    db_query_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Additional metrics
    custom_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Issues detected
    issues: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    # Recommendations from AI
    recommendations: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_health_service', 'service_name'),
        Index('idx_health_status', 'status'),
        Index('idx_health_timestamp', 'timestamp'),
    )


class NotificationLog(Base):
    """
    Log all notifications sent
    Track delivery success/failure
    """
    __tablename__ = "notification_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Notification details
    notification_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    
    # Content
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Recipients
    recipients: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # sent, failed, pending
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Related alert
    alert_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # Additional metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    notification_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_notification_type', 'notification_type'),
        Index('idx_notification_channel', 'channel'),
        Index('idx_notification_status', 'status'),
    )
