from pydantic import Tag
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.tags.schemas import TagPublic
from app.models.tag import TagORM
from app.services.pagination import paginate_query


class TagRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_tags(
        self, search: str | None,
        order_by: str = "id", direction: str = "asc",
        page: int = 1, per_page: int = 10
    ):
        query = select(TagORM)
        if search:
            query = select(TagORM).where(
                func.lower(TagORM.name).ilike(f"%{search.lower()}%"))

        allowed_order = {
            "id": TagORM.id,
            "name": func.lower(TagORM.name)
        }

        result = paginate_query(
            db=self.db,
            model=TagORM,
            search=search,
            base_query=query,
            page=page,
            per_page=per_page,
            order_by=order_by,
            direction=direction,
            allowed_order=allowed_order
        )

        result["items"] = [TagPublic.model_validate(
            item) for item in result["items"]]

        return result

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
