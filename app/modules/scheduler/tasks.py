import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta

sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from app.modules.identity.models import User
from app.modules.recsys.service import recsys_service
from app.modules.watcher.audit_job import get_auditor
from pydantic import BaseModel, Optional, Any, Field 

logger = logging.getLogger(__name__)


class TimerScheduling(BaseModel):
    initiator_name: str = Field(..., description="Name of the user to get recommendations for")


async def scheduling_user_recommendations(initiator_name: str):
    """Schedule user recommendations"""
    print(f"\nScheduling recommendations for: '{initiator_name}'")
    return


async def run_system_audit():
    """
    Run comprehensive system audit
    Should be scheduled to run every 5-15 minutes
    """
    logger.info("⏰ Running scheduled system audit...")
    
    try:
        auditor = get_auditor()
        results = await auditor.run_full_audit()
        
        logger.info(f"Audit completed: {results['overall_health']} - {len(results.get('issues', []))} issues")
        
        return results
        
    except Exception as e:
        logger.error(f"Scheduled audit failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


async def cleanup_old_logs():
    """
    Clean up old audit logs, health records, etc.
    Should run daily
    """
    logger.info("🧹 Running cleanup of old logs...")
    
    try:
        from app.modules.admin.models import AuditLog, SystemHealth, NotificationLog, AlertHistory
        from sqlalchemy import delete
        
        async with AsyncSessionLocal() as db:
            cutoff_90_days = datetime.utcnow() - timedelta(days=90)
            cutoff_30_days = datetime.utcnow() - timedelta(days=30)
            cutoff_7_days = datetime.utcnow() - timedelta(days=7)
            
            # Delete old audit logs (>90 days)
            result = await db.execute(
                delete(AuditLog).where(AuditLog.timestamp < cutoff_90_days)
            )
            audit_deleted = result.rowcount
            
            # Delete old system health records (>30 days)
            result = await db.execute(
                delete(SystemHealth).where(SystemHealth.timestamp < cutoff_30_days)
            )
            health_deleted = result.rowcount
            
            # Delete old notification logs (>30 days)
            result = await db.execute(
                delete(NotificationLog).where(NotificationLog.created_at < cutoff_30_days)
            )
            notif_deleted = result.rowcount
            
            # Delete old resolved alerts (>7 days)
            result = await db.execute(
                delete(AlertHistory).where(
                    AlertHistory.created_at < cutoff_7_days,
                    AlertHistory.status == "resolved"
                )
            )
            alert_deleted = result.rowcount
            
            await db.commit()
            
            logger.info(f"Cleanup complete: {audit_deleted} audit logs, {health_deleted} health records, {notif_deleted} notifications, {alert_deleted} alerts")
            
            return {
                "audit_logs_deleted": audit_deleted,
                "health_records_deleted": health_deleted,
                "notifications_deleted": notif_deleted,
                "alerts_deleted": alert_deleted
            }
            
    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)} 
    