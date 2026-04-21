from ..krisha_scraping.protocols import IImageDownloader


class PhotoImporter:
    def __init__(self, env, image_downloader: IImageDownloader) -> None:
        self._env = env
        self._image_downloader = image_downloader

    def import_photos(self, property_id: int, photo_urls: list[str]) -> int:
        imported = 0
        for index, photo_url in enumerate(photo_urls):
            if not photo_url:
                continue
            image_data = self._image_downloader.download(photo_url)
            if not image_data:
                continue
            self._env["estate.property.image"].create({
                "property_id": property_id,
                "name": f"Фото {index + 1}",
                "image_data": image_data,
                "sequence": index * 10,
                "is_main": index == 0,
            })
            imported += 1
        return imported
