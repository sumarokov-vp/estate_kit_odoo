from .protocols import IImageSync, IPropertySync


class ApiSyncService:
    def __init__(self, property_sync: IPropertySync, image_sync: IImageSync) -> None:
        self._property_sync = property_sync
        self._image_sync = image_sync

    def push_property(self, record) -> None:
        record.ensure_one()
        self._property_sync.push_property(record)
        self._image_sync.push_images_for_property(record)

    def push_owner(self, record):
        record.ensure_one()
        return self._property_sync.push_owner(record)
