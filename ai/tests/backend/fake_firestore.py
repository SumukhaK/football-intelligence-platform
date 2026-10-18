"""An in-memory stand-in for the slice of ``firestore.Client`` the store uses."""

from __future__ import annotations

import copy
from typing import Any


class FakeSnapshot:
    """A document read: whether it exists, and a copy of its data."""

    def __init__(self, data: dict[str, Any] | None) -> None:
        self.exists = data is not None
        self._data = copy.deepcopy(data)

    def to_dict(self) -> dict[str, Any] | None:
        return copy.deepcopy(self._data)


class FakeDocument:
    def __init__(self, rows: dict[str, dict[str, Any]], key: str) -> None:
        self._rows = rows
        self._key = key

    def get(self) -> FakeSnapshot:
        return FakeSnapshot(self._rows.get(self._key))

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        previous = self._rows.get(self._key, {}) if merge else {}
        self._rows[self._key] = {**previous, **copy.deepcopy(data)}

    def update(self, data: dict[str, Any]) -> None:
        """Match Firestore's field patch and missing-document behavior."""
        if self._key not in self._rows:
            raise KeyError(self._key)
        self.set(data, merge=True)


class FakeQuery:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def stream(self) -> list[FakeSnapshot]:
        return [FakeSnapshot(row) for row in self._rows]


class FakeCollection:
    def __init__(self, rows: dict[str, dict[str, Any]]) -> None:
        self._rows = rows

    def document(self, key: str) -> FakeDocument:
        return FakeDocument(self._rows, key)

    def where(self, *, filter: Any) -> FakeQuery:  # noqa: A002 — Firestore's name
        assert filter.op_string == "=="
        field, value = filter.field_path, filter.value
        return FakeQuery([r for r in self._rows.values() if r.get(field) == value])


class FakeFirestore:
    """Collections of documents, keyed by collection name then document ID."""

    def __init__(self) -> None:
        self.collections: dict[str, dict[str, dict[str, Any]]] = {}

    def collection(self, name: str) -> FakeCollection:
        return FakeCollection(self.collections.setdefault(name, {}))
