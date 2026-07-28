from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def _to_float(value):
    """
    Converts EXIF rational values to float.
    Works with both IFDRational and normal numeric types.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        try:
            return float(value.numerator) / float(value.denominator)
        except Exception:
            return 0.0


def convert_to_degrees(value):
    """
    Converts GPS coordinates stored as
    Degrees, Minutes, Seconds -> Decimal Degrees
    """
    d = _to_float(value[0])
    m = _to_float(value[1])
    s = _to_float(value[2])

    return d + (m / 60.0) + (s / 3600.0)


def extract_gps(image_path):
    try:
        image = Image.open(image_path)
        exif = image.getexif()

        if not exif:
            return None

        # --------------------------------------------------
        # General EXIF
        # --------------------------------------------------
        exif_data = {}

        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            exif_data[tag] = value

        camera = exif_data.get("Model")
        captured = (
            exif_data.get("DateTimeOriginal")
            or exif_data.get("DateTime")
        )

        # Clean camera model
        if isinstance(camera, bytes):
            camera = camera.decode("utf-8", errors="ignore")

        if camera:
            camera = "".join(
                ch for ch in str(camera) if ch.isprintable()
            ).strip()

        # --------------------------------------------------
        # GPS
        # --------------------------------------------------
        gps_ifd = exif.get_ifd(34853)

        if not gps_ifd:
            return None

        gps = {}

        for key, value in gps_ifd.items():
            gps[GPSTAGS.get(key, key)] = value

        required = [
            "GPSLatitude",
            "GPSLongitude",
            "GPSLatitudeRef",
            "GPSLongitudeRef",
        ]

        if not all(k in gps for k in required):
            return None

        lat = convert_to_degrees(gps["GPSLatitude"])
        lon = convert_to_degrees(gps["GPSLongitude"])

        if gps["GPSLatitudeRef"] == "S":
            lat = -lat

        if gps["GPSLongitudeRef"] == "W":
            lon = -lon

        altitude = None

        if "GPSAltitude" in gps:
            altitude = _to_float(gps["GPSAltitude"])

            if (
                "GPSAltitudeRef" in gps
                and gps["GPSAltitudeRef"] == 1
            ):
                altitude = -altitude

        return {
            "latitude": round(lat, 8),
            "longitude": round(lon, 8),
            "altitude": round(altitude, 2) if altitude is not None else None,
            "captured": captured,
            "camera": camera,
            # DJI XMP values are not available through Pillow.
            # They can be populated later using ExifTool if needed.
            "yaw": None,
            "pitch": None,
            "roll": None,
        }

    except Exception as e:
        print(f"GPS Extraction Error ({image_path}): {e}")
        return None