from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():

    return {
        "status": "UP",
        "application": "LinkedIn AI Studio",
        "timestamp": datetime.utcnow(),
    }