from typing import Protocol


class IImageUploader(Protocol):
    def upload(self, vals: dict, image_data: bytes) -> None: ...
