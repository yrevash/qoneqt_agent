import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge
from sqlalchemy import text
import time
import asyncio

from app.core.config import settings
from app.core.logging import setup_logging, get_request_logger
from app.api.v1.router import api_router
from app.modules.admin.routes import admin_router


# Setup logging on startup
setup_logging(
    log_level=settings.LOG_LEVEL,
    log_dir=settings.LOG_DIR,
    enable_json=settings.ENABLE_JSON_LOGGING,
)

logger = logging.getLogger(__name__)
request_logger = get_request_logger()

# Prometheus Gauges for service health
redis_up = Gauge('redis_up', 'Redis service is up (1) or down (0)')
pg_up = Gauge('pg_up', 'PostgreSQL service is up (1) or down (0)')
rabbitmq_up = Gauge('rabbitmq_up', 'RabbitMQ service is up (1) or down (0)')

async def check_service_health():
    """Background task to check service health and update metrics"""
    from app.core.redis import RedisClient
    from app.core.database import engine
    from app.core.queue import RabbitMQClient
    
    while True:
        try:
            # Check Redis
            try:
                redis_conn = RedisClient.get_instance()
                await redis_conn.ping()
                redis_up.set(1)
                logger.debug("Redis: Healthy")
            except Exception as e:
                redis_up.set(0)
                logger.error(f"Redis: Down - {e}")
            
            # Check PostgreSQL
            try:
                async with engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                pg_up.set(1)
                logger.debug("PostgreSQL: Healthy")
            except Exception as e:
                pg_up.set(0)
                logger.error(f"PostgreSQL: Down - {e}")
            
            # Check RabbitMQ
            try:
                channel = await RabbitMQClient.get_channel()
                if channel and not channel.is_closed:
                    rabbitmq_up.set(1)
                    logger.debug("RabbitMQ: Healthy")
                else:
                    rabbitmq_up.set(0)
                    logger.warning("RabbitMQ: Channel closed")
            except Exception as e:
                rabbitmq_up.set(0)
                logger.error(f"RabbitMQ: Down - {e}")
            
        except Exception as e:
            logger.error(f"Error in health check: {e}")
        
        # Check every 10 seconds
        await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting Qoneqt Agent Network")
    logger.info(f"Environment: {settings.PROJECT_NAME}")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    logger.info(f"Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    
    # Start background health check task
    health_task = asyncio.create_task(check_service_health())
    logger.info("Health monitoring started")
    
    yield
    
    # Shutdown
    health_task.cancel()
    logger.info("Shutting down Qoneqt Agent Network")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    
    # Get request ID if exists
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Log request
    request_logger.log_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        request_id=request_id,
        metadata={
            "user_agent": request.headers.get("user-agent"),
            "ip": request.client.host if request.client else None
        }
    )
    
    return response


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev tunnels
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)

# --- OBSERVABILITY ---
# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint for monitoring"""
    from app.core.redis import RedisClient
    from app.core.database import engine
    from app.core.queue import RabbitMQClient
    
    health_status = {
        "status": "healthy",
        "service": "qoneqt-api",
        "timestamp": time.time(),
        "services": {}
    }
    
    # Check each service
    try:
        redis_conn = RedisClient.get_instance()
        await redis_conn.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["services"]["postgresql"] = "healthy"
    except Exception as e:
        health_status["services"]["postgresql"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    try:
        channel = await RabbitMQClient.get_channel()
        if channel and not channel.is_closed:
            health_status["services"]["rabbitmq"] = "healthy"
        else:
            health_status["services"]["rabbitmq"] = "unhealthy: channel closed"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["rabbitmq"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
    <html>
        <head>
            <title>Qoneqt God Mode</title>
            <style>
                body { font-family: sans-serif; background: #111; color: #eee; padding: 2rem; }
                .card { background: #222; padding: 1rem; margin-bottom: 1rem; border-radius: 8px; border-left: 5px solid #00d4ff; }
                h1 { color: #00d4ff; }
                code { background: #333; padding: 0.2rem; }
                a { color: #00d4ff; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>Qoneqt Agent Network 🟢</h1>
            <p>System Status: <stronPERATIONAL</strong></p>
            
            <div class="card">
                <h3>API Endpoints</h3>
                <ul>
                    <li><a href="/docs">Swagger Documentation</a> (Interactive API)</li>
                    <li><a href="/metrics">Prometheus Metrics</a> (System Pulse)</li>
                    <li><a href="/api/v1/health">Health Check</a> (System Health)</li>
                </ul>
            </div>

            <div class="card">
                <h3>Quick Actions</h3>
                <p>Use the Swagger UI to <code>POST /api/v1/agent/trigger</code></p>
                <p>Admin Panel: <code>GET /api/v1/admin/stats</code></p>
            </div>
            
            <div class="card">
                <h3>Admin Features</h3>
                <ul>
                    <li>Configuration Management: <code>/api/v1/admin/config</code></li>
                    <li>System Alerts: <code>/api/v1/admin/alerts</code></li>
                    <li>Audit Logs: <code>/api/v1/admin/audit-logs</code></li>
                    <li>System Health: <code>/api/v1/admin/health</code></li>
                </ul>
            </div>
        </body>
    </html>
    """
    return html_content