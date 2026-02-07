from __future__ import annotations

from datetime import datetime
from typing import List

from sqlmodel import Session, select

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
        created_at=layout.created_at,
        updated_at=layout.updated_at,
    )


class KeyboardLayoutService:
    """Service for keyboard layout operations."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_layouts(self, skip: int, limit: int) -> List[KeyboardLayoutRead]:
        statement = select(KeyboardLayout).offset(skip).limit(limit)
        layouts = self._session.exec(statement).all()
        return [layout_to_response(layout) for layout in layouts]

    def get_layout(self, layout_id: int) -> KeyboardLayoutRead:
        layout = self._session.get(KeyboardLayout, layout_id)
        if not layout:
            raise EntityNotFoundError("KeyboardLayout", layout_id)
        return layout_to_response(layout)

    def create_layout(self, payload: KeyboardLayoutCreate) -> KeyboardLayoutRead:
        layout = KeyboardLayout(
            name=payload.name,
            description=payload.description,
            rows=payload.rows,
            columns=payload.columns,
            predictive_cells=payload.predictive_cells,
            cells=payload.cells,
        )
        self._session.add(layout)
        self._session.commit()
        self._session.refresh(layout)
        return layout_to_response(layout)

    def update_layout(self, layout_id: int, payload: KeyboardLayoutUpdate) -> KeyboardLayoutRead:
        layout = self._session.get(KeyboardLayout, layout_id)
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
        layout.updated_at = datetime.utcnow()
        self._session.add(layout)
        self._session.commit()
        self._session.refresh(layout)
        return layout_to_response(layout)

    def delete_layout(self, layout_id: int) -> None:
        layout = self._session.get(KeyboardLayout, layout_id)
        if not layout:
            raise EntityNotFoundError("KeyboardLayout", layout_id)
        self._session.delete(layout)
        self._session.commit()
