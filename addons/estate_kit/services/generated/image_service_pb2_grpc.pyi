from typing import Any

import grpc

from . import image_service_pb2

class ImageServiceStub:
    def __init__(self, channel: grpc.Channel) -> None: ...
    def UploadImage(
        self,
        request: image_service_pb2.UploadImageRequest,
        timeout: float | None = ...,
        metadata: Any = ...,
    ) -> image_service_pb2.UploadImageResponse: ...
    def GetImage(
        self,
        request: image_service_pb2.GetImageRequest,
        timeout: float | None = ...,
        metadata: Any = ...,
    ) -> image_service_pb2.GetImageResponse: ...
    def DeleteImage(
        self,
        request: image_service_pb2.DeleteImageRequest,
        timeout: float | None = ...,
        metadata: Any = ...,
    ) -> image_service_pb2.DeleteImageResponse: ...
    def DeleteImages(
        self,
        request: image_service_pb2.DeleteImagesRequest,
        timeout: float | None = ...,
        metadata: Any = ...,
    ) -> image_service_pb2.DeleteImagesResponse: ...
    def HealthCheck(
        self,
        request: image_service_pb2.HealthCheckRequest,
        timeout: float | None = ...,
        metadata: Any = ...,
    ) -> image_service_pb2.HealthCheckResponse: ...
