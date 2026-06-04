from .protocols import IImageDeleter, IImageUploader, IVideoUploader


class ImageManagementService:
    def __init__(
        self,
        image_uploader: IImageUploader,
        image_deleter: IImageDeleter,
        video_uploader: IVideoUploader,
    ) -> None:
        self._image_uploader = image_uploader
        self._image_deleter = image_deleter
        self._video_uploader = video_uploader

    def upload(self, vals: dict, image_data: bytes) -> None:
        self._image_uploader.upload(vals, image_data)

    def upload_video(self, vals: dict, video_data: bytes, content_type: str) -> None:
        self._video_uploader.upload(vals, video_data, content_type)

    def delete_images(self, records) -> None:
        self._image_deleter.delete(records)
