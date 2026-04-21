import logging

from .protocols import IImageCompressor, IImageService

_logger = logging.getLogger(__name__)


class ImageUploader:
    def __init__(self, image_service: IImageService, compressor: IImageCompressor) -> None:
        self._image_service = image_service
        self._compressor = compressor

    def upload(self, vals: dict, image_data: bytes) -> None:
        if not image_data:
            return

        file_name = vals.get("name", "image")
        file_data, content_type = self._compressor.compress(image_data)

        result = self._image_service.upload(file_data, content_type, generate_thumbnail=True)
        if result:
            vals["image_key"] = result["key"]
            vals["thumbnail_key"] = result["thumbnail_key"]
        else:
            _logger.warning("Image Service upload failed for %s", file_name)
