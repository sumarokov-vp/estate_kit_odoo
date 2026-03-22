from .config import DEFAULT_ADDRESS
from .grpc_gateway import GrpcImageServiceGateway
from .service import ImageService


class Factory:
    @staticmethod
    def create(env) -> ImageService:
        config = env["ir.config_parameter"].sudo()
        address = config.get_param("estate_kit.image_service_address") or DEFAULT_ADDRESS
        return ImageService(GrpcImageServiceGateway(address))
