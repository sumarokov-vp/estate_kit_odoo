from typing import Protocol


class IImageDownloader(Protocol):
    def download(self, url: str) -> bytes | None: ...
