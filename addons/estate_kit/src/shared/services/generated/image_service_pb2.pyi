from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class UploadImageRequest(_message.Message):
    __slots__ = ("data", "content_type", "generate_thumbnail")
    DATA_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    GENERATE_THUMBNAIL_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    content_type: str
    generate_thumbnail: bool
    def __init__(self, data: _Optional[bytes] = ..., content_type: _Optional[str] = ..., generate_thumbnail: bool = ...) -> None: ...

class UploadImageResponse(_message.Message):
    __slots__ = ("key", "url", "thumbnail_key", "thumbnail_url")
    KEY_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    THUMBNAIL_KEY_FIELD_NUMBER: _ClassVar[int]
    THUMBNAIL_URL_FIELD_NUMBER: _ClassVar[int]
    key: str
    url: str
    thumbnail_key: str
    thumbnail_url: str
    def __init__(self, key: _Optional[str] = ..., url: _Optional[str] = ..., thumbnail_key: _Optional[str] = ..., thumbnail_url: _Optional[str] = ...) -> None: ...

class UploadImagesRequest(_message.Message):
    __slots__ = ("images",)
    IMAGES_FIELD_NUMBER: _ClassVar[int]
    images: _containers.RepeatedCompositeFieldContainer[UploadImageRequest]
    def __init__(self, images: _Optional[_Iterable[_Union[UploadImageRequest, _Mapping]]] = ...) -> None: ...

class UploadImagesResponse(_message.Message):
    __slots__ = ("results",)
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[UploadImageResponse]
    def __init__(self, results: _Optional[_Iterable[_Union[UploadImageResponse, _Mapping]]] = ...) -> None: ...

class GetImageRequest(_message.Message):
    __slots__ = ("key",)
    KEY_FIELD_NUMBER: _ClassVar[int]
    key: str
    def __init__(self, key: _Optional[str] = ...) -> None: ...

class GetImageResponse(_message.Message):
    __slots__ = ("data", "content_type")
    DATA_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    content_type: str
    def __init__(self, data: _Optional[bytes] = ..., content_type: _Optional[str] = ...) -> None: ...

class GetImagesRequest(_message.Message):
    __slots__ = ("keys",)
    KEYS_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, keys: _Optional[_Iterable[str]] = ...) -> None: ...

class GetImagesResponse(_message.Message):
    __slots__ = ("results",)
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[GetImageResponse]
    def __init__(self, results: _Optional[_Iterable[_Union[GetImageResponse, _Mapping]]] = ...) -> None: ...

class GetImageUrlRequest(_message.Message):
    __slots__ = ("key", "expires_in_seconds")
    KEY_FIELD_NUMBER: _ClassVar[int]
    EXPIRES_IN_SECONDS_FIELD_NUMBER: _ClassVar[int]
    key: str
    expires_in_seconds: int
    def __init__(self, key: _Optional[str] = ..., expires_in_seconds: _Optional[int] = ...) -> None: ...

class GetImageUrlResponse(_message.Message):
    __slots__ = ("url",)
    URL_FIELD_NUMBER: _ClassVar[int]
    url: str
    def __init__(self, url: _Optional[str] = ...) -> None: ...

class DeleteImageRequest(_message.Message):
    __slots__ = ("key",)
    KEY_FIELD_NUMBER: _ClassVar[int]
    key: str
    def __init__(self, key: _Optional[str] = ...) -> None: ...

class DeleteImageResponse(_message.Message):
    __slots__ = ("success",)
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class DeleteImagesRequest(_message.Message):
    __slots__ = ("keys",)
    KEYS_FIELD_NUMBER: _ClassVar[int]
    keys: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, keys: _Optional[_Iterable[str]] = ...) -> None: ...

class DeleteImagesResponse(_message.Message):
    __slots__ = ("results",)
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedScalarFieldContainer[bool]
    def __init__(self, results: _Optional[_Iterable[bool]] = ...) -> None: ...

class RotateImageClockwiseRequest(_message.Message):
    __slots__ = ("key", "degrees")
    KEY_FIELD_NUMBER: _ClassVar[int]
    DEGREES_FIELD_NUMBER: _ClassVar[int]
    key: str
    degrees: int
    def __init__(self, key: _Optional[str] = ..., degrees: _Optional[int] = ...) -> None: ...

class RotateImageClockwiseResponse(_message.Message):
    __slots__ = ("key", "url")
    KEY_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    key: str
    url: str
    def __init__(self, key: _Optional[str] = ..., url: _Optional[str] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("healthy", "message")
    HEALTHY_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    healthy: bool
    message: str
    def __init__(self, healthy: bool = ..., message: _Optional[str] = ...) -> None: ...
