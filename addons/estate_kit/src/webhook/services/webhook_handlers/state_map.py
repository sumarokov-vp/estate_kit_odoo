STRING_STATE_MAP: dict[str, str] = {
    "active": "published",
    "rejected": "rejected",
    "suspended": "unpublished",
    "new": "moderation",
    "moderation": "moderation",
    "legal_review": "legal_review",
}
