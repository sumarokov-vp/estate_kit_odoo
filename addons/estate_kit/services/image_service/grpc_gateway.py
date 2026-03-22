import grpc

from ..generated import image_service_pb2, image_service_pb2_grpc
from .config import GRPC_TIMEOUT


class GrpcImageServiceGateway:
    def __init__(self, address: str):
        self._address = address

    def upload(self, data: bytes, content_type: str, generate_thumbnail: bool) -> dict | None:
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
            return {"key": response.key, "thumbnail_key": response.thumbnail_key}

    def download(self, key: str) -> tuple[bytes, str] | None:
        with grpc.insecure_channel(self._address) as channel:
            stub = image_service_pb2_grpc.ImageServiceStub(channel)
            response = stub.GetImage(
                image_service_pb2.GetImageRequest(key=key),
                timeout=GRPC_TIMEOUT,
            )
            return (response.data, response.content_type)

    def delete(self, key: str) -> bool:
        with grpc.insecure_channel(self._address) as channel:
            stub = image_service_pb2_grpc.ImageServiceStub(channel)
            response = stub.DeleteImage(
                image_service_pb2.DeleteImageRequest(key=key),
                timeout=GRPC_TIMEOUT,
            )
            return response.success

    def delete_many(self, keys: list[str]) -> list[bool]:
        with grpc.insecure_channel(self._address) as channel:
            stub = image_service_pb2_grpc.ImageServiceStub(channel)
            response = stub.DeleteImages(
                image_service_pb2.DeleteImagesRequest(keys=keys),
                timeout=GRPC_TIMEOUT,
            )
            return list(response.results)
