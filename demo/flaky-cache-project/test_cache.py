from __future__ import annotations

from cache import LRUCache


def test_evicts_least_recently_used_entry() -> None:
    cache = LRUCache(capacity=2)
    cache.put("a", 1)
    cache.put("b", 2)
    # Touch "a" so "b" becomes least-recently-used.
    assert cache.get("a") == 1
    # Inserting "c" should evict "b" (the LRU entry), keeping "a" and "c".
    cache.put("c", 3)

    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert len(cache) == 2


def test_capacity_is_never_exceeded() -> None:
    cache = LRUCache(capacity=3)
    for i in range(10):
        cache.put(f"k{i}", i)
    assert len(cache) == 3
    # The three most-recently inserted keys must survive.
    assert cache.get("k9") == 9
    assert cache.get("k8") == 8
    assert cache.get("k7") == 7
