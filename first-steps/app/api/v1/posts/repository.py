
from math import ceil
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.v1.posts.schemas import PaginatedPost
from app.models import AuthorORM, PostORM, TagORM
from app.services.pagination import paginate_query


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, post_id: int) -> PostORM | None:
        return self.db.get(PostORM, post_id)

    def lists_posts(
        self, search: str | None,
        page: int, per_page: int,
        order_by: str, direction: str
    ) -> dict[PostORM, Any]:
        query = select(PostORM)
        if search:
            query = select(PostORM).where(
                func.lower(PostORM.title).ilike(f"%{search.lower()}%")
            )

        allowed_order = {
            "id": PostORM.id,
            "title": PostORM.title
        }

        result = paginate_query(
            db=self.db, model=PostORM,
            search=search, base_query=query,
            page=page, per_page=per_page,
            order_by=order_by, direction=direction,
            allowed_order=allowed_order
        )

        return result

    def by_tags(self, tags: list[str]) -> list[PostORM]:
        normalized_tag_names = [tag.strip().lower()
                                for tag in tags if tag.strip()]

        if not normalized_tag_names:
            return []

        post_list = (
            select(PostORM)
            .options(
                selectinload(PostORM.tags),
                joinedload(PostORM.author),
            )
            .where(PostORM.tags.any(func.lower(TagORM.name).in_(normalized_tag_names)))
            .order_by(PostORM.id.asc())
        )

        return self.db.execute(post_list).scalars().all()

    def ensure_author(self, name: str, email: str) -> AuthorORM:
        author_obj = self.db.execute(
            select(AuthorORM).where(AuthorORM.email == email)
        ).scalar_one_or_none()

        if author_obj:
            return author_obj

        author_obj = AuthorORM(
            name=name,
            email=email
        )
        self.db.add(author_obj)
        self.db.flush()

        return author_obj

    def ensure_tag(self, name: str) -> TagORM:
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

    def create_post(self, title: str, content: str, author: dict | None, tags: list[dict], image_url: str) -> PostORM:
        author_obj = None

        if author:
            author_obj = self.ensure_author(
                name=author["username"], email=author["email"])

        post = PostORM(
            title=title, content=content, image_url=image_url, author=author_obj)

        names = tags[0]["name"].split(",")
        for name in names:

            name = name.strip().lower()
            if not name:
                continue

            tag_obj = self.ensure_tag(name)
            post.tags.append(tag_obj)

        self.db.add(post)
        self.db.flush()
        self.db.refresh(post)

        return post

    def update_post(self, post: PostORM, updates: dict) -> PostORM:
        for key, value in updates.items():
            setattr(post, key, value)

        return post

    def delete_post(self, post: PostORM) -> None:
        self.db.delete(post)

        return
