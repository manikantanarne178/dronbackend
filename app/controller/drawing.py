from fastapi import UploadFile

from app.services.drawing_service import DrawingService


class DrawingController:

    @staticmethod
    async def upload(file, db):
        return DrawingService.save_drawing(file, db)