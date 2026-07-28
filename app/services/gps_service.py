from pathlib import Path

from app.core.config import settings
from app.utils.gps_extractor import extract_gps


def get_all_gps():
    images = []

    for image in settings.UPLOAD_DIR.iterdir():

        if image.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        gps = extract_gps(image)

        if gps:
            images.append(
                {
                    "image": image.name,
                    **gps
                }
            )

    return images