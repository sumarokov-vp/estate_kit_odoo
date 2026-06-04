import logging

import grpc

from .protocols import IImageServiceGateway

_logger = logging.getLogger(__name__)


class ImageService:
    def __init__(self, gateway: IImageServiceGateway):
        self._gateway = gateway

    def upload(self, data: bytes, content_type: str, generate_thumbnail: bool = True) -> dict | None:
        try:
            return self._gateway.upload(data, content_type, generate_thumbnail)
        except grpc.RpcError:
            _logger.exception("Failed to upload image to Image Service")
            return None

    def download(self, key: str) -> tuple[bytes, str] | None:
        try:
            return self._gateway.download(key)
        except grpc.RpcError:
            _logger.exception("Failed to download image %s from Image Service", key)
            return None

    def delete(self, key: str) -> bool:
        try:
            return self._gateway.delete(key)
        except grpc.RpcError:
            _logger.exception("Failed to delete image %s from Image Service", key)
            return False

    def delete_many(self, keys: list[str]) -> list[bool]:
        try:
            return self._gateway.delete_many(keys)
        except grpc.RpcError:
            _logger.exception("Failed to delete images from Image Service")
            return [False] * len(keys)

    def rotate(self, key: str, degrees: int) -> dict | None:
        try:
            return self._gateway.rotate(key, degrees)
        except grpc.RpcError:
            _logger.exception("Failed to rotate image %s in Image Service", key)
            return None

    def upload_video(self, data: bytes, content_type: str, generate_poster: bool = True) -> dict | None:
        try:
            return self._gateway.upload_video(data, content_type, generate_poster)
        except grpc.RpcError:
            _logger.exception("Failed to upload video to Image Service")
            return None

    def download_video(self, key: str) -> tuple[bytes, str] | None:
        try:
            return self._gateway.download_video(key)
        except grpc.RpcError:
            _logger.exception("Failed to download video %s from Image Service", key)
            return None

    def get_video_url(self, key: str, expires_in_seconds: int = 3600) -> str | None:
        try:
            return self._gateway.get_video_url(key, expires_in_seconds)
        except grpc.RpcError:
            _logger.exception("Failed to get video url %s from Image Service", key)
            return None

    def delete_video(self, key: str) -> bool:
        try:
            return self._gateway.delete_video(key)
        except grpc.RpcError:
            _logger.exception("Failed to delete video %s from Image Service", key)
            return False
