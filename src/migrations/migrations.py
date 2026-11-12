from src.database.database import engine
from src.schema.schema import Base
 
 
async def run_migrations():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
 
 