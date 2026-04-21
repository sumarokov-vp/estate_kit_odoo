from typing import Protocol


class IPhotoImporter(Protocol):
    def import_photos(self, property_id: int, photo_urls: list[str]) -> int: ...
