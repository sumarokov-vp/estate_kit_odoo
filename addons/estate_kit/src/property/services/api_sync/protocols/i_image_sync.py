from typing import Any, Protocol


class IImageSync(Protocol):
    def push_images_for_property(self, property_record: Any) -> None: ...
