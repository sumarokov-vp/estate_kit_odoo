from ..image_sync_service import ImageSyncService
from ..property_sync_service import PropertySyncService
from .service import ApiSyncService


class Factory:
    @staticmethod
    def create(env) -> ApiSyncService:
        return ApiSyncService(
            PropertySyncService(env),
            ImageSyncService(env),
        )
