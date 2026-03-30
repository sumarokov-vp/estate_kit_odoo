from typing import Protocol


class IImageService(Protocol):
    def upload(
        self,
        data: bytes,
        content_type: str,
        generate_thumbnail: bool = True,
    ) -> dict | None: ...

    def delete_many(self, keys: list[str]) -> list[bool]: ...
