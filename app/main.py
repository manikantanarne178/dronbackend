import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.database import create_tables, SessionLocal
from app.core.seed_rules import seed_rules
from app.route.drawing import router as drawing_router
from app.route.home import router as home_router
from app.route.upload import router as upload_router
from app.route import reconstruction
from app.route.analytics import router as analytics_router

from app.controller.auth import router as auth_router
from app.controller.projects import router as projects_router
from app.controller.report import router as report_router
from app.route.gps import router as gps_router
from app.route import report

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan handler:
    Initializes database tables and seeds default rule configurations
    safely on application startup without blocking module imports.
    """
    try:
        logger.info("Initializing database schema...")
        create_tables()
        db = SessionLocal()
        try:
            seed_rules(db)
            logger.info("Default rule configurations verified/seeded.")
        finally:
            db.close()
        logger.info("Database startup initialization completed successfully.")
    except Exception as e:
        logger.error(f"Startup database initialization warning: {e}")
    yield


app = FastAPI(
    title="DroneVision API",
    version="1.0.0",
    description="Backend API for DroneVision 3D Mapping Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dronevision-eta.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app|http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================
# Routers
# ============================
app.include_router(drawing_router)
# AutoDCR Engine routes
from app.route.autodcr.router import router as autodcr_router

app.include_router(autodcr_router)
app.include_router(home_router)
app.include_router(upload_router)
app.include_router(reconstruction.router)
app.include_router(analytics_router)
app.include_router(report_router)
app.include_router(projects_router)
app.include_router(auth_router)
app.include_router(gps_router)
app.include_router(report.router)

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
