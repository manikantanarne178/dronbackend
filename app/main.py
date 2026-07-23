from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.database import create_tables

from app.route.home import router as home_router
from app.route.upload import router as upload_router
from app.route import reconstruction
from app.route.analytics import router as analytics_router

from app.controller.auth import router as auth_router
from app.controller.projects import router as projects_router
from app.controller.report import router as report_router

app = FastAPI(
    title="DroneVision API",
    version="1.0.0",
    description="Backend API for DroneVision 3D Mapping Platform",
)

# Create database tables
create_tables()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================
# Routers
# ============================

app.include_router(home_router)
app.include_router(upload_router)
app.include_router(reconstruction.router)
app.include_router(analytics_router)
app.include_router(report_router)
app.include_router(projects_router)
app.include_router(auth_router)


# ============================
# Swagger File Upload Fix
# ============================

def _fix_file_formats(obj):
    if isinstance(obj, dict):
        if obj.get("contentMediaType") == "application/octet-stream":
            obj.pop("contentMediaType", None)
            obj["type"] = "string"
            obj["format"] = "binary"

        for value in obj.values():
            _fix_file_formats(value)

    elif isinstance(obj, list):
        for item in obj:
            _fix_file_formats(item)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    components = openapi_schema.get("components", {}).get("schemas", {})

    for schema in components.values():
        _fix_file_formats(schema)

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi