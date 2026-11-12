import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
 
load_dotenv()
 
from urllib.parse import quote_plus

db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD", "postgres")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "coder_agent")

encoded_password = quote_plus(db_password) if db_password else ""

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
)
# ASYNC ENGINE
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)
 

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
 
# BASE MODEL
Base = declarative_base()
 
 
# Dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
 
 