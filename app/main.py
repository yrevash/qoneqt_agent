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