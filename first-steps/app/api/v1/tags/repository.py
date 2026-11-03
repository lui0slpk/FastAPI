from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.tag import TagORM


class TagRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_tag(self, name: str) -> TagORM:
        name = name.strip().lower()

        # for PostgreSQL
        # tag_obj = self.db.execute(
        #     select(TagORM).where(TagORM.name.ilike(name))
        # ).scalar_one_or_none()

        # for SQLite3
        tag_obj = self.db.execute(
            select(TagORM).where(func.lower(TagORM.name) == name)
        ).scalar_one_or_none()

        if tag_obj:
            return tag_obj

        tag_obj = TagORM(name=name)
        self.db.add(tag_obj)
        self.db.flush()

        return tag_obj


# class TagRepository(Base):
#     id: Mapped[Integer] = mapped_column(
#         Integer, nullable=False, primary_key=True)
