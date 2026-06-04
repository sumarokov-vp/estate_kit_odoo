from typing import Protocol


class IVideoUploader(Protocol):
    def upload(self, vals: dict, video_data: bytes, content_type: str) -> None: ...
