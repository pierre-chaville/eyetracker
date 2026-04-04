from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KeyboardLayout
from app.schemas.keyboard_layout import (
    KeyboardLayoutCreate,
    KeyboardLayoutRead,
    KeyboardLayoutUpdate,
)
from app.utils.exceptions import EntityNotFoundError


def layout_to_response(layout: KeyboardLayout) -> KeyboardLayoutRead:
    return KeyboardLayoutRead(
        id=layout.id,
        name=layout.name,
        description=layout.description,
        rows=layout.rows,
        columns=layout.columns,
        predictive_cells=layout.predictive_cells,
        cells=layout.cells,
        sort_order=getattr(layout, "sort_order", 0) or 0,
        created_at=layout.created_at,
        updated_at=layout.updated_at,
    )


class KeyboardLayoutService:
    """Service for keyboard layout operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _next_sort_order(self) -> int:
        result = await self._session.execute(select(func.max(KeyboardLayout.sort_order)))
        max_so = result.scalar()
        return (max_so if max_so is not None else -1) + 1

    async def list_layouts(self, skip: int, limit: int) -> List[KeyboardLayoutRead]:
        statement = (
            select(KeyboardLayout)
            .order_by(KeyboardLayout.sort_order.asc(), KeyboardLayout.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(statement)
        layouts = list(result.scalars().all())
        return [layout_to_response(layout) for layout in layouts]

    async def get_layout(self, layout_id: int) -> KeyboardLayoutRead:
        layout = await self._session.get(KeyboardLayout, layout_id)
        if not layout:
            raise EntityNotFoundError("KeyboardLayout", layout_id)
        return layout_to_response(layout)

    async def create_layout(self, payload: KeyboardLayoutCreate) -> KeyboardLayoutRead:
        sort_order = (
            payload.sort_order
            if payload.sort_order is not None
            else await self._next_sort_order()
        )
        layout = KeyboardLayout(
            name=payload.name,
            description=payload.description,
            rows=payload.rows,
            columns=payload.columns,
            predictive_cells=payload.predictive_cells,
            cells=payload.cells,
            sort_order=sort_order,
        )
        self._session.add(layout)
        await self._session.commit()
        await self._session.refresh(layout)
        return layout_to_response(layout)

    async def update_layout(self, layout_id: int, payload: KeyboardLayoutUpdate) -> KeyboardLayoutRead:
        layout = await self._session.get(KeyboardLayout, layout_id)
        if not layout:
            raise EntityNotFoundError("KeyboardLayout", layout_id)
        if payload.name is not None:
            layout.name = payload.name
        if payload.description is not None:
            layout.description = payload.description
        if payload.rows is not None:
            layout.rows = payload.rows
        if payload.columns is not None:
            layout.columns = payload.columns
        if payload.predictive_cells is not None:
            layout.predictive_cells = payload.predictive_cells
        if payload.cells is not None:
            layout.cells = payload.cells
        if payload.sort_order is not None:
            layout.sort_order = payload.sort_order
        layout.updated_at = datetime.utcnow()
        self._session.add(layout)
        await self._session.commit()
        await self._session.refresh(layout)
        return layout_to_response(layout)

    async def delete_layout(self, layout_id: int) -> None:
        layout = await self._session.get(KeyboardLayout, layout_id)
        if not layout:
            raise EntityNotFoundError("KeyboardLayout", layout_id)
        self._session.delete(layout)
        await self._session.commit()
