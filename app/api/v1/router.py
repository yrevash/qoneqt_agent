import uuid
import time
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user
from app.core.redis import RedisClient
from app.core.queue import RabbitMQClient
from app.modules.identity.models import User, AgentTrace, Connection
from app.modules.agent_brain.gatekeeper import gatekeeper_service
from app.modules.recsys.embedding import embedding_service 

# Init Router
api_router = APIRouter()
logger = logging.getLogger(__name__)

# --- Pydantic Schemas ---
class SelectUserRequest(BaseModel):
    user_id: str  # Can select any user by ID
    
class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str
    bio: Optional[str] = None
    location: Optional[str] = None
    role: Optional[str] = None
    skills: Optional[List[str]] = None 

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

class UserProfile(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    role: Optional[str]
    skills: Optional[List[str]]
    created_at: str

class ConnectionItem(BaseModel):
    id: uuid.UUID
    initiator_id: uuid.UUID
    receiver_id: uuid.UUID
    status: str
    created_at: str
    # Related user info
    other_user_name: Optional[str] = None
    other_user_bio: Optional[str] = None

# --- Endpoints ---

@api_router.post("/auth/select-user", response_model=Token)
async def select_user(form_data: SelectUserRequest, db: AsyncSession = Depends(get_db)):
    """Select which user/agent to control (no password needed)"""
    result = await db.execute(select(User).where(User.id == uuid.UUID(form_data.user_id)))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )
    
    # Initialize energy if not exists
    energy = await RedisClient.check_energy(str(user.id))
    if energy == 0:
        await RedisClient.get_instance().set(f"user:energy:{user.id}", 100)

    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": str(user.id),
        "full_name": user.full_name
    }

@api_router.post("/users/create", response_model=Token, status_code=status.HTTP_201_CREATED)
async def create_user(form_data: CreateUserRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user/agent"""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == form_data.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    # Generate interest vector from bio + skills + role
    profile_text = f"{form_data.bio or ''} {form_data.role or ''} {' '.join(form_data.skills or [])}"
    interest_vector = embedding_service.get_embedding(profile_text)
    
    new_user = User(
        email=form_data.email,
        full_name=form_data.full_name,
        bio=form_data.bio,
        location=form_data.location,
        role=form_data.role,
        skills=form_data.skills,
        interest_vector=interest_vector,  # Populate vector immediately
        is_active=True
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Initialize energy in Redis
    await RedisClient.get_instance().set(f"user:energy:{new_user.id}", 100)
    
    # Generate token
    access_token = create_access_token(data={"sub": str(new_user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(new_user.id),
        "full_name": new_user.full_name
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
    
    logger.info(f"🚀 Publishing message to {queue_name} for user {current_user.full_name}: {request.query}")
    await RabbitMQClient.publish(queue_name, message)
    logger.info(f"✅ Message published successfully")
    
    return {
        "status": "QUEUED",
        "trace_id": trace_id,
        "queue": queue_name,
        "energy_remaining": energy - COST
    }

@api_router.get("/agent/feed", response_model=List[FeedItem])
async def get_agent_feed(
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get agent decision feed with pagination"""
    stmt = (
        select(AgentTrace)
        .where(AgentTrace.agent_id == current_user.id)
        .order_by(desc(AgentTrace.created_at))
        .limit(limit)
        .offset(offset)
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

@api_router.get("/users/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "bio": current_user.bio,
        "location": current_user.location,
        "role": current_user.role,
        "skills": current_user.skills,
        "created_at": current_user.created_at.isoformat()
    }

@api_router.get("/users", response_model=List[UserProfile])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all users - NO AUTH REQUIRED for testing/selection"""
    stmt = (
        select(User)
        .where(User.is_active == True)
        .limit(limit)
        .offset(offset)
    )
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "bio": u.bio,
            "location": u.location,
            "role": u.role,
            "skills": u.skills,
            "created_at": u.created_at.isoformat()
        }
        for u in users
    ]

@api_router.get("/connections", response_model=List[ConnectionItem])
async def get_connections(
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's connections (sent and received)"""
    from sqlalchemy.orm import selectinload
    
    # Get connections where user is initiator or receiver
    stmt = (
        select(Connection)
        .options(selectinload(Connection.initiator), selectinload(Connection.receiver))
        .where(
            (Connection.initiator_id == current_user.id) |
            (Connection.receiver_id == current_user.id)
        )
    )
    
    if status_filter:
        stmt = stmt.where(Connection.status == status_filter.upper())
    
    stmt = stmt.order_by(desc(Connection.created_at))
    
    result = await db.execute(stmt)
    connections = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "initiator_id": c.initiator_id,
            "receiver_id": c.receiver_id,
            "status": c.status,
            "created_at": c.created_at.isoformat(),
            "other_user_name": (
                c.receiver.full_name if c.initiator_id == current_user.id 
                else c.initiator.full_name
            ),
            "other_user_bio": (
                c.receiver.bio if c.initiator_id == current_user.id 
                else c.initiator.bio
            )
        }
        for c in connections
    ]

@api_router.get("/energy")
async def get_energy(current_user: User = Depends(get_current_user)):
    """Get current user's energy balance"""
    energy = await RedisClient.check_energy(str(current_user.id))
    # Initialize energy if not exists
    if energy == 0:
        await RedisClient.get_instance().set(f"user:energy:{current_user.id}", 100)
        energy = 100
    return {"energy": energy, "user_id": str(current_user.id)}

@api_router.post("/connections/{connection_id}/respond")
async def respond_to_connection(
    connection_id: str,
    action: str,  # "ACCEPT" or "REJECT"
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept or reject a connection request"""
    conn = await db.get(Connection, uuid.UUID(connection_id))
    
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Only the receiver can respond
    if conn.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to respond to this connection")
    
    if conn.status != "PENDING":
        raise HTTPException(status_code=400, detail="Connection already processed")
    
    if action.upper() not in ["ACCEPT", "REJECT"]:
        raise HTTPException(status_code=400, detail="Action must be ACCEPT or REJECT")
    
    conn.status = action.upper() + "ED"  # ACCEPTED or REJECTED
    await db.commit()
    
    return {"status": "success", "connection_id": str(conn.id), "new_status": conn.status}

@api_router.post("/admin/reset-energy")
async def reset_energy(
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Reset energy to 100 (for testing)"""
    target_id = user_id or str(current_user.id)
    await RedisClient.get_instance().set(f"user:energy:{target_id}", 100)
    return {"status": "success", "user_id": target_id, "energy": 100}

@api_router.get("/admin/users")
async def admin_list_all_users(
    db: AsyncSession = Depends(get_db)
):
    """List ALL users without authentication (for testing)"""
    stmt = select(User).where(User.is_active == True)
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "bio": u.bio,
            "location": u.location,
            "role": u.role,
            "skills": u.skills,
            "created_at": u.created_at.isoformat()
        }
        for u in users
    ]