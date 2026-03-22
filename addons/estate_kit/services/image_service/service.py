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
