import logging

from .protocols import IImageService

_logger = logging.getLogger(__name__)


class VideoUploader:
    def __init__(self, image_service: IImageService) -> None:
        self._image_service = image_service

    def upload(self, vals: dict, video_data: bytes, content_type: str) -> None:
        if not video_data:
            return

        file_name = vals.get("name", "video")

        result = self._image_service.upload_video(video_data, content_type, generate_poster=True)
        if result:
            vals["video_key"] = result["key"]
            vals["poster_key"] = result["poster_key"]
            vals["media_type"] = "video"
        else:
            _logger.warning("Image Service video upload failed for %s", file_name)
