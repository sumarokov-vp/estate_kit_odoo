from .protocols import IImageDeleter, IImageUploader


class ImageManagementService:
    def __init__(
        self,
        image_uploader: IImageUploader,
        image_deleter: IImageDeleter,
    ) -> None:
        self._image_uploader = image_uploader
        self._image_deleter = image_deleter

    def upload(self, vals: dict, image_data: bytes) -> None:
        self._image_uploader.upload(vals, image_data)

    def delete_images(self, records) -> None:
        self._image_deleter.delete(records)
