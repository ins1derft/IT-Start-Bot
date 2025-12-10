from __future__ import annotations

from itstart_domain import TagCategory

from .repositories import TagRepository

SEED_TAGS = {
    # keep lowercase to match user input normalization
    TagCategory.format: ["remote", "office", "hybrid"],
    TagCategory.occupation: ["тестировщик", "разработчик", "дизайнер", "аналитик", "devops"],
    TagCategory.platform: ["android", "ios", "windows"],
    TagCategory.language: ["python", "kotlin", "swift", "js", "csharp"],
    TagCategory.location: ["moscow", "spb", "remote"],
    TagCategory.technology: ["react", "sentry", "postgresql"],
    TagCategory.duration: ["part-time", "full-time"],
}


async def seed_tags(tag_repo: TagRepository) -> None:
    existing = await tag_repo.get_all()
    existing_map = {(t.name, t.category) for t in existing}
    for category, names in SEED_TAGS.items():
        for name in names:
            if (name, category) not in existing_map:
                tag_repo.create(name=name, category=category)
