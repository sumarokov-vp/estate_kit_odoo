import logging

import grpc

from .generated import image_service_pb2, image_service_pb2_grpc

_logger = logging.getLogger(__name__)

DEFAULT_ADDRESS = "localhost:50051"
GRPC_TIMEOUT = 30


class ImageServiceClient:
    def __init__(self, env):
        config = env["ir.config_parameter"].sudo()
        self._address = (
            config.get_param("estate_kit.image_service_address") or DEFAULT_ADDRESS
        )

    def upload(self, data: bytes, content_type: str, generate_thumbnail: bool = True):
        """Upload image, return (key, url, thumbnail_key, thumbnail_url) or None."""
        try:
            with grpc.insecure_channel(self._address) as channel:
                stub = image_service_pb2_grpc.ImageServiceStub(channel)
                response = stub.UploadImage(
                    image_service_pb2.UploadImageRequest(
                        data=data,
                        content_type=content_type,
                        generate_thumbnail=generate_thumbnail,
                    ),
                    timeout=GRPC_TIMEOUT,
                )
                return {
                    "key": response.key,
                    "thumbnail_key": response.thumbnail_key,
                }
        except grpc.RpcError:
            _logger.exception("Failed to upload image to Image Service at %s", self._address)
            return None

    def download(self, key: str) -> tuple[bytes, str] | None:
        """Download image by key, return (data, content_type) or None."""
        try:
            with grpc.insecure_channel(self._address) as channel:
                stub = image_service_pb2_grpc.ImageServiceStub(channel)
                response = stub.GetImage(
                    image_service_pb2.GetImageRequest(key=key),
                    timeout=GRPC_TIMEOUT,
                )
                return (response.data, response.content_type)
        except grpc.RpcError:
            _logger.exception("Failed to download image %s from Image Service", key)
            return None

    def delete(self, key: str) -> bool:
        """Delete image by key."""
        try:
            with grpc.insecure_channel(self._address) as channel:
                stub = image_service_pb2_grpc.ImageServiceStub(channel)
                response = stub.DeleteImage(
                    image_service_pb2.DeleteImageRequest(key=key),
                    timeout=GRPC_TIMEOUT,
                )
                return response.success
        except grpc.RpcError:
            _logger.exception("Failed to delete image %s from Image Service", key)
            return False

    def delete_many(self, keys: list[str]) -> list[bool]:
        """Delete multiple images by keys."""
        try:
            with grpc.insecure_channel(self._address) as channel:
                stub = image_service_pb2_grpc.ImageServiceStub(channel)
                response = stub.DeleteImages(
                    image_service_pb2.DeleteImagesRequest(keys=keys),
                    timeout=GRPC_TIMEOUT,
                )
                return list(response.results)
        except grpc.RpcError:
            _logger.exception("Failed to delete images from Image Service")
            return [False] * len(keys)
