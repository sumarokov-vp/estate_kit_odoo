import base64
import logging
import mimetypes

from .protocols import IImageService

_logger = logging.getLogger(__name__)


class ImageUploader:
    def __init__(self, image_service: IImageService) -> None:
        self._image_service = image_service

    def upload(self, vals: dict, image_b64: str) -> None:
        try:
            file_data = base64.b64decode(image_b64)
        except Exception:
            _logger.warning("Failed to decode base64 image data")
            return

        file_name = vals.get("name", "image")
        content_type = mimetypes.guess_type(file_name + ".jpg")[0] or "image/jpeg"

        result = self._image_service.upload(file_data, content_type, generate_thumbnail=True)
        if result:
            vals["image_key"] = result["key"]
            vals["thumbnail_key"] = result["thumbnail_key"]
        else:
            _logger.warning("Image Service upload failed for %s", file_name)
