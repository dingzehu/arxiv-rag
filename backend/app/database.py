from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

# to build the connection pool
# echo=True logs every SQL query to the console — useful during development
engine = create_async_engine(settings.database_url, echo=True)

# sessionmaker produces a session factory (AsyncSessionLocal)
# class_=AsyncSession overrides the default Session — makes every session async-capable
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    # AsyncSessionLocal is the factory — call it to produce a session 
    async with AsyncSessionLocal() as session:
        yield session