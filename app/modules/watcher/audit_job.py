"""
AI-Powered System Auditor
Runs comprehensive system checks on regular intervals
Uses AI to analyze patterns, detect anomalies, and provide recommendations
"""
import asyncio
import logging
import psutil
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import RedisClient
from app.modules.admin.models import SystemHealth, AlertHistory, AuditLog
from app.modules.identity.models import User, Connection, AgentTrace
from app.core.notifications import get_notification_service, NotificationChannel, NotificationPriority
from app.core.config import settings

logger = logging.getLogger(__name__)


class SystemAuditor:
    """AI-powered system auditor"""
    
    def __init__(self):
        self.ollama_host = settings.OLLAMA_HOST
        self.ollama_model = settings.OLLAMA_MODEL
        self.notification_service = get_notification_service()
    
    async def run_full_audit(self) -> Dict[str, Any]:
        """
        Run comprehensive system audit
        Returns audit results with AI recommendations
        """
        logger.info("🔍 Starting full system audit...")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "issues": [],
            "recommendations": [],
            "overall_health": "healthy"
        }
        
        try:
            # Run all checks
            results["checks"]["infrastructure"] = await self._check_infrastructure()
            results["checks"]["database"] = await self._check_database()
            results["checks"]["api_health"] = await self._check_api_health()
            results["checks"]["queue_health"] = await self._check_queue_health()
            results["checks"]["cache_health"] = await self._check_cache_health()
            results["checks"]["agent_activity"] = await self._check_agent_activity()
            results["checks"]["error_rates"] = await self._check_error_rates()
            results["checks"]["resource_usage"] = await self._check_resource_usage()
            results["checks"]["security"] = await self._check_security()
            
            # Aggregate issues
            for check_name, check_result in results["checks"].items():
                if check_result.get("issues"):
                    results["issues"].extend(check_result["issues"])
            
            # Determine overall health
            critical_count = sum(1 for issue in results["issues"] if issue.get("severity") == "critical")
            warning_count = sum(1 for issue in results["issues"] if issue.get("severity") == "warning")
            
            if critical_count > 0:
                results["overall_health"] = "critical"
            elif warning_count > 3:
                results["overall_health"] = "degraded"
            elif warning_count > 0:
                results["overall_health"] = "warning"
            else:
                results["overall_health"] = "healthy"
            
            # Get AI recommendations
            if results["issues"]:
                results["recommendations"] = await self._get_ai_recommendations(results)
            
            # Save health record
            await self._save_health_record(results)
            
            # Send notifications if issues found
            if critical_count > 0:
                await self._notify_critical_issues(results)
            
            logger.info(f"✅ Audit complete: {results['overall_health']} - {len(results['issues'])} issues found")
            
        except Exception as e:
            logger.error(f"❌ Audit failed: {e}", exc_info=True)
            results["overall_health"] = "error"
            results["error"] = str(e)
        
        return results
    
    async def _check_infrastructure(self) -> Dict[str, Any]:
        """Check infrastructure components (CPU, memory, disk)"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            issues = []
            
            if cpu_percent > 80:
                issues.append({
                    "severity": "warning",
                    "component": "CPU",
                    "message": f"High CPU usage: {cpu_percent}%",
                    "value": cpu_percent
                })
            
            if memory.percent > 85:
                issues.append({
                    "severity": "critical" if memory.percent > 95 else "warning",
                    "component": "Memory",
                    "message": f"High memory usage: {memory.percent}%",
                    "value": memory.percent
                })
            
            if disk.percent > 85:
                issues.append({
                    "severity": "critical" if disk.percent > 95 else "warning",
                    "component": "Disk",
                    "message": f"Low disk space: {disk.percent}% used",
                    "value": disk.percent
                })
            
            return {
                "status": "critical" if any(i["severity"] == "critical" for i in issues) else "healthy",
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "disk_usage": disk.percent,
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Infrastructure check failed: {e}")
            return {"status": "error", "error": str(e), "issues": []}
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database health and performance"""
        try:
            async with get_db_session() as db:
                # Test connection
                start_time = datetime.utcnow()
                result = await db.execute(select(func.count(User.id)))
                user_count = result.scalar()
                query_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                issues = []
                
                if query_time > 1000:  # > 1 second
                    issues.append({
                        "severity": "warning",
                        "component": "Database",
                        "message": f"Slow database queries: {query_time:.2f}ms",
                        "value": query_time
                    })
                
                return {
                    "status": "healthy",
                    "query_time_ms": query_time,
                    "total_users": user_count,
                    "issues": issues
                }
                
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return {
                "status": "critical",
                "error": str(e),
                "issues": [{
                    "severity": "critical",
                    "component": "Database",
                    "message": f"Database connection failed: {str(e)}"
                }]
            }
    
    async def _check_api_health(self) -> Dict[str, Any]:
        """Check API health and response times"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = datetime.utcnow()
                
                # Try to ping the API health endpoint
                try:
                    async with session.get(f"http://api:8000/api/v1/health", timeout=5) as resp:
                        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                        
                        issues = []
                        
                        if resp.status != 200:
                            issues.append({
                                "severity": "critical",
                                "component": "API",
                                "message": f"API health check returned {resp.status}"
                            })
                        
                        if response_time > 500:
                            issues.append({
                                "severity": "warning",
                                "component": "API",
                                "message": f"Slow API response: {response_time:.2f}ms",
                                "value": response_time
                            })
                        
                        return {
                            "status": "healthy" if resp.status == 200 else "degraded",
                            "response_time_ms": response_time,
                            "status_code": resp.status,
                            "issues": issues
                        }
                        
                except asyncio.TimeoutError:
                    return {
                        "status": "critical",
                        "issues": [{
                            "severity": "critical",
                            "component": "API",
                            "message": "API health check timeout"
                        }]
                    }
                    
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "issues": [{
                    "severity": "warning",
                    "component": "API",
                    "message": f"Could not check API health: {str(e)}"
                }]
            }
    
    async def _check_queue_health(self) -> Dict[str, Any]:
        """Check RabbitMQ queue health"""
        # TODO: Implement RabbitMQ health check
        return {
            "status": "healthy",
            "issues": []
        }
    
    async def _check_cache_health(self) -> Dict[str, Any]:
        """Check Redis cache health"""
        try:
            redis = await RedisClient.get_instance()
            
            # Test connection
            start_time = datetime.utcnow()
            await redis.set("health_check", "ok", ex=10)
            result = await redis.get("health_check")
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            issues = []
            
            if result != "ok":
                issues.append({
                    "severity": "critical",
                    "component": "Redis",
                    "message": "Redis read/write test failed"
                })
            
            if response_time > 100:
                issues.append({
                    "severity": "warning",
                    "component": "Redis",
                    "message": f"Slow Redis response: {response_time:.2f}ms",
                    "value": response_time
                })
            
            return {
                "status": "healthy" if not issues else "degraded",
                "response_time_ms": response_time,
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Redis check failed: {e}")
            return {
                "status": "critical",
                "error": str(e),
                "issues": [{
                    "severity": "critical",
                    "component": "Redis",
                    "message": f"Redis connection failed: {str(e)}"
                }]
            }
    
    async def _check_agent_activity(self) -> Dict[str, Any]:
        """Check agent activity patterns"""
        try:
            async with get_db_session() as db:
                # Check recent agent activity (last hour)
                cutoff = datetime.utcnow() - timedelta(hours=1)
                
                result = await db.execute(
                    select(func.count(AgentTrace.id)).where(AgentTrace.created_at >= cutoff)
                )
                recent_activity = result.scalar() or 0
                
                # Check failed connections
                result = await db.execute(
                    select(func.count(Connection.id)).where(
                        and_(
                            Connection.status == "REJECTED",
                            Connection.created_at >= cutoff
                        )
                    )
                )
                failed_connections = result.scalar() or 0
                
                issues = []
                
                if recent_activity == 0:
                    issues.append({
                        "severity": "warning",
                        "component": "Agent Activity",
                        "message": "No agent activity in the last hour"
                    })
                
                if failed_connections > 10:
                    issues.append({
                        "severity": "warning",
                        "component": "Agent Connections",
                        "message": f"High connection failure rate: {failed_connections} in last hour"
                    })
                
                return {
                    "status": "healthy",
                    "recent_activity": recent_activity,
                    "failed_connections": failed_connections,
                    "issues": issues
                }
                
        except Exception as e:
            logger.error(f"Agent activity check failed: {e}")
            return {"status": "error", "error": str(e), "issues": []}
    
    async def _check_error_rates(self) -> Dict[str, Any]:
        """Check error rates from audit logs"""
        try:
            async with get_db_session() as db:
                cutoff = datetime.utcnow() - timedelta(hours=1)
                
                # Total actions
                total_result = await db.execute(
                    select(func.count(AuditLog.id)).where(AuditLog.timestamp >= cutoff)
                )
                total_actions = total_result.scalar() or 0
                
                # Failed actions
                error_result = await db.execute(
                    select(func.count(AuditLog.id)).where(
                        and_(
                            AuditLog.timestamp >= cutoff,
                            AuditLog.success == False
                        )
                    )
                )
                error_count = error_result.scalar() or 0
                
                error_rate = (error_count / total_actions * 100) if total_actions > 0 else 0
                
                issues = []
                
                if error_rate > 5:
                    issues.append({
                        "severity": "critical" if error_rate > 10 else "warning",
                        "component": "Error Rate",
                        "message": f"High error rate: {error_rate:.1f}%",
                        "value": error_rate
                    })
                
                return {
                    "status": "healthy" if error_rate < 5 else "degraded",
                    "error_rate": error_rate,
                    "total_actions": total_actions,
                    "error_count": error_count,
                    "issues": issues
                }
                
        except Exception as e:
            logger.error(f"Error rate check failed: {e}")
            return {"status": "error", "error": str(e), "issues": []}
    
    async def _check_resource_usage(self) -> Dict[str, Any]:
        """Check system resource usage trends"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Check for process leaks
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            issues = []
            
            if process_memory > 1000:  # > 1GB
                issues.append({
                    "severity": "warning",
                    "component": "Memory Leak",
                    "message": f"Process using {process_memory:.0f}MB memory",
                    "value": process_memory
                })
            
            return {
                "status": "healthy",
                "process_memory_mb": process_memory,
                "issues": issues
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e), "issues": []}
    
    async def _check_security(self) -> Dict[str, Any]:
        """Check security-related issues"""
        try:
            async with get_db_session() as db:
                # Check for suspicious activity (many failed actions)
                cutoff = datetime.utcnow() - timedelta(hours=1)
                
                result = await db.execute(
                    select(
                        AuditLog.user_id,
                        func.count(AuditLog.id).label('fail_count')
                    )
                    .where(
                        and_(
                            AuditLog.timestamp >= cutoff,
                            AuditLog.success == False
                        )
                    )
                    .group_by(AuditLog.user_id)
                    .having(func.count(AuditLog.id) > 10)
                )
                
                suspicious_users = result.all()
                
                issues = []
                
                for user_id, fail_count in suspicious_users:
                    issues.append({
                        "severity": "warning",
                        "component": "Security",
                        "message": f"User {user_id} has {fail_count} failed actions",
                        "user_id": user_id
                    })
                
                return {
                    "status": "healthy" if not issues else "warning",
                    "suspicious_activity_count": len(suspicious_users),
                    "issues": issues
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e), "issues": []}
    
    async def _get_ai_recommendations(self, audit_results: Dict[str, Any]) -> List[str]:
        """Use AI to analyze audit results and provide recommendations"""
        try:
            # Prepare prompt for AI
            issues_summary = "\n".join([
                f"- {issue['component']}: {issue['message']}"
                for issue in audit_results["issues"]
            ])
            
            prompt = f"""You are a system reliability engineer analyzing a production system audit.

System Health: {audit_results["overall_health"]}

Issues Found:
{issues_summary}

Based on these issues, provide 3-5 specific, actionable recommendations to improve system health and prevent future problems. Format as a bullet-point list."""
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=30
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        recommendations_text = data.get("response", "")
                        
                        # Parse recommendations
                        recommendations = [
                            line.strip().lstrip('-•*').strip()
                            for line in recommendations_text.split('\n')
                            if line.strip() and (line.strip().startswith('-') or line.strip().startswith('•') or line.strip().startswith('*'))
                        ]
                        
                        return recommendations[:5]  # Max 5
            
            return ["Unable to generate AI recommendations"]
            
        except Exception as e:
            logger.error(f"Failed to get AI recommendations: {e}")
            return [f"AI analysis unavailable: {str(e)}"]
    
    async def _save_health_record(self, audit_results: Dict[str, Any]) -> None:
        """Save health record to database"""
        try:
            async with get_db_session() as db:
                health_record = SystemHealth(
                    service_name="system",
                    status=audit_results["overall_health"],
                    cpu_usage=audit_results["checks"].get("infrastructure", {}).get("cpu_usage"),
                    memory_usage=audit_results["checks"].get("infrastructure", {}).get("memory_usage"),
                    disk_usage=audit_results["checks"].get("infrastructure", {}).get("disk_usage"),
                    custom_metrics={
                        "checks": audit_results["checks"],
                        "issue_count": len(audit_results["issues"])
                    },
                    issues={"issues": audit_results["issues"]},
                    recommendations={"recommendations": audit_results.get("recommendations", [])}
                )
                
                db.add(health_record)
                await db.commit()
                
        except Exception as e:
            logger.error(f"Failed to save health record: {e}")
    
    async def _notify_critical_issues(self, audit_results: Dict[str, Any]) -> None:
        """Send notifications for critical issues"""
        try:
            critical_issues = [i for i in audit_results["issues"] if i.get("severity") == "critical"]
            
            if critical_issues:
                message = "Critical system issues detected:\n\n"
                message += "\n".join([f"• {issue['component']}: {issue['message']}" for issue in critical_issues])
                
                if audit_results.get("recommendations"):
                    message += "\n\nRecommendations:\n"
                    message += "\n".join([f"• {rec}" for rec in audit_results["recommendations"]])
                
                await self.notification_service.send_notification(
                    title="🚨 CRITICAL: System Audit Issues",
                    message=message,
                    channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                    priority=NotificationPriority.CRITICAL,
                    metadata={"audit_results": audit_results},
                    recipients={"email": ["admin@example.com"]}
                )
                
        except Exception as e:
            logger.error(f"Failed to send critical notifications: {e}")


# Singleton instance
_auditor: Optional[SystemAuditor] = None


def get_auditor() -> SystemAuditor:
    """Get auditor singleton"""
    global _auditor
    if _auditor is None:
        _auditor = SystemAuditor()
    return _auditor
