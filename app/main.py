from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator # <--- NEW

from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# --- LAYER 5: OBSERVABILITY ---
# This automatically tracks latency, request count, and errors
Instrumentator().instrument(app).expose(app)

@app.get("/")
async def root():
    return {"message": "Qoneqt Agent Network API is Live 🟢"}

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
            </style>
        </head>
        <body>
            <h1>Qoneqt Agent Network 🟢</h1>
            <p>System Status: <strong>OPERATIONAL</strong></p>
            
            <div class="card">
                <h3>🔗 API Endpoints</h3>
                <ul>
                    <li><a href="/docs" style="color:#fff">Swagger Documentation</a> (Interactive API)</li>
                    <li><a href="/metrics" style="color:#fff">Prometheus Metrics</a> (System Pulse)</li>
                </ul>
            </div>

            <div class="card">
                <h3>⚡ Quick Actions</h3>
                <p>Use the Swagger UI to <code>POST /agent/trigger</code></p>
            </div>
        </body>
    </html>
    """
    return html_content