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
    intent: str = "manual_wakeup"
    payload: dict = {}

class TriggerResponse(BaseModel):
    status: str
    trace_id: str
    queue: str
    energy_remaining: int

class FeedItem(BaseModel):
    id: uuid.UUID
    decision: str
    reasoning: dict
    timestamp: str

# --- Endpoints ---

@api_router.post("/auth/login", response_model=Token)
async def login(form_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Dev Authentication: Login with ANY password as long as the Email exists.
    """
    # 1. Check if user exists
    result = await db.execute(select(User).where(User.email == form_data.email))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email",
        )

    # 2. Generate Token
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
    The Panic Button: Forces an agent to wake up.
    Cost: 10 Energy Units.
    """
    COST = 10
    
    # 1. Cost Governor (Redis)
    energy = await RedisClient.check_energy(str(current_user.id))
    
    # Logic: Allow if energy > 0 (For testing we can be lenient, or strict)
    # If energy is 0 (first run), we might want to seed it.
    if energy <= 0:
        # Auto-seed for dev if 0
        await RedisClient.get_instance().set(f"user:energy:{current_user.id}", 100)
        energy = 100
    
    if energy < COST:
        raise HTTPException(status_code=402, detail="Insufficient Energy. Please recharge.")

    # 2. Deduct Energy
    await RedisClient.deduct_energy(str(current_user.id), COST)
    
    # 3. Push to RabbitMQ
    trace_id = str(uuid.uuid4())
    queue_name = "queue.high_priority" # User triggers are always high priority
    
    message = {
        "trace_id": trace_id,
        "agent_id": str(current_user.id),
        "action": "MANUAL_TRIGGER",
        "intent": request.intent,
        "timestamp": time.time(),
        "source": "api_gateway"
    }
    
    await RabbitMQClient.publish(queue_name, message)
    
    return {
        "status": "queued",
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
    """
    Observability: Returns the latest thoughts/decisions of your Agent.
    """
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
            "reasoning": t.reasoning_log, # This is the JSON from the Brain
            "timestamp": t.created_at.isoformat()
        }
        for t in traces
    ]