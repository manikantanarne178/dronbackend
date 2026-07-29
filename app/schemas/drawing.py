from pydantic import BaseModel
from datetime import datetime


class DrawingUploadResponse(BaseModel):
    drawing_id: str
    filename: str
    file_type: str
    uploaded_at: datetime
    status: str