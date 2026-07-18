from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

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


def _fix_file_formats(obj):
    if isinstance(obj, dict):
        # Replace OpenAPI 3.1+ contentMediaType for files with "format: binary"
        if obj.get("contentMediaType") == "application/octet-stream":
            obj.pop("contentMediaType", None)
            obj["type"] = "string"
            obj["format"] = "binary"
        for v in obj.values():
            _fix_file_formats(v)
    elif isinstance(obj, list):
        for item in obj:
            _fix_file_formats(item)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title, version=app.version, description=app.description, routes=app.routes
    )
    components = openapi_schema.get("components", {}).get("schemas", {})
    for schema in components.values():
        _fix_file_formats(schema)
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi