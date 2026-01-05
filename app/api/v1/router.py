import uuid
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user
from app.core.redis import RedisClient
from app.core.queue import RabbitMQClient
from app.modules.identity.models import User, AgentTrace
from app.modules.agent_brain.gatekeeper import gatekeeper_service 

# Init Router
api_router = APIRouter()

# --- Pydantic Schemas ---
class LoginRequest(BaseModel):
    email: str
    password: str 

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    full_name: str

class TriggerRequest(BaseModel):
    query: str  # <--- CHANGED: Now requires a specific goal
    intent: str = "networking_search"

class TriggerResponse(BaseModel):
    status: str
    trace_id: Optional[str] = None
    queue: Optional[str] = None
    energy_remaining: int
    message: Optional[str] = None

class FeedItem(BaseModel):
    id: uuid.UUID
    decision: str
    reasoning: dict
    timestamp: str

# --- Endpoints ---

@api_router.post("/auth/login", response_model=Token)
async def login(form_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.email))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": str(user.id),
        "full_name": user.full_name
    }

@api_router.post("/agent/trigger", response_model=TriggerResponse)
async def trigger_agent(
    request: TriggerRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Goal-Oriented Trigger.
    1. Gatekeeper checks query.
    2. If Valid -> Deduct Cost -> Queue.
    3. If Junk -> Reject (0 Cost).
    """
    COST = 10
    
    # 1. GATEKEEPER CHECK (The Filter)
    # This runs BEFORE we touch the user's credits.
    check = await gatekeeper_service.validate_request(request.query)
    
    if check["status"] == "BLOCKED":
        # We return 200 OK but with a rejection message, so the UI can show it nicely.
        # Or you can throw 400. Let's return a nice response.
        current_energy = await RedisClient.check_energy(str(current_user.id))
        return {
            "status": "REJECTED",
            "message": f"Gatekeeper: {check.get('reason')}",
            "energy_remaining": current_energy # No deduction
        }

    # 2. Cost Governor
    energy = await RedisClient.check_energy(str(current_user.id))
    if energy <= 0:
        await RedisClient.get_instance().set(f"user:energy:{current_user.id}", 100)
        energy = 100
    
    if energy < COST:
        raise HTTPException(status_code=402, detail="Insufficient Energy.")

    # 3. Deduct Energy
    await RedisClient.deduct_energy(str(current_user.id), COST)
    
    # 4. Push to RabbitMQ
    trace_id = str(uuid.uuid4())
    queue_name = "queue.high_priority"
    
    message = {
        "trace_id": trace_id,
        "agent_id": str(current_user.id),
        "action": "NETWORKING_SEARCH",
        "query": request.query, 
        "timestamp": time.time(),
        "source": "api_gateway"
    }
    
    await RabbitMQClient.publish(queue_name, message)
    
    return {
        "status": "QUEUED",
        "trace_id": trace_id,
        "queue": queue_name,
        "energy_remaining": energy - COST
    }

@api_router.get("/agent/feed", response_model=List[FeedItem])
async def get_agent_feed(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = (
        select(AgentTrace)
        .where(AgentTrace.agent_id == current_user.id)
        .order_by(desc(AgentTrace.created_at))
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    traces = result.scalars().all()
    
    return [
        {
            "id": t.id,
            "decision": t.decision,
            "reasoning": t.reasoning_log,
            "timestamp": t.created_at.isoformat()
        }
        for t in traces
    ]