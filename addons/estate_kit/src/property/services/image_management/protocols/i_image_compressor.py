from typing import Protocol


class IImageCompressor(Protocol):
    def compress(self, data: bytes) -> tuple[bytes, str]:
        """Compress image data. Returns (compressed_bytes, content_type)."""
        ...
