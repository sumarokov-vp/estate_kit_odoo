_MAIN_IMAGE_BIAS = -1000


class MainImageResolver:
    def resolve(self, prop):
        images = prop.image_ids.filtered(
            lambda i: i.image_key or i.thumbnail_key
        )
        if not images:
            return images
        return images.sorted(
            key=lambda i: (_MAIN_IMAGE_BIAS if i.is_main else 0, i.sequence, i.id)
        )[0]
