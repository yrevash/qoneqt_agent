import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Boolean, Float, DateTime, ARRAY, ForeignKey, Text, Index
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
    
    # OPEN SOURCE SOTA: all-mpnet-base-v2 (768 dimensions)
    interest_vector: Mapped[Optional[List[float]]] = mapped_column(Vector(768), nullable=True)
    
    # Scheduler
    activity_schedule: Mapped[Optional[List[float]]] = mapped_column(ARRAY(Float), nullable=True)
    
    # Meta
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    traces: Mapped[List["AgentTrace"]] = relationship(back_populates="agent")

    # Update Index for 768 dimensions
    __table_args__ = (
        Index(
            'idx_users_interest_vector_hnsw', 
            'interest_vector', 
            postgresql_using='hnsw', 
            postgresql_with={'m': 16, 'ef_construction': 64}, 
            postgresql_ops={'interest_vector': 'vector_cosine_ops'}
        ),
    )


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    interaction_type: Mapped[str] = mapped_column(String)
    reasoning_log: Mapped[dict] = mapped_column(JSONB)
    decision: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    agent: Mapped["User"] = relationship(back_populates="traces")