"""An in-memory stand-in for the slice of ``firestore.Client`` the store uses."""

from __future__ import annotations

import copy
import threading
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

    def get(self, transaction: FakeTransaction | None = None) -> FakeSnapshot:
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


class FakeTransaction:
    """Enough of ``firestore.Transaction`` for ``firestore.transactional``.

    Transactions run one at a time, which is what Firestore's conflict retries
    guarantee; writes apply on commit.
    """

    _read_only = False
    _max_attempts = 5

    def __init__(self, lock: threading.Lock) -> None:
        self._lock = lock
        self._id: bytes | None = None
        self._writes: list[tuple[FakeDocument, dict[str, Any], bool]] = []

    def _clean_up(self) -> None:
        self._writes, self._id = [], None

    def _begin(self, retry_id: bytes | None = None) -> None:
        self._lock.acquire()
        self._id = b"fake"

    def _commit(self) -> list[Any]:
        for document, data, merge in self._writes:
            document.set(data, merge=merge)
        self._clean_up()
        self._lock.release()
        return []

    def _rollback(self) -> None:
        self._clean_up()
        if self._lock.locked():
            self._lock.release()

    def set(
        self, document: FakeDocument, data: dict[str, Any], merge: bool = False
    ) -> None:
        self._writes.append((document, data, merge))


class FakeFirestore:
    """Collections of documents, keyed by collection name then document ID."""

    def __init__(self) -> None:
        self.collections: dict[str, dict[str, dict[str, Any]]] = {}
        self._transaction_lock = threading.Lock()

    def transaction(self) -> FakeTransaction:
        return FakeTransaction(self._transaction_lock)

    def collection(self, name: str) -> FakeCollection:
        return FakeCollection(self.collections.setdefault(name, {}))
