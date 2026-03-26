from typing import Any, Protocol


class IImageService(Protocol):
    def upload(
        self,
        file_data: bytes,
        content_type: str,
        generate_thumbnail: bool = False,
    ) -> dict[str, Any] | None: ...

    def delete_many(self, keys: list[str]) -> None: ...
