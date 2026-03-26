from .protocols import IImageService, IImageSync


class ImageDeleter:
    def __init__(self, image_service: IImageService, image_sync: IImageSync) -> None:
        self._image_service = image_service
        self._image_sync = image_sync

    def delete(self, records) -> None:
        keys_to_delete = []
        api_images_to_delete = []
        for rec in records:
            if rec.image_key:
                keys_to_delete.append(rec.image_key)
            if rec.thumbnail_key:
                keys_to_delete.append(rec.thumbnail_key)
            if rec.external_id:
                api_images_to_delete.append(
                    (rec.external_id, rec.property_id.external_id)
                )
        if keys_to_delete:
            self._image_service.delete_many(keys_to_delete)
        if api_images_to_delete:
            self._image_sync.delete_images(api_images_to_delete)
