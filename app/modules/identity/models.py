import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, Float, DateTime, ARRAY, ForeignKey, Text, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    # Identity
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Profile & Brain
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata for Hybrid Search
    location: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True) 
    skills: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Vector Embedding (768 dimensions)
    interest_vector: Mapped[Optional[List[float]]] = mapped_column(Vector(768), nullable=True)
    
    # Scheduler
    activity_schedule: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)    
    
    # Meta
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    traces: Mapped[List["AgentTrace"]] = relationship(back_populates="agent", foreign_keys="AgentTrace.agent_id")
    
    # Connections (As Initiator)
    sent_connections: Mapped[List["Connection"]] = relationship(
        back_populates="initiator", 
        foreign_keys="Connection.initiator_id"
    )
    # Connections (As Receiver)
    received_connections: Mapped[List["Connection"]] = relationship(
        back_populates="receiver", 
        foreign_keys="Connection.receiver_id"
    )

    # HNSW Index for Vector Search
    __table_args__ = (
        Index(
            'idx_users_interest_vector_hnsw', 
            'interest_vector', 
            postgresql_using='hnsw', 
            postgresql_with={'m': 16, 'ef_construction': 64}, 
            postgresql_ops={'interest_vector': 'vector_cosine_ops'}
        ),
    )


class Connection(Base):
    """
    Tracks the relationship state between two users.
    Prevents spamming invitations.
    """
    __tablename__ = "connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    initiator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # STATUS: PENDING, ACCEPTED, REJECTED, BLOCKED
    status: Mapped[str] = mapped_column(String, default="PENDING", index=True)
    
    # Which search triggered this connection?
    request_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    

    # Relationships
    initiator: Mapped["User"] = relationship(back_populates="sent_connections", foreign_keys=[initiator_id])
    receiver: Mapped["User"] = relationship(back_populates="received_connections", foreign_keys=[receiver_id])

    # Ensure unique link direction
    __table_args__ = (
        UniqueConstraint('initiator_id', 'receiver_id', name='uq_connection_link'),
    )


class AgentTrace(Base):
    """
    The 'Thought Log'. Now scoped by Chat ID (request_id).
    """
    __tablename__ = "agent_traces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who is thinking?
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    
    # Who are they thinking about? (NEW)
    target_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)
    
    # The "Chat ID" / "Session ID" (NEW)
    # Used to prevent re-screening the same person in the same session.
    request_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    
    interaction_type: Mapped[str] = mapped_column(String) # SCREENING, NEGOTIATION
    reasoning_log: Mapped[dict] = mapped_column(JSONB)
    decision: Mapped[str] = mapped_column(String) # ACCEPT, REJECT
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    agent: Mapped["User"] = relationship(back_populates="traces", foreign_keys=[agent_id])