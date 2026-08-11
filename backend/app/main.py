import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.api.routes import router
from app.core import database

logger = logging.getLogger(__name__)

_cleanup_task = None

async def periodic_cleanup():
    """Background task running every 2 minutes to delete blogs older than 15 minutes."""
    while True:
        try:
            await asyncio.sleep(120)  # check every 2 minutes
            database.delete_old_blogs(max_age_minutes=15)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in periodic_cleanup task: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    database.init_db()
    global _cleanup_task
    _cleanup_task = asyncio.create_task(periodic_cleanup())
    yield
    # Shutdown
    if _cleanup_task:
        _cleanup_task.cancel()

app = FastAPI(
    title="Blog Writing Agent API",
    description="LangGraph-powered technical blog generator",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — configurable via FRONTEND_URL env var for production
frontend_url = os.getenv("FRONTEND_URL", "")
allowed_origins = ["http://localhost:3000", "http://localhost:5173"]
if frontend_url:
    allowed_origins.append(frontend_url)
else:
    allowed_origins.append("*")  # fallback for local dev

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve generated images
images_dir = Path("images")
images_dir.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.get("/")
def root():
    return {"message": "Blog Writing Agent API is running"}

