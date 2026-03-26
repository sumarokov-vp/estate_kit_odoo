from typing import Protocol


class IImageSync(Protocol):
    def delete_images(self, images_to_delete: list[tuple[int, int]]) -> None: ...
