from fastapi import APIRouter

from app.services.gps_service import get_all_gps

router = APIRouter(
    prefix="/gps",
    tags=["GPS"],
)


@router.get("/")
def gps_locations():
    return {
        "count": len(get_all_gps()),
        "locations": get_all_gps()
    }