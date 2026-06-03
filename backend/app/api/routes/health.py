from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def get_health():
    """
    Service health check endpoint.
    """
    return {"status": "healthy", "service": "Plum Adjudicate Backend"}
