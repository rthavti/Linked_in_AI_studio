from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.database import Base, engine
import app.db.models  # Registers all SQLAlchemy models
from app.logger import logger
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    logger.info("Starting scheduler...")
    start_scheduler()

    logger.info("Application started.")

    yield

    stop_scheduler()
    logger.info("Application stopped.")


app = FastAPI(lifespan=lifespan)
app.include_router(router)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(static_dir / "index.html")
