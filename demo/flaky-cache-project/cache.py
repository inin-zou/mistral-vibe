"""A tiny LRU-ish cache used for the Pawgress live demo.

It has exactly one bug (see README.md) so a coding agent can fix it live while
Pawgress re-runs the verification command until the test passes 5/5.
"""

from __future__ import annotations

from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self._store: OrderedDict[str, int] = OrderedDict()

    def get(self, key: str) -> int | None:
        if key not in self._store:
            return None
        # Mark the key as most-recently-used.
        self._store.move_to_end(key)
        return self._store[key]

    def put(self, key: str, value: int) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self.capacity:
            # BUG: evicts the most-recently-used entry (last=True) instead of the
            # least-recently-used one. The one-line fix is `last=False`.
            self._store.popitem(last=True)

    def __len__(self) -> int:
        return len(self._store)
