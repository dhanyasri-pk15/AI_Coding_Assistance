import sys
import asyncio
import selectors
import warnings
import logging

# Suppress google_genai AFC warning loggers and flags
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("google_genai.models").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=".*Direct use of automatic function calling.*")

try:
    from google.genai.models import Models, AsyncModels
    Models._logged_afc_warning = True
    AsyncModels._logged_afc_warning = True
except Exception:
    pass

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        import uvicorn.config
        uvicorn.config.Config.get_loop_factory = lambda self: (
            lambda: asyncio.SelectorEventLoop(selectors.SelectSelector())
        )
    except Exception:
        pass

from fastapi import FastAPI
 
from src.router.router import router
from src.migrations.migrations import run_migrations
from src.seeders.seeder import seed_customers
from src.service.service import GraphService
from src.database.database import DATABASE_URL

#1.2 - 1.3 fastapi instance,GraphService instance
app = FastAPI(
    title="Multi Agent AI System",
    version="1.0",
)
#print(DATABASE_URL)
graph_service = GraphService()
 
#1.21 - 1.147 Perform startup function(create tables using migration,seed values for customer tables,compile the graph)
@app.on_event("startup")
async def startup_event():
 
    # Run DB migrations
    await run_migrations()
 
    # Insert sample customers
    await seed_customers()
 
    # Compile LangGraph
    await graph_service.compile()
 
#1.148 register router
app.include_router(router)
 
 