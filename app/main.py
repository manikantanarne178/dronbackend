from fastapi import FastAPI

from app.route.home import router as home_router
from app.route.upload import router as upload_router
from app.route import reconstruction
app = FastAPI(
    title="DroneVision API",
    version="1.0.0",
    description="Backend API for DroneVision 3D Mapping Platform",
)

app.include_router(home_router)
app.include_router(upload_router)
app.include_router(reconstruction.router)