def notify(message: str, notification_type: str = "info") -> dict:
    return {
        "type": "ir.actions.client",
        "tag": "display_notification",
        "params": {
            "message": message,
            "type": notification_type,
            "sticky": False,
        },
    }


def reload_settings() -> dict:
    return {
        "type": "ir.actions.client",
        "tag": "reload",
    }
