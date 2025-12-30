from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Create the Async Engine
engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    echo=True,  # to see the logging of the sql
    future=True
)

# Create the Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Base Class for all Models
class Base(DeclarativeBase):
    pass

# Dependency for FastAPI Routes (to get a DB session)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()