from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.content import router as content_router
from app.api.dashboard import router as dashboard_router
from app.api.ingest import router as ingest_router
from app.api.schedule import router as schedule_router
from app.api.topics import router as topics_router

router = APIRouter()

router.include_router(
    health_router,
)

router.include_router(
    ingest_router,
)

router.include_router(
    content_router,
)

router.include_router(
    dashboard_router,
)

router.include_router(
    schedule_router,
)

router.include_router(
    topics_router,
)
