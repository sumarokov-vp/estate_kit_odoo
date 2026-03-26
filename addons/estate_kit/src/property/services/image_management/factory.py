from ......src.shared.services.image_service import Factory as ImageServiceFactory
from ..image_sync_service import ImageSyncService
from .image_deleter import ImageDeleter
from .image_uploader import ImageUploader
from .service import ImageManagementService


class Factory:
    @staticmethod
    def create(env) -> ImageManagementService:
        image_service = ImageServiceFactory.create(env)
        image_sync = ImageSyncService(env)
        image_uploader = ImageUploader(image_service)
        image_deleter = ImageDeleter(image_service, image_sync)
        return ImageManagementService(image_uploader, image_deleter)
