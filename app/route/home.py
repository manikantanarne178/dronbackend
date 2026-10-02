from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def home():
    return {
        "message": "Welcome to DroneVision"
    }

@router.get("/health")
def health():
    return {
        "status": "HEALTHY",
        "service": "DroneVision API"
    }