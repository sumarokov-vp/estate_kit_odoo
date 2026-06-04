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

    def rotate(self, key: str, degrees: int) -> dict | None:
        with grpc.insecure_channel(self._address) as channel:
            stub = image_service_pb2_grpc.ImageServiceStub(channel)
            response = stub.RotateImageClockwise(  # type: ignore[attr-defined]
                image_service_pb2.RotateImageClockwiseRequest(key=key, degrees=degrees),
                timeout=GRPC_TIMEOUT,
            )
            return {"key": response.key, "thumbnail_key": response.thumbnail_key}

    def upload_video(self, data: bytes, content_type: str, generate_poster: bool) -> dict | None:
        with grpc.insecure_channel(self._address) as channel:
            stub = image_service_pb2_grpc.ImageServiceStub(channel)
            response = stub.UploadVideo(
                image_service_pb2.UploadVideoRequest(
                    data=data,
                    content_type=content_type,
                    generate_poster=generate_poster,
                ),
                timeout=GRPC_TIMEOUT,
            )
            return {"key": response.key, "poster_key": response.poster_key}

    def download_video(self, key: str) -> tuple[bytes, str] | None:
        with grpc.insecure_channel(self._address) as channel:
            stub = image_service_pb2_grpc.ImageServiceStub(channel)
            response = stub.GetVideo(
                image_service_pb2.GetVideoRequest(key=key),
                timeout=GRPC_TIMEOUT,
            )
            return (response.data, response.content_type)

    def get_video_url(self, key: str, expires_in_seconds: int = 3600) -> str | None:
        with grpc.insecure_channel(self._address) as channel:
            stub = image_service_pb2_grpc.ImageServiceStub(channel)
            response = stub.GetVideoUrl(
                image_service_pb2.GetVideoUrlRequest(
                    key=key,
                    expires_in_seconds=expires_in_seconds,
                ),
                timeout=GRPC_TIMEOUT,
            )
            return response.url

    def delete_video(self, key: str) -> bool:
        with grpc.insecure_channel(self._address) as channel:
            stub = image_service_pb2_grpc.ImageServiceStub(channel)
            response = stub.DeleteVideo(
                image_service_pb2.DeleteVideoRequest(key=key),
                timeout=GRPC_TIMEOUT,
            )
            return response.success
