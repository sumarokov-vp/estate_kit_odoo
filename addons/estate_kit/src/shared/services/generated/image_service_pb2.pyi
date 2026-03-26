from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message

DESCRIPTOR: _descriptor.FileDescriptor

class UploadImageRequest(_message.Message):
    data: bytes
    content_type: str
    generate_thumbnail: bool
    def __init__(
        self,
        *,
        data: bytes = ...,
        content_type: str = ...,
        generate_thumbnail: bool = ...,
    ) -> None: ...

class UploadImageResponse(_message.Message):
    key: str
    url: str
    thumbnail_key: str
    thumbnail_url: str
    def __init__(
        self,
        *,
        key: str = ...,
        url: str = ...,
        thumbnail_key: str = ...,
        thumbnail_url: str = ...,
    ) -> None: ...

class GetImageRequest(_message.Message):
    key: str
    def __init__(self, *, key: str = ...) -> None: ...

class GetImageResponse(_message.Message):
    data: bytes
    content_type: str
    def __init__(self, *, data: bytes = ..., content_type: str = ...) -> None: ...

class DeleteImageRequest(_message.Message):
    key: str
    def __init__(self, *, key: str = ...) -> None: ...

class DeleteImageResponse(_message.Message):
    success: bool
    def __init__(self, *, success: bool = ...) -> None: ...

class DeleteImagesRequest(_message.Message):
    keys: list[str]
    def __init__(self, *, keys: list[str] = ...) -> None: ...

class DeleteImagesResponse(_message.Message):
    results: list[bool]
    def __init__(self, *, results: list[bool] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    healthy: bool
    message: str
    def __init__(self, *, healthy: bool = ..., message: str = ...) -> None: ...
