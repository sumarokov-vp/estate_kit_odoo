import io
import logging

from PIL import Image

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass

_logger = logging.getLogger(__name__)

MAX_DIMENSION = 2000
JPEG_QUALITY = 80


class ImageCompressor:
    def compress(self, data: bytes) -> tuple[bytes, str]:
        image = Image.open(io.BytesIO(data))

        if image.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode != "P" else None)
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")

        width, height = image.size
        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            if width >= height:
                new_width = MAX_DIMENSION
                new_height = int(height * MAX_DIMENSION / width)
            else:
                new_height = MAX_DIMENSION
                new_width = int(width * MAX_DIMENSION / height)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            _logger.info("Resized image from %dx%d to %dx%d", width, height, new_width, new_height)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)

        return buffer.getvalue(), "image/jpeg"
