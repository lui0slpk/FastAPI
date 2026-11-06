from math import ceil
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

DEFAULT_PER_PAGE = 10
MAX_PER_PAGE = 50


def sanitize_pagination(page: int = 1, per_page: int = DEFAULT_PER_PAGE):
    page = max(1, int(page or 1))
    per_page = min(MAX_PER_PAGE, max(1, int(per_page or DEFAULT_PER_PAGE)))

    return page, per_page


def paginate_query(
    db: Session,
    model,
    search: str | None = None,
    base_query=None,
    page: int = 1,
    per_page: int = DEFAULT_PER_PAGE,
    order_by: str | None = None,
    direction: str = "asc",
    allowed_order: dict[str, Any] | None = None
):
    page, per_page = sanitize_pagination(page, per_page)
    query = base_query if base_query is not None else select(model)

    total = db.scalar(select(func.count()).select_from(model)) or 0

    if total == 0:
        return {
            "total": 0,
            "pages": 0,
            "page": page,
            "per_page": per_page,
            "order_by": order_by,
            "direction": direction,
            "items": []
        }

    if allowed_order and order_by:
        col = allowed_order.get(order_by, allowed_order.get("id"))
        query = query.order_by(
            col.desc() if direction == "desc" else col.asc())

    items = db.execute(query.offset(
        (page - 1) * per_page).limit(per_page)).scalars().all()

    total_pages = ceil(total/per_page)

    has_prev = page > 1
    has_next = page < total_pages if total_pages > 0 else False

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "per_page": per_page,
        "has_prev": has_prev,
        "has_next": has_next,
        "order_by": order_by,
        "direction": direction,
        "search": search,
        "items": items
    }
